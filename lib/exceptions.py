#!/usr/bin/env python3
"""
Иерархия исключений для LarkTeX.
Каждое исключение содержит полный контекст ошибки для отладки.
"""

from typing import Optional, Any, Dict


class LarkTeXError(Exception):
    """Базовое исключение для всех ошибок LarkTeX."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}

    def to_dict(self) -> dict:
        """Сериализация ошибки в словарь для логирования."""
        return {
            'error_type': self.__class__.__name__,
            'message': str(self),
            'details': self.details
        }

    def __str__(self):
        msg = f"[{self.__class__.__name__}] {super().__str__()}"
        if self.details:
            for key, value in self.details.items():
                msg += f"\n  {key}: {value}"
        return msg


class NormalizationError(LarkTeXError):
    """Ошибка на этапе нормализации текста."""

    def __init__(self, message: str, original_text: str = '',
                 normalized_text: str = '', step: str = '', **kwargs):
        details = {
            'original_text': original_text,
            'normalized_text': normalized_text,
            'step': step,
            **kwargs
        }
        super().__init__(message, details)


class ParseError(LarkTeXError):
    """Ошибка на этапе парсинга нормализованного текста."""

    def __init__(self, message: str, normalized_text: str = '',
                 position: int = 0, **kwargs):
        # Выделяем контекст вокруг ошибки
        context = ""
        if normalized_text and position:
            context_start = max(0, position - 20)
            context_end = min(len(normalized_text), position + 20)
            context = normalized_text[context_start:context_end]

        details = {
            'normalized_text': normalized_text,
            'error_position': position,
            'context': f"...{context}..." if context else "",
            **kwargs
        }
        super().__init__(message, details)


class GeneratorError(LarkTeXError):
    """Ошибка на этапе генерации LaTeX из AST."""

    def __init__(self, message: str, ast_repr: str = '',
                 node_type: str = '', **kwargs):
        details = {
            'ast': ast_repr,
            'node_type': node_type,
            **kwargs
        }
        super().__init__(message, details)
