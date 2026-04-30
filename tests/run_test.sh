#!/bin/bash
# Запуск тестов через server.py с проверкой результатов

# set -e  # Отключаем exit на ошибке для продолжения тестов

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

INPUT_FILE="${1:-tests/expected_latex.jsonl}"
STOP_ON_FAIL=1  # По умолчанию останавливаемся на первом fail

if [ ! -f "$INPUT_FILE" ]; then
    echo "Ошибка: файл $INPUT_FILE не найден"
    exit 1
fi

echo "Запуск тестов из $INPUT_FILE..."
echo "================================"

# Создаём временные файлы
TEMP_OUTPUT=$(mktemp)
TEMP_FILTERED=$(mktemp)
trap "rm -f $TEMP_OUTPUT $TEMP_FILTERED" EXIT

# Фильтруем: пропускаем пустые строки и строки без input/expected
python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        if 'input' in data and 'expected' in data:
            print(line)
    except:
        continue
" < "$INPUT_FILE" > "$TEMP_FILTERED"

# Запускаем сервер и сохраняем результаты
cat "$TEMP_FILTERED" | python server.py > "$TEMP_OUTPUT"

# Сравниваем
PASSED=0
FAILED=0

exec 3< "$TEMP_OUTPUT"
while IFS= read -r input_line; do
    read -r result_line <&3 || break
    
    input_text=$(echo "$input_line" | python -c "import sys, json; print(json.load(sys.stdin).get('input', ''))")
    expected=$(echo "$input_line" | python -c "import sys, json; print(json.load(sys.stdin).get('expected', ''))")
    latex=$(echo "$result_line" | python -c "import sys, json; print(json.load(sys.stdin).get('latex', ''))")
    status=$(echo "$result_line" | python -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))")
    
    if [ "$status" = "ok" ] && [ "$latex" = "$expected" ]; then
        echo "✓ $input_text"
        PASSED=$((PASSED + 1))
    else
        # Собираем данные
        normalized=$(echo "$result_line" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('normalized', ''))" 2>/dev/null || echo "")
        error=$(echo "$result_line" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('error', ''))" 2>/dev/null || echo "")
        
        echo "✗ FAIL: $input_text"
        echo "  Input:      $input_text"
        if [ -n "$normalized" ]; then
            echo "  Normalized: $normalized"
        fi
        echo "  Expected:   $expected"
        echo "  Got:        $latex"
        if [ "$status" != "ok" ]; then
            echo "  Status:     $status"
        fi
        if [ -n "$error" ]; then
            echo "  Error:      $error"
        fi
        FAILED=$((FAILED + 1))
        
        if [ $STOP_ON_FAIL -eq 1 ]; then
            echo "================================"
            echo "Остановка на первом fail."
            exit 1
        fi
    fi
done < "$TEMP_FILTERED" 3< "$TEMP_OUTPUT"

echo "================================"
echo "ИТОГИ: $PASSED пройдено, $FAILED не пройдено"

if [ $FAILED -gt 0 ]; then
    exit 1
fi