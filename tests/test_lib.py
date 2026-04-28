#!/usr/bin/env python3
"""Тесты для lib/ модулей с детализированным выводом."""

import json
import sys
from pathlib import Path

# Добавить корень проекта в путь
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from normalizer import Normalizer
from lib.parser import Parser
from lib.generator import Generator

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'


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
    # Путь к файлу с тестами
    tests_dir = Path(__file__).parent
    jsonl_file = tests_dir / "expected_latex.jsonl"

    if not jsonl_file.exists():
        print(f"Ошибка: файл {jsonl_file} не найден")
        sys.exit(1)

    # Инициализировать движок (ресурсы загружаются один раз)
    norm = Normalizer()
    parser = Parser()
    gen = Generator()

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
        normalized = norm.normalize(input_text)

        try:
            ast = parser.parse(normalized)
            actual = gen.generate(ast)
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
            print(f"  Expected:   {expected!r}")
            print(f"  Actual:     {actual!r}")
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
