#!/bin/bash
# Быстрая отладка одного математического выражения
# Использование: ./tests/debug_single.sh "корень из а плюс б"

if [ $# -eq 0 ]; then
    echo "Использование: $0 'математическое выражение'"
    echo "Пример: $0 'корень из а плюс б'"
    exit 1
fi

INPUT_TEXT="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Отладка математического выражения           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Input: $INPUT_TEXT"
echo ""

# Шаг 1: Нормализация
echo "┌──────────────────────────────────────────────────────────┐"
echo "│ Шаг 1: Нормализация                                     │"
echo "└──────────────────────────────────────────────────────────┘"

python3 -c "
import sys
sys.path.insert(0, '.')
from lib.normalizer import Normalizer
n = Normalizer()
result = n.normalize_text('$INPUT_TEXT')
print(f'Результат: {result}')
" 2>&1

NORMALIZED=$(python3 -c "
import sys
sys.path.insert(0, '.')
from lib.normalizer import Normalizer
n = Normalizer()
print(n.normalize_text('$INPUT_TEXT'))
" 2>&1)

echo ""

# Шаг 2: Парсинг
echo "┌──────────────────────────────────────────────────────────┐"
echo "│ Шаг 2: Парсинг                                          │"
echo "└──────────────────────────────────────────────────────────┘"

python3 -c "
import sys
sys.path.insert(0, '.')
from lib.parser import Parser
p = Parser()
try:
    ast = p.parse('$NORMALIZED')
    print(f'AST: {ast!r}')
except Exception as e:
    print(f'ОШИБКА: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""

# Шаг 3: Генерация LaTeX
echo "┌──────────────────────────────────────────────────────────┐"
echo "│ Шаг 3: Генерация LaTeX                                  │"
echo "└──────────────────────────────────────────────────────────┘"

python3 -c "
import sys
sys.path.insert(0, '.')
from lib.parser import Parser
from lib.generator import Generator
p = Parser()
g = Generator()
try:
    ast = p.parse('$NORMALIZED')
    latex = g.generate(ast)
    print(f'LaTeX: {latex}')
except Exception as e:
    print(f'ОШИБКА: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""

# Шаг 4: Полный pipeline через сервер
echo "┌──────────────────────────────────────────────────────────┐"
echo "│ Шаг 4: Полный pipeline (server.py)                 b     │"
echo "└──────────────────────────────────────────────────────────┘"

echo "{\"input\": \"$INPUT_TEXT\"}" | python3 server.py --verbose 2>&1

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    Отладка завершена                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
