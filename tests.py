import json
import sys
import os
from extractor import MathExtractor

import logging
logging.basicConfig(level=logging.WARNING, force=True)

def run_tests(filepath):
    ex = MathExtractor()
    passed = 0
    total = 0

    if not os.path.exists(filepath):
        print(f"Error: file {filepath} not found.")
        return

    print(f"--- Running tests from: {filepath} ---")

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                text = data.get('input')
                expected = data.get('expected')

                if not text or not expected:
                    print(f"⏩ Line {line_num}: Missing input or expected")
                    continue

                raw_result = ex.transform_text(text)
                result = raw_result.replace('$', '')

                if result == expected:
                    print(f"✅ PASS: {text}")
                    passed += 1
                else:
                    print(f"❌ FAIL: {text}")
                    print(f"   Expected: {expected}")
                    print(f"   Got:      {result}")
                    return  # Останавливаемся на первой ошибке

                total += 1

            except json.JSONDecodeError as e:
                print(f"⏩ Line {line_num}: JSON error: {e}")
            except Exception as e:
                print(f"⏩ Line {line_num}: {e}")
                import traceback
                traceback.print_exc()

    print(f"\nSummary: {passed}/{total} passed.")

if __name__ == "__main__":
    path_to_file = sys.argv[1] if len(sys.argv) > 1 else 'tests.jsonl'
    run_tests(path_to_file)
