#!/usr/bin/env python3
"""Тесты для полного пайплайна: input → LaTeX."""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from larktex import LarktexEngine


class TestLarktexPipeline:
    """Тесты на данных из expected_latex.jsonl."""

    @pytest.fixture
    def engine(self):
        return LarktexEngine()

    @pytest.fixture
    def test_cases(self):
        jsonl_file = Path(__file__).parent / "expected_latex.jsonl"
        tests = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    tests.append(json.loads(line))
        return tests

    @pytest.mark.parametrize("tc", [
        pytest.param(tc, id=f"test_{i}")
        for i, tc in enumerate([])  # Динамическая генерация
    ])
    def test_pipeline(self, engine, tc):
        """Проверка полного пайплайна."""
        result = engine.process(tc['input'])
        expected = tc['expected']
        assert result == expected, f"got {result!r}, expected {expected!r}"


# Динамическая генерация тестов
def load_test_cases():
    jsonl_file = Path(__file__).parent / "expected_latex.jsonl"
    tests = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                tests.append((i, json.loads(line)))
    return tests


for i, tc in load_test_cases():
    def make_test(data, idx):
        def test_method(self, engine):
            result = engine.process(data['input'])
            expected = data['expected']
            assert result == expected, f"ID {idx}: got {result!r}, expected {expected!r}"
        return test_method
    
    setattr(TestLarktexPipeline, f"test_latex_{i}", make_test(tc, i))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
