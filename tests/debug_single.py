#!/bin/bash
# Отладка одного теста с максимальной детализацией

if [ $# -eq 0 ]; then
    echo "Использование: $0 'математическое выражение'"
    echo "Пример: $0 'корень из а плюс б'"
    exit 1
fi

INPUT_TEXT="$1"

echo "=== Отладка одного теста ==="
echo "Input: $INPUT_TEXT"
echo ""

# Нормализация
echo "--- Нормализация ---"
cd "$(dirname "$0")/.."
NORMALIZED=$(python3 -c "
import sys
sys.path.insert(0, '.')
from lib.normalizer import Normalizer
n = Normalizer()
print(n.normalize_text('$INPUT_TEXT'))
" 2>&1)
echo "Normalized: $NORMALIZED"
echo ""

# Парсинг
echo "--- Парсинг ---"
AST=$(python3 -c "
import sys
sys.path.insert(0, '.')
from lib.parser import Parser
p = Parser()
try:
    ast = p.parse('$NORMALIZED')
    print(repr(ast))
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
" 2>&1)
echo "$AST"
echo ""

# Генерация LaTeX
echo "--- Генерация LaTeX ---"
LATEX=$(python3 -c "
import sys
sys.path.insert(0, '.')
from lib.parser import Parser
from lib.generator import Generator
p = Parser()
g = Generator()
try:
    ast = p.parse('$NORMALIZED')
    latex = g.generate(ast)
    print(latex)
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)
echo "LaTeX: $LATEX"
echo ""

echo "=== Отладка завершена ==="
