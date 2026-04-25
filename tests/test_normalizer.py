#!/usr/bin/env python3
"""Тесты для нормализатора на данных из expected_outputs.jsonl."""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizer import Normalizer


def load_test_cases():
    """Загрузить тесты из expected_outputs.jsonl."""
    jsonl_file = Path(__file__).parent / "expected_outputs.jsonl"
    tests = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tests.append(json.loads(line))
    return tests


class TestNormalizer:
    """Тесты нормализатора."""

    @pytest.fixture
    def normalizer(self):
        return Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Настройка для отображения точек."""
        if request.node.name.startswith('test_case_'):
            sys.stdout.write('.')
            sys.stdout.flush()
        yield

    def test_all_cases(self, normalizer):
        """Единый тест для всех случаев из JSONL."""
        test_cases = load_test_cases()
        for i, tc in enumerate(test_cases):
            actual = normalizer.process(tc['input'])
            expected = tc['expected']
            assert actual == expected, (
                f"\n\nTest {i} (ID {tc.get('id', 'N/A')}):\n"
                f"  Input:    {tc['input']!r}\n"
                f"  Expected: {expected!r}\n"
                f"  Actual:   {actual!r}"
            )


class TestBasicNormalization:
    """Базовые тесты нормализации."""

    @pytest.fixture
    def normalizer(self):
        return Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    def test_simple_function(self, normalizer):
        result = normalizer.normalize_text("синус икс")
        assert "sin" in result and "x" in result

    def test_equation(self, normalizer):
        result = normalizer.normalize_text("икс равно игрек")
        assert "=" in result

    def test_power_square(self, normalizer):
        result = normalizer.normalize_text("икс в квадрате")
        assert "^2" in result

    def test_greek_letter(self, normalizer):
        result = normalizer.normalize_text("дельта")
        assert "δ" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])