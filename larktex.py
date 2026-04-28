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
from typing import Optional, Any, Any

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
        from normalizer import Normalizer
        _normalizer = Normalizer(i18n_dir=str(ROOT_DIR / "i18n"))
    return _normalizer


def _get_parser():
    """Ленивая инициализация Parser."""
    global _parser
    if _parser is None:
        from parser import Parser
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
            parsed = self.parser.parse(normalized)
            # Применяем design: проверка скобок + \sin, \cos и т.д.
            from design import design
            latex, error = design(parsed)
            if error:
                return f"# Design error: {error}\n{parsed}"
            return latex
        except Exception as e:
            return f"# Parse error: {e}\n{normalized}"