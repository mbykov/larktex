#!/usr/bin/env python3
"""Тесты для нормализатора на данных из expected_outputs.jsonl."""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizer import Normalizer


class TestNormalizerFromJSONL:
    """Тесты на данных из expected_outputs.jsonl."""

    @pytest.fixture
    def normalizer(self):
        return Normalizer(i18n_dir=str(Path(__file__).parent.parent / "i18n"))

    @pytest.fixture
    def test_cases(self):
        """Загрузить тестовые данные из expected_outputs.jsonl."""
        jsonl_file = Path(__file__).parent / "expected_outputs.jsonl"
        tests = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tests.append(json.loads(line))
        return tests

    @pytest.mark.parametrize("test_data", [
        pytest.param(tc, id=f"id_{tc['id']}")
        for tc in []  # Заполняется динамически
    ])
    def test_from_jsonl(self, normalizer, test_data):
        """Проверка каждого примера из expected_outputs.jsonl."""
        actual = normalizer.process(test_data['input'])
        expected = test_data['expected']
        assert actual == expected, f"ID {test_data['id']}: got {actual!r}, expected {expected!r}"


def load_test_cases():
    """Загрузить тесты для параметризации."""
    jsonl_file = Path(__file__).parent / "expected_outputs.jsonl"
    tests = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tests.append(json.loads(line))
    return tests


# Динамическая генерация тестов
for i, tc in enumerate(load_test_cases()):
    def make_test(data, idx):
        def test_method(self, normalizer):
            actual = normalizer.process(data['input'])
            expected = data['expected']
            assert actual == expected, f"Test {idx}: got {actual!r}, expected {expected!r}"
        return test_method
    
    test_name = f"test_from_jsonl_{i}"
    setattr(TestNormalizerFromJSONL, test_name, make_test(tc, i))


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