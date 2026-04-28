#!/bin/bash
# Запуск тестов через server.py с проверкой результатов

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

INPUT_FILE="${1:-tests/expected_latex.jsonl}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Ошибка: файл $INPUT_FILE не найден"
    exit 1
fi

echo "Запуск тестов из $INPUT_FILE..."
echo "================================"

# Создаём временный файл для результатов
TEMP_OUTPUT=$(mktemp)
trap "rm -f $TEMP_OUTPUT" EXIT

# Запускаем сервер и сохраняем результаты
cat "$INPUT_FILE" | python server.py > "$TEMP_OUTPUT"

# Сравниваем
PASSED=0
FAILED=0

while IFS= read -r input_line && IFS= read -r result_line <&3; do
    expected=$(echo "$input_line" | python -c "import sys, json; print(json.load(sys.stdin).get('expected', ''))")
    latex=$(echo "$result_line" | python -c "import sys, json; print(json.load(sys.stdin).get('latex', ''))")
    status=$(echo "$result_line" | python -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))")
    
    if [ "$status" = "ok" ] && [ "$latex" = "$expected" ]; then
        echo "✓ $(echo "$input_line" | python -c "import sys, json; print(json.load(sys.stdin).get('input', ''))")"
        PASSED=$((PASSED + 1))
    else
        echo "✗ FAIL: $(echo "$input_line" | python -c "import sys, json; print(json.load(sys.stdin).get('input', ''))")"
        if [ "$status" != "ok" ]; then
            echo "  Status: $status"
        fi
        echo "  Expected: $expected"
        echo "  Got:      $latex"
        FAILED=$((FAILED + 1))
    fi
done < "$INPUT_FILE" 3< "$TEMP_OUTPUT"

echo "================================"
echo "ИТОГИ: $PASSED пройдено, $FAILED не пройдено"

if [ $FAILED -gt 0 ]; then
    exit 1
fi