#!/bin/bash
# Запуск тестов через server.py с проверкой результатов

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Значения по умолчанию
INPUT_FILE="tests/expected_latex.jsonl"
VERBOSE=false
STOP_ON_FAIL=true
DEBUG_SINGLE=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case "$1" in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --continue|-c)
            STOP_ON_FAIL=false
            shift
            ;;
        --debug|-d)
            DEBUG_SINGLE=true
            shift
            ;;
        *)
            INPUT_FILE="$1"
            shift
            ;;
    esac
done

if [ ! -f "$INPUT_FILE" ]; then
    echo "Ошибка: файл $INPUT_FILE не найден"
    echo "Доступные файлы:"
    ls -1 tests/*.jsonl 2>/dev/null || echo "  (нет .jsonl файлов)"
    exit 1
fi

echo "Запуск тестов из $INPUT_FILE..."
echo "================================"

# Создаем временные файлы
TEMP_INPUT=$(mktemp)
TEMP_OUTPUT=$(mktemp)
trap "rm -f $TEMP_INPUT $TEMP_OUTPUT" EXIT

# Фильтруем и сохраняем входные данные
python3 -c "
import sys, json
count = 0
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        data = json.loads(line)
        if 'input' in data and 'expected' in data:
            print(line)
            count += 1
    except:
        continue
print(f'Total tests: {count}', file=sys.stderr)
" < "$INPUT_FILE" > "$TEMP_INPUT"

# Проверяем, есть ли тесты
if [ ! -s "$TEMP_INPUT" ]; then
    echo "Ошибка: нет валидных тестов в $INPUT_FILE"
    exit 1
fi

# Запускаем сервер и сохраняем вывод
if [ "$VERBOSE" = true ]; then
    cat "$TEMP_INPUT" | python3 server.py --verbose > "$TEMP_OUTPUT" 2>/dev/null
else
    cat "$TEMP_INPUT" | python3 server.py > "$TEMP_OUTPUT" 2>/dev/null
fi

# Проверяем, что вывод не пустой
if [ ! -s "$TEMP_OUTPUT" ]; then
    echo "Ошибка: сервер не вернул результатов"
    echo "Проверьте:"
    echo "  head -1 $TEMP_INPUT | python3 server.py"
    exit 1
fi

# Сравниваем результаты
PASSED=0
FAILED=0
TEST_NUM=0

# Читаем оба файла построчно
while IFS= read -r input_line && IFS= read -r output_line <&3; do
    TEST_NUM=$((TEST_NUM + 1))

    # Извлекаем данные
    input_text=$(echo "$input_line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('input', ''))" 2>/dev/null)
    expected=$(echo "$input_line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('expected', ''))" 2>/dev/null)
    latex=$(echo "$output_line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('latex', ''))" 2>/dev/null)
    status=$(echo "$output_line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

    if [ "$status" = "ok" ] && [ "$latex" = "$expected" ]; then
        echo "✓ $input_text"
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))

        echo ""
        echo "✗ FAIL #$FAILED: $input_text"
        echo "  Expected: $expected"
        echo "  Got:      $latex"
        echo "  Status:   $status"

        if [ "$VERBOSE" = true ]; then
            normalized=$(echo "$output_line" | python3 -c "
import sys, json
d = json.load(sys.stdin)
debug = d.get('debug', {})
print(debug.get('normalized', 'no data'))
" 2>/dev/null)
            echo "  Normalized: $normalized"
        fi

        echo ""

        if [ "$DEBUG_SINGLE" = true ]; then
            echo "Запуск детальной отладки..."
            ./tests/debug_single.sh "$input_text"
            exit 1
        fi

        if [ "$STOP_ON_FAIL" = true ]; then
            echo "Остановка на первом fail."
            echo "Для отладки: ./tests/debug_single.sh '$input_text'"
            exit 1
        fi
    fi
done < "$TEMP_INPUT" 3< "$TEMP_OUTPUT"

echo ""
echo "================================"
echo "ИТОГИ: $PASSED пройдено, $FAILED не пройдено из $TEST_NUM"
echo "================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
