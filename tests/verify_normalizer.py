#!/usr/bin/env python3
"""
Тестирование нормализатора на реальных данных с независимыми эталонными результатами.
Сравнивает output нормализатора с expected из expected_outputs.jsonl
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizer import Normalizer


def load_expected(filepath: Path) -> dict:
    """Загрузить эталонные результаты."""
    expected = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            expected[data['id']] = data['expected']
    return expected


def main():
    normalizer = Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    expected_file = Path(__file__).parent / "expected_outputs.jsonl"
    expected = load_expected(expected_file)

    input_file = Path(__file__).parent / "raw_input.txt"

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    passed = 0
    failed = 0
    errors = []

    for i, line in enumerate(lines, 1):
        if i not in expected:
            continue  # Пропускаем строки без эталона

        actual = normalizer.process(line)
        expected_output = expected[i]

        if actual == expected_output:
            passed += 1
            print(f"✓ {i}: {line!r}")
        else:
            failed += 1
            errors.append({
                'id': i,
                'input': line,
                'expected': expected_output,
                'actual': actual
            })
            print(f"✗ {i}: {line!r}")
            print(f"  Expected: {expected_output!r}")
            print(f"  Actual:   {actual!r}")

    print(f"\n{'='*50}")
    print(f"Результаты: {passed} passed, {failed} failed")

    if errors:
        print(f"\nОшибки ({len(errors)}):")
        for err in errors[:10]:  # Показать первые 10 ошибок
            print(f"  ID {err['id']}: {err['input']!r}")
            print(f"    Expected: {err['expected']!r}")
            print(f"    Actual:   {err['actual']!r}")
        if len(errors) > 10:
            print(f"  ... и ещё {len(errors) - 10} ошибок")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
