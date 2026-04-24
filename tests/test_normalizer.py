#!/usr/bin/env python3
"""Тесты для нормализатора."""

import pytest
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizer import Normalizer


class TestNormalizer:
    """Тесты для класса Normalizer."""

    @pytest.fixture
    def normalizer(self):
        """Создаёт экземпляр Normalizer для тестов."""
        return Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    def test_simple_function(self, normalizer):
        """Простая функция: синус икс."""
        result = normalizer.normalize_text("синус икс")
        assert result == "sin x"

    def test_function_with_preposition(self, normalizer):
        """Функция с предлогом: синус от икс."""
        result = normalizer.normalize_text("синус от икс")
        assert result == "sin x"

    def test_equation(self, normalizer):
        """Уравнение: икс равно игрек."""
        result = normalizer.normalize_text("икс равно игрек")
        assert result == "x = y"

    def test_sqrt(self, normalizer):
        """Корень: корень из а плюс б."""
        result = normalizer.normalize_text("корень из а плюс б")
        assert result == "sqrt a + b"

    def test_integral(self, normalizer):
        """Интеграл: интеграл от синус икс де икс."""
        result = normalizer.normalize_text("интеграл синус икс де икс")
        assert result == "integral sin x d x"

    def test_greek_letter(self, normalizer):
        """Греческая буква: дельта равно нулю."""
        result = normalizer.normalize_text("дельта равно нулю")
        assert result == "δ = 0"

    def test_case_normalization(self, normalizer):
        """Нормализация падежей: синуса -> синус."""
        result = normalizer.normalize_text("синуса икса")
        assert "sin" in result and "x" in result

    def test_power_square(self, normalizer):
        """Степень квадрат: икс в квадрате."""
        result = normalizer.normalize_text("икс в квадрате")
        assert result == "x^2"

    def test_power_cube(self, normalizer):
        """Степень куб: икс в кубе."""
        result = normalizer.normalize_text("икс в кубе")
        assert result == "x^3"

    def test_capital_letter(self, normalizer):
        """Заглавная буква: а заглавная."""
        result = normalizer.normalize_text("а заглавная")
        assert result == "A"

    def test_capital_with_function(self, normalizer):
        """Функция от заглавной буквы: синус а заглавная."""
        result = normalizer.normalize_text("синус а заглавная")
        assert result == "sin A"

    def test_hyperbolic_function(self, normalizer):
        """Гиперболическая функция: синус гиперболический."""
        result = normalizer.normalize_text("синус гиперболический икс")
        assert result == "sinh x"

    def test_arcsin(self, normalizer):
        """Обратная функция: арксинус."""
        result = normalizer.normalize_text("арксинус икс")
        assert result == "arcsin x"

    def test_multiple_variables(self, normalizer):
        """Несколько переменных: икс плюс игрек плюс зет."""
        result = normalizer.normalize_text("икс плюс игрек плюс зет")
        assert result == "x + y + z"

    def test_complex_expression(self, normalizer):
        """Сложное выражение: корень квадратный из а плюс б делить на два."""
        result = normalizer.normalize_text("корень из а плюс б делить на два")
        assert "sqrt" in result and "+" in result and "/" in result

    def test_numbers(self, normalizer):
        """Числа: от нуля до десяти."""
        result = normalizer.normalize_text("от нуля до десяти")
        assert "0" in result and "10" in result

    def test_double_integral(self, normalizer):
        """Двойной интеграл."""
        result = normalizer.normalize_text("двойной интеграл от икс до игрек")
        assert "integral" in result.lower() or "double_integral" in result.lower()

    def test_parentheses(self, normalizer):
        """Скобки: открыть скобку икс плюс игрек закрыть скобку."""
        result = normalizer.normalize_text("открыть скобку икс плюс игрек закрыть скобку")
        assert "( x + y )" in result or "(x + y)" in result

    def test_pi(self, normalizer):
        """Константа пи."""
        result = normalizer.normalize_text("пи")
        assert result == "pi"

    def test_euler(self, normalizer):
        """Число Эйлера."""
        result = normalizer.normalize_text("эйлер")
        assert result == "e"


class TestRealData:
    """Тесты на реальных данных из файла raw_input.txt."""

    @pytest.fixture
    def normalizer(self):
        """Создаёт экземпляр Normalizer для тестов."""
        return Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    @pytest.fixture
    def test_data(self):
        """Загружает тестовые данные."""
        test_file = Path(__file__).parent / "raw_input.txt"
        if test_file.exists():
            with open(test_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return []

    def test_process_real_data(self, normalizer, test_data):
        """Обработка реальных данных не должна падать."""
        for line in test_data[:50]:  # Первые 50 строк
            result = normalizer.process(line)
            # Просто проверяем, что результат — строка
            assert isinstance(result, str)

    def test_sample_real_inputs(self, normalizer):
        """Проверка некоторых реальных примеров."""
        test_cases = [
            ("мю равно хи", True),
            ("синус икс делить эм заглавная", True),
            ("интеграл от пяти до три от синус игрек де игрек", True),
            ("котангенс от интеграл синус эр заглавная де эр заглавная", True),
        ]
        
        for input_text, should_work in test_cases:
            result = normalizer.process(input_text)
            assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
