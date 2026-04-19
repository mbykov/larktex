import json
from extractor import MathExtractor

def run_tests():
    ex = MathExtractor()
    passed = 0
    total = 0

    try:
        with open('tests.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                total += 1
                data = json.loads(line)
                text = data['input']
                expected = data['expected']

                result = ex.transform(text)

                if result == expected:
                    print(f"✅ PASS: {text} -> {result}")
                    passed += 1
                else:
                    print(f"❌ FAIL: {text}")
                    print(f"   Expected: {expected}")
                    print(f"   Got:      {result}")
    except FileNotFoundError:
        print("Error: tests.jsonl not found.")
        return

    print(f"\nSummary: {passed}/{total} passed.")

if __name__ == "__main__":
    run_tests()
