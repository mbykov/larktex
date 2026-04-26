#!/usr/bin/env python3
"""Тесты для larktex с детализированным выводом."""

import argparse
import json
import sys
from pathlib import Path

# Добавить корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from larktex import LarktexEngine


# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'


def parse_args():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Тесты для larktex')
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='Путь к файлу JSONL с тестами (по умолчанию: tests/expected_latex.jsonl)'
    )
    return parser.parse_args()


def load_test_cases(jsonl_path: Path):
    """Загрузить тесты из JSONL файла."""
    tests = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    test_data = json.loads(line)
                    test_data['_line_num'] = line_num
                    tests.append(test_data)
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга строки {line_num}: {e}")
                    sys.exit(1)
    return tests


def main():
    """Запуск тестов с детализированным выводом."""
    args = parse_args()

    # Путь к файлу с тестами
    tests_dir = Path(__file__).parent
    if args.file:
        jsonl_file = Path(args.file)
        if not jsonl_file.is_absolute():
            jsonl_file = tests_dir.parent / args.file
    else:
        jsonl_file = tests_dir / "expected_latex.jsonl"

    if not jsonl_file.exists():
        print(f"Ошибка: файл {jsonl_file} не найден")
        sys.exit(1)

    # Инициализировать движок (ресурсы загружаются один раз)
    engine = LarktexEngine()

    # Загрузить тесты
    test_cases = load_test_cases(jsonl_file)

    if not test_cases:
        print("Нет тестов для выполнения")
        sys.exit(1)

    passed = 0
    failed = 0

    for i, tc in enumerate(test_cases):
        input_text = tc.get('input', '')
        expected = tc.get('expected', '')
        line_num = tc.get('_line_num', '?')

        # Выполнить нормализацию
        normalized = engine.normalizer.normalize_text(input_text)

        try:
            parsed = engine.parser.parse(normalized)
            from design import design
            latex, error = design(parsed)
            if error:
                actual = f"# Design error: {error}\n{parsed}"
            else:
                actual = latex
        except Exception as e:
            print(f"\n{RED}--- Тест (строка {line_num}) ---{RESET}")
            print(f"  Input:      {input_text!r}")
            print(f"  Normalized: {normalized!r}")
            print(f"  Actual:     ERROR: {e}")
            print(f"{'=' * 60}")
            print(f"\n{RED}ИТОГИ: {passed} пройдено, 1 не пройдено из {len(test_cases)}{RESET}")
            print(f"{'=' * 60}")
            sys.exit(1)

        # Проверить результат
        if actual == expected:
            print(f"{GREEN}✓{RESET} {input_text} - {expected}")
            passed += 1
        else:
            print(f"\n{RED}--- Тест (строка {line_num}) ---{RESET}")
            print(f"  Input:      {input_text!r}")
            print(f"  Normalized: {normalized!r}")
            print(f"  Parsed:     {parsed!r}")
            print(f"  Expected:   {expected!r}")
            print(f"  Actual:     {actual!r}")
            
            # Показать различия
            print(f"\n  Различия:")
            print(f"    Ожидаемая длина: {len(expected)}")
            print(f"    Фактическая длина: {len(actual)}")
            
            # Показать посимвольно
            min_len = min(len(expected), len(actual))
            for pos in range(min_len):
                if expected[pos] != actual[pos]:
                    print(f"    Первая разница на позиции {pos}:")
                    print(f"      Expected[{pos}]: {expected[pos]!r} (ord={ord(expected[pos])})")
                    print(f"      Actual[{pos}]:   {actual[pos]!r} (ord={ord(actual[pos])})")
                    
                    # Показать контекст вокруг различия
                    ctx_start = max(0, pos - 10)
                    ctx_end_exp = min(len(expected), pos + 10)
                    ctx_end_act = min(len(actual), pos + 10)
                    print(f"\n    Контекст (Expected): ...{expected[ctx_start:ctx_end_exp]!r}...")
                    print(f"    Контекст (Actual):   ...{actual[ctx_start:ctx_end_act]!r}...")
                    break
            
            # Показать diff-подобный вывод
            print(f"\n  Пошаговое сравнение токенов:")
            exp_tokens = expected.split()
            act_tokens = actual.split()
            
            max_tokens = max(len(exp_tokens), len(act_tokens))
            for j in range(max_tokens):
                exp_tok = exp_tokens[j] if j < len(exp_tokens) else "(нет)"
                act_tok = act_tokens[j] if j < len(act_tokens) else "(нет)"
                marker = "✓" if exp_tok == act_tok else "✗"
                print(f"    [{j:2d}] {marker} Expected: {exp_tok!r:15} Actual: {act_tok!r}")
            
            print(f"{'=' * 60}")
            print(f"\n{RED}ИТОГИ: {passed} пройдено, 1 не пройдено из {len(test_cases)}{RESET}")
            print(f"{'=' * 60}")
            sys.exit(1)

    # Итоговая статистика
    print(f"\n{'=' * 60}")
    print(f"ИТОГИ: {passed} пройдено, {failed} не пройдено из {len(test_cases)}")
    print(f"{'=' * 60}")

    sys.exit(0)


if __name__ == "__main__":
    main()
