#!/usr/bin/env python3
"""Сервер larktex через stdin/stdout.

Читает JSON-объекты из stdin, пишет результаты в stdout.
Формат:
  Вход:  {"input": "синус икс"}
  Выход: {"latex": "\\sin(x)", "status": "ok"}

Пример использования:
  echo '{"input": "синус икс"}' | python server.py
  cat tests.jsonl | python server.py
"""

import json
import sys
from pathlib import Path

# Добавляем корень проекта в путь
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from larktex import LarktexEngine

# Создаём один экземпляр (ресурсы грузятся один раз)
engine = LarktexEngine()


def process_request(data: dict) -> dict:
    """Обрабатывает запрос и возвращает результат."""
    input_text = data.get('input', '')
    
    if not input_text:
        return {"latex": "", "status": "error", "message": "No input provided"}
    
    try:
        latex = engine.process(input_text)
        # Проверяем, нет ли ошибок парсинга
        if latex.startswith('# Parse error:') or latex.startswith('# Design error:'):
            return {"latex": latex, "status": "error", "message": latex.split('\n')[0]}
        return {"latex": latex, "status": "ok"}
    except Exception as e:
        return {"latex": "", "status": "error", "message": str(e)}


def main():
    """Основной цикл: читает JSON из stdin, пишет в stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            result = process_request(request)
            print(json.dumps(result, ensure_ascii=False))
        except json.JSONDecodeError as e:
            error_result = {"latex": "", "status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(error_result, ensure_ascii=False))
        
        # fflush stdout
        sys.stdout.flush()


if __name__ == "__main__":
    main()
