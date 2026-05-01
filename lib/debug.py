#!/usr/bin/env python3
"""
Инструменты для отладки и логирования.
Поддержка --verbose режима для детального вывода.
"""

import sys
import json
import traceback
from typing import Optional
from datetime import datetime
from contextlib import contextmanager


class DebugLogger:
    """Логгер с поддержкой уровней детализации."""

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None):
        self.verbose = verbose
        self.log_file = log_file
        self._indent = 0

    def indent(self):
        self._indent += 1

    def dedent(self):
        self._indent = max(0, self._indent - 1)

    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Форматирует сообщение с отступом и метаданными."""
        prefix = '  ' * self._indent
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        parts = [f"{prefix}[{timestamp} {level}] {message}"]

        if kwargs and self.verbose:
            for key, value in kwargs.items():
                parts.append(f"{prefix}  {key}: {value}")

        return '\n'.join(parts)

    def info(self, message: str, **kwargs):
        self._log('INFO', message, **kwargs)

    def debug(self, message: str, **kwargs):
        if self.verbose:
            self._log('DEBUG', message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log('ERROR', message, **kwargs)

    def step(self, message: str):
        """Логирует шаг процесса."""
        self._log('STEP', f"▶ {message}")
        self.indent()

    def step_end(self, success: bool = True):
        """Завершает шаг процесса."""
        self.dedent()
        status = '✓' if success else '✗'
        self._log('STEP', f"{status} Done")

    def _log(self, level: str, message: str, **kwargs):
        formatted = self._format_message(level, message, **kwargs)
        print(formatted, file=sys.stderr)

        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(formatted + '\n')


# Глобальный экземпляр логгера
_logger: Optional[DebugLogger] = None


def get_logger() -> DebugLogger:
    """Возвращает глобальный логгер."""
    global _logger
    if _logger is None:
        _logger = DebugLogger(verbose=False)
    return _logger


def set_logger(logger: DebugLogger):
    """Устанавливает глобальный логгер."""
    global _logger
    _logger = logger


@contextmanager
def log_step(logger: DebugLogger, step_name: str):
    """Контекстный менеджер для логирования шага."""
    logger.step(step_name)
    try:
        yield
        logger.step_end(success=True)
    except Exception as e:
        logger.step_end(success=False)
        raise


def verbose_flag_supported():
    """Проверяет, поддерживается ли --verbose в аргументах командной строки."""
    return '--verbose' in sys.argv or '-v' in sys.argv
