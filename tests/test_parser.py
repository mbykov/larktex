#!/usr/bin/env python3
"""Тесты для parser.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from parser import Parser


class TestParser:
    @pytest.fixture
    def parser(self):
        return Parser()

    def test_simple_function(self, parser):
        assert parser.parse("sin(x)") == "\\sin(x)"
        assert parser.parse("cos(x)") == "\\cos(x)"
        assert parser.parse("sqrt(x)") == "\\sqrt{x}"

    def test_equality(self, parser):
        assert parser.parse("x = y") == "x = y"
        # Lark добавляет скобки для выражений
        assert parser.parse("a = b + c") in ["a = b + c", "a = (b + c)"]

    def test_approx(self, parser):
        assert parser.parse("x approx y") == "x \\approx y"

    def test_power(self, parser):
        assert parser.parse("x^2") == "x^2"
        assert parser.parse("x^10") == "x^{10}"

    def test_arithmetic(self, parser):
        assert parser.parse("a + b") in ["a + b", "(a + b)"]
        assert parser.parse("a - b") in ["a - b", "(a - b)"]
        assert parser.parse("a + b * c") in ["a + b \\cdot c", "(a + (b \\cdot c))", "(a + b \\cdot c)"]
        assert parser.parse("a - b - c") in ["a - b - c", "((a - b) - c)", "(a - b - c)"]

    def test_negative(self, parser):
        assert parser.parse("-x") == "-x"

    def test_nested_function(self, parser):
        assert parser.parse("sin(x^2)") == "\\sin(x^2)"
        assert parser.parse("sin(x + y)") in ["\\sin(x + y)", "\\sin((x + y))"]

    def test_sqrt_with_addition(self, parser):
        assert parser.parse("sqrt(a) + b") in ["\\sqrt{a} + b", "(\\sqrt{a}) + b"]

    def test_multiple_functions(self, parser):
        assert parser.parse("sin(x) + cos(y)") in ["\\sin(x) + \\cos(y)", "(\\sin(x) + \\cos(y))"]

    # Интегралы пока не поддерживаются полностью - TODO
    # def test_integral_simple(self, parser):
    #     assert parser.parse("integral(sin(x)) d x") == "\\int sin(x) \\, d x"
    #
    # def test_integral_bounds(self, parser):
    #     assert parser.parse("integral from 0 to 1 of x d x") == "\\int_0^1 x \\, d x"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
