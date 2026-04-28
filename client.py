#!/usr/bin/env python3
"""Клиент для сервера larktex.

Поддерживает два режима:
1. CLI: python client.py "синус икс"
2. Batch: cat input.jsonl | python client.py

Примеры:
  echo '{"input": "синус икс"}' | python client.py
  python client.py "корень из а"
  cat tests.jsonl | python client.py > output.jsonl
"""

import json
import sys
from pathlib import Path

# Добавляем корень проекта в путь
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from larktex import LarktexEngine

engine = LarktexEngine()


def convert(text: str) -> str:
    """Конвертирует текст в LaTeX."""
    return engine.process(text)


def process_line(line: str) -> dict:
    """Обрабатывает одну строку JSON."""
    line = line.strip()
    if not line:
        return None
    
    try:
        data = json.loads(line)
        input_text = data.get('input', '')
        if not input_text:
            return {"latex": "", "status": "error", "message": "No input"}
        
        latex = convert(input_text)
        status = "ok" if not latex.startswith('#') else "error"
        return {"latex": latex, "status": status}
    
    except json.JSONDecodeError:
        # Если не JSON, пробуем как простой текст
        latex = convert(line)
        return {"latex": latex, "status": "ok"}
    except Exception as e:
        return {"latex": "", "status": "error", "message": str(e)}


def main():
    """Основной цикл."""
    # Если передан аргумент - CLI режим
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        latex = convert(text)
        print(json.dumps({"latex": latex, "status": "ok" if not latex.startswith('#') else "error"}, ensure_ascii=False))
        return
    
    # Иначе - batch режим (stdin)
    for line in sys.stdin:
        result = process_line(line)
        if result:
            print(json.dumps(result, ensure_ascii=False))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
