#!/usr/bin/env python3
"""
larktex — CLI и сервер для преобразования математического текста в LaTeX.

Режимы:
  CLI:    uv run larktex.py "синус от икс"
  Server: uv run larktex.py --server --port 8000
  Test:   uv run larktex.py --test
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Добавляем корневую директорию в путь
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))


class LarktexEngine:
    """
    Движок larktex с однократной загрузкой ресурсов.
    
    При инициализации:
    - Загружает i18n/ru.json один раз
    - Создаёт Normalizer и Parser
    
    Метод `process()` переиспользует эти объекты.
    """

    _instance: Optional['LarktexEngine'] = None

    def __init__(self):
        from normalizer import Normalizer
        from parser import Parser
        
        self.normalizer = Normalizer(i18n_dir=str(ROOT_DIR / "i18n"))
        self.parser = Parser()

    @classmethod
    def get_instance(cls) -> 'LarktexEngine':
        """Глобальный синглтон — ресурсы загружаются один раз."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def process(self, text: str) -> str:
        """Преобразует русский текст в LaTeX."""
        normalized = self.normalizer.normalize_text(text)
        try:
            parsed = self.parser.parse(normalized)
            # Применяем design: проверка скобок + \sin, \cos и т.д.
            from design import design
            latex, error = design(parsed)
            if error:
                return f"# Design error: {error}\n{parsed}"
            return latex
        except Exception as e:
            return f"# Parse error: {e}\n{normalized}"


def run_cli(input_text: str):
    """CLI режим: один запрос и выход."""
    engine = LarktexEngine.get_instance()
    result = engine.process(input_text)
    print(result)


def run_tests():
    """Запуск тестов через verify_normalizer."""
    from tests.verify_normalizer import main as verify_main
    sys.exit(verify_main())


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    HTTP сервер для обработки запросов.
    
    ENDPOINTS:
      POST /convert
        Body: {"text": "синус от икс"}
        Response: {"normalized": "sin x", "latex": "\\sin(x)"}
      
      GET /health
        Response: {"status": "ok"}
    """
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        import uvicorn
    except ImportError:
        print("Error: fastapi и uvicorn не установлены.")
        print("Установите: uv add fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(title="larktex", description="Math text to LaTeX converter")
    
    class ConvertRequest(BaseModel):
        text: str

    class ConvertResponse(BaseModel):
        normalized: str
        latex: str

    # Инициализация движка при старте (ресурсы загружаются один раз)
    engine = LarktexEngine()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/convert", response_model=ConvertResponse)
    def convert(req: ConvertRequest):
        """Преобразует математический текст в LaTeX."""
        normalized = engine.normalizer.normalize_text(req.text)
        try:
            parsed = engine.parser.parse(normalized)
            from design import design
            latex, error = design(parsed)
            if error:
                latex = f"# Error: {error}\n{parsed}"
        except Exception as e:
            latex = f"# Error: {e}\n{normalized}"
        return {"normalized": normalized, "latex": latex}

    @app.post("/process")
    def process(text: str):
        """Альтернативный endpoint: просто текст → LaTeX."""
        result = engine.process(text)
        return {"result": result}

    print(f"Запуск сервера на http://{host}:{port}")
    print("Endpoints:")
    print(f"  POST /convert - {{'text': 'синус от икс'}}")
    print(f"  GET  /health  - статус")
    
    uvicorn.run(app, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(
        description='larktex — Math text to LaTeX converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  CLI режим:
    uv run larktex.py "синус от икс"
    uv run larktex.py "корень из а плюс б в квадрате"

  Серверный режим:
    uv run larktex.py --server
    uv run larktex.py --server --port 8080

  Тесты:
    uv run larktex.py --test
        """
    )
    
    parser.add_argument('input', nargs='?', help='Математический текст на русском')
    parser.add_argument('--server', action='store_true', help='Запустить HTTP сервер')
    parser.add_argument('--port', type=int, default=8000, help='Порт сервера (по умолчанию: 8000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Хост сервера (по умолчанию: 0.0.0.0)')
    parser.add_argument('--test', action='store_true', help='Запустить тесты')
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
        return
    
    if args.server:
        run_server(host=args.host, port=args.port)
        return
    
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    run_cli(args.input)


if __name__ == "__main__":
    main()