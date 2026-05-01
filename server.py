#!/usr/bin/env python3
"""Сервер larktex через stdin/stdout с детальным логированием."""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from lib.debug import DebugLogger, get_logger, set_logger, verbose_flag_supported
from lib.exceptions import LarkTeXError, NormalizationError, ParseError, GeneratorError
from lib.normalizer import Normalizer
from lib.parser import Parser
from lib.generator import Generator

# Настраиваем логгер
verbose = verbose_flag_supported()
logger = DebugLogger(verbose=verbose)
set_logger(logger)

# Создаём экземпляры
normalizer = Normalizer(i18n_dir=str(ROOT_DIR / "i18n"))
parser = Parser()
generator = Generator()


def process_with_debug(input_text: str) -> dict:
    """
    Обрабатывает запрос с детальным логированием каждого шага.
    Возвращает результат с полной информацией о процессе.
    """
    logger.info(f"Processing: {input_text!r}")

    result = {
        'input': input_text,
        'status': 'ok',
        'normalized': '',
        'ast': '',
        'latex': '',
        'steps': [],
        'errors': []
    }

    try:
        # Шаг 1: Нормализация
        logger.step("Normalization")
        try:
            normalized = normalizer.normalize_text(input_text)
            result['normalized'] = normalized
            result['steps'].append({
                'step': 'normalization',
                'input': input_text,
                'output': normalized,
                'status': 'ok'
            })
            logger.debug(f"Input: {input_text!r}")
            logger.debug(f"Output: {normalized!r}")
            logger.step_end(success=True)
        except Exception as e:
            logger.step_end(success=False)
            error = NormalizationError(
                str(e),
                original_text=input_text,
                step='normalization'
            )
            result['errors'].append(error.to_dict())
            raise error

        # Шаг 2: Парсинг
        logger.step("Parsing")
        try:
            ast = parser.parse(normalized)
            result['ast'] = repr(ast)
            result['steps'].append({
                'step': 'parsing',
                'input': normalized,
                'output': repr(ast),
                'status': 'ok'
            })
            logger.debug(f"AST: {ast!r}")
            logger.step_end(success=True)
        except Exception as e:
            logger.step_end(success=False)
            logger.error(f"Parse error at: {normalized!r}")

            # Пытаемся определить позицию ошибки
            error_pos = 0
            if hasattr(e, 'pos_in_stream'):
                error_pos = e.pos_in_stream
            elif hasattr(e, 'column'):
                error_pos = e.column

            error = ParseError(
                str(e),
                normalized_text=normalized,
                position=error_pos
            )
            result['errors'].append(error.to_dict())
            raise error

        # Шаг 3: Генерация LaTeX
        logger.step("LaTeX Generation")
        try:
            latex = generator.generate(ast)
            result['latex'] = latex
            result['steps'].append({
                'step': 'generation',
                'input': repr(ast),
                'output': latex,
                'status': 'ok'
            })
            logger.debug(f"LaTeX: {latex!r}")
            logger.step_end(success=True)
        except Exception as e:
            logger.step_end(success=False)
            error = GeneratorError(
                str(e),
                ast_repr=repr(ast),
                node_type=type(ast).__name__ if ast else 'None'
            )
            result['errors'].append(error.to_dict())
            raise error

        logger.info(f"Success: {latex!r}")
        return result

    except LarkTeXError as e:
        result['status'] = 'error'
        result['latex'] = f"# {e.__class__.__name__}: {e}"
        logger.error(str(e))
        return result

    except Exception as e:
        result['status'] = 'error'
        result['latex'] = f"# Unknown error: {e}"
        logger.error(f"Unexpected error: {e}")
        if verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        return result


def main():
    """Основной цикл с поддержкой --verbose."""

    if '--verbose' in sys.argv:
        sys.argv.remove('--verbose')
    if '-v' in sys.argv:
        sys.argv.remove('-v')

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            result = process_with_debug(request.get('input', ''))

            # Выводим результат
            output = {
                'latex': result['latex'],
                'status': result['status']
            }

            # В verbose режиме добавляем детали
            if verbose:
                output['debug'] = {
                    'normalized': result.get('normalized', ''),
                    'ast': result.get('ast', ''),
                    'steps': result.get('steps', []),
                    'errors': result.get('errors', [])
                }

            print(json.dumps(output, ensure_ascii=False))

        except json.JSONDecodeError as e:
            error_result = {
                "latex": "",
                "status": "error",
                "message": f"Invalid JSON: {e}"
            }
            print(json.dumps(error_result, ensure_ascii=False))

        sys.stdout.flush()


if __name__ == "__main__":
    main()
