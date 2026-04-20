import json
import sys
import os
import logging
from extractor import MathExtractor

# Принудительная настройка логирования (убираем INFO)
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
        for line in f:
            line = line.strip()
            if not line: continue

            try:
                # 1. Пытаемся распарсить как JSON (для tests.jsonl)
                if line.startswith('{'):
                    data = json.loads(line)
                    # Поддержка разных ключей (input/expected или rus/script)
                    text = data.get('input') or data.get('rus')
                    expected = data.get('expected') or data.get('script')

                # 2. Если это формат "rus": текст, "script": латекс (как в sin.txt)
                elif '"rus":' in line:
                    # Очень простая нарезка строки
                    parts = line.split('"script":')
                    text = parts[0].replace('"rus":', '').strip(' ",')
                    expected = parts[1].strip(' "')
                else:
                    continue

                if not text or not expected: continue

                # Выполняем трансформацию
                raw_result = ex.transform_text(text)
                # Убираем $ для чистого сравнения
                result = raw_result.replace('$', '')

                if result == expected:
                    print(f"✅ PASS: {text} -> {raw_result}")
                    passed += 1
                else:
                    print(f"❌ FAIL: {text}")
                    print(f"   Expected: {expected}")
                    print(f"   Got:      {result}")
                    # Детальная диагностика перед выходом
                    norm = ex.normalize_island(text)
                    print(f"   Normalized as: '{norm}'")

                    sys.exit(1) # Жесткая остановка
                total += 1
            except Exception as e:
                print(f"⏩ Skip line error: {e}")

    print(f"\nSummary: {passed}/{total} passed.")

if __name__ == "__main__":
    # Если передан аргумент, используем его, иначе стандартный файл
    path_to_file = sys.argv[1] if len(sys.argv) > 1 else 'tests.jsonl'
    run_tests(path_to_file)
