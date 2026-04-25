#!/usr/bin/env python3
"""
Валидация нормализатора на данных из expected_outputs.jsonl.
Читает input из JSONL, вызывает нормализатор, сравнивает с expected.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizer import Normalizer


def main():
    normalizer = Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    jsonl_file = Path(__file__).parent / "expected_outputs.jsonl"
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    passed = 0
    failed = 0
    errors = []

    for i, tc in enumerate(test_cases):
        input_text = tc['input']
        expected = tc['expected']
        
        actual = normalizer.process(input_text)
        
        if actual == expected:
            passed += 1
            print(f"✓ {i}: {input_text!r}")
        else:
            failed += 1
            errors.append({
                'id': i,
                'input': input_text,
                'expected': expected,
                'actual': actual
            })
            print(f"✗ {i}: {input_text!r}")
            print(f"  Expected: {expected!r}")
            print(f"  Actual:   {actual!r}")

    print(f"\n{'='*50}")
    print(f"Результаты: {passed} passed, {failed} failed")

    if errors:
        print(f"\nОшибки ({len(errors)}):")
        for err in errors[:10]:
            print(f"  ID {err['id']}: {err['input']!r}")
            print(f"    Expected: {err['expected']!r}")
            print(f"    Actual:   {err['actual']!r}")
        if len(errors) > 10:
            print(f"  ... и ещё {len(errors) - 10} ошибок")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())