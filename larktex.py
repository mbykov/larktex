#!/usr/bin/env python3
"""
larktex — библиотека для преобразования математического текста в LaTeX.

Использование:
    from larktex import LarktexEngine
    
    engine = LarktexEngine()
    result = engine.process("синус от икс")
"""

import sys
from pathlib import Path
from typing import Optional, Any

# Добавляем корневую директорию в путь
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Глобальные объекты (ленивая инициализация)
_normalizer: Optional[Any] = None
_parser: Optional[Any] = None


def _get_normalizer():
    """Ленивая инициализация Normalizer."""
    global _normalizer
    if _normalizer is None:
        from lib.normalizer import Normalizer
        _normalizer = Normalizer(i18n_dir=str(ROOT_DIR / "i18n"))
    return _normalizer


def _get_parser():
    """Ленивая инициализация Parser из lib/."""
    global _parser
    if _parser is None:
        from lib.parser import Parser
        _parser = Parser()
    return _parser


class LarktexEngine:
    """
    Движок larktex с dependency injection.
    
    При инициализации:
    - По умолчанию использует глобальные объекты Normalizer и Parser (создаются один раз)
    - Можно передать свои объекты для тестирования
    
    Пример:
        engine = LarktexEngine()  # использует глобальные объекты
        engine = LarktexEngine(normalizer=my_normalizer, parser=my_parser)  # кастомные
    """

    def __init__(
        self,
        normalizer: Optional[Any] = None,
        parser: Optional[Any] = None
    ):
        # Dependency injection: можно передать свои объекты
        self.normalizer = normalizer or _get_normalizer()
        self.parser = parser or _get_parser()

    def process(self, text: str) -> str:
        """Преобразует русский текст в LaTeX."""
        normalized = self.normalizer.normalize_text(text)
        try:
            ast = self.parser.parse(normalized)
            from lib.generator import Generator
            g = Generator()
            latex = g.generate(ast)
            return latex
        except Exception as e:
            return f"# Parse error: {e}\n{normalized}"


if __name__ == "__main__":
    engine = LarktexEngine()
    tests = [
        "синус икс",
        "а плюс б всё делить на в",
        "интеграл от икс де икс",
        "a + b all / c",
    ]
    for t in tests:
        result = engine.process(t)
        print(f"{t!r} → {result!r}")
