#!/usr/bin/env python3
"""
Normalizer — преобразует русский математический текст в латиницу.

Читает только i18n/ru.json.
НЕ добавляет скобки! Только заменяет термины:
- "всё"/"все" → "all"
- "открыть скобку" → "(", "закрыть скобку" → ")"
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any


class Normalizer:
    """Нормализатор математического текста."""

    def __init__(self, i18n_dir: str = "i18n"):
        self.i18n_dir = Path(i18n_dir)
        self.data: Dict[str, Any] = {}
        self._reverse_map: Dict[str, str] = {}
        
        self._load_resources()

    def _load_resources(self) -> None:
        """Загрузить словарь ru.json."""
        lang_file = self.i18n_dir / "ru.json"
        if not lang_file.exists():
            raise FileNotFoundError(f"i18n/ru.json not found: {lang_file}")
        
        with open(lang_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self._build_reverse_map()

    def _build_reverse_map(self) -> None:
        """Создать обратное отображение: синоним -> целевое значение."""
        categories_to_process = [
            'variables', 'functions', 'operators', 'powers', 
            'numbers', 'special', 'logic', 'relations', 
            'integrals', 'summation', 'misc'
        ]
        
        for category in categories_to_process:
            items = self.data.get(category, {})
            for target, synonyms in items.items():
                for synonym in synonyms:
                    self._reverse_map[synonym.lower()] = target

    def normalize_text(self, text: str) -> str:
        """
        Нормализовать текст: заменить все синонимы на латиницу.
        
        Порядок:
        1. Фразы со "в" (в квадрате, в кубе) — до удаления "в"
        2. "всё" / "все" → "all"
        3. "делить на" → "/"
        4. "де" → "d" (для дифференциала)
        5. Удалить предлоги (от, из, на, до)
        6. Обработка скобок (только явные команды)
        7. "в" как переменная → "v"
        8. Длинные синонимы первыми
        9. Очистить пробелы
        """
        result = text
        
        # 1. Обработка степеней: "в квадрате", "в кубе" и т.д.
        for power, synonyms in self.data.get('powers', {}).items():
            for synonym in synonyms:
                if 'в ' in synonym or synonym.startswith('в '):
                    pattern = re.compile(
                        r'\b' + re.escape(synonym) + r'\b',
                        re.IGNORECASE
                    )
                    result = pattern.sub(f'^{power}', result)
        
        # 2. "всё" / "все" → "all" (просто замена слова, БЕЗ скобок)
        result = re.sub(r'\bвсё\b', ' all ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bвсе\b', ' all ', result, flags=re.IGNORECASE)
        
        # 3. "делить на" → "/"
        result = re.sub(r'\bделить на\b', ' / ', result, flags=re.IGNORECASE)
        
        # 4. "де" → "d" (дифференциал: "де икс" → "d x")
        result = re.sub(r'\bде\b', ' d ', result, flags=re.IGNORECASE)
        
        # 5. Удалить предлоги (кроме "в" — он может быть переменной)
        for pred in ['от', 'из', 'на', 'до']:
            result = re.sub(r'\b' + pred + r'\b', ' ', result, flags=re.IGNORECASE)
        
        # 6. Обработка явных скобок (только если пользователь сказал "скобка")
        result = re.sub(r'\bоткрыть скобку\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть скобку\b', ' ) ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bоткрывающая скобка\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрывающая скобка\b', ' ) ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bоткрыть\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть\b', ' ) ', result, flags=re.IGNORECASE)
        
        # 7. "в" как переменная → "v"
        result = re.sub(r'\bв\b', ' v ', result, flags=re.IGNORECASE)
        
        # 8. Длинные синонимы первыми
        sorted_synonyms = sorted(self._reverse_map.keys(), key=len, reverse=True)
        
        for synonym in sorted_synonyms:
            target = self._reverse_map[synonym]
            
            # Пропускаем уже обработанные
            if synonym in ['открыть скобку', 'закрыть скобку', 'открыть', 'закрыть']:
                continue
            if 'в ' in synonym:
                continue
            if synonym in ['от', 'из', 'на', 'до', 'в', 'делить на', 'де', 'всё', 'все', 'all']:
                continue
            if len(synonym) == 1 and synonym.isascii() and synonym.isalpha():
                continue
            
            pattern = re.compile(
                r'\b' + re.escape(synonym) + r'\b',
                re.IGNORECASE
            )
            result = pattern.sub(target, result)
        
        # 9. Очистка пробелов (сохраняем пробелы вокруг операторов)
        result = re.sub(r'\s+\^', '^', result)  # Пробел перед ^ удаляем
        result = re.sub(r'\(\s+', '(', result)  # Пробел после ( удаляем
        result = re.sub(r'\s+\)', ')', result)  # Пробел перед ) удаляем
        result = re.sub(r'\s+', ' ', result).strip()  # Остальные пробелы нормализуем
        
        return result

    def extract_math_islands(self, text: str) -> List[Tuple[str, bool]]:
        """Выделить математические сегменты из текста."""
        segments = re.split(r'([,.:;])', text)
        result = []
        
        math_keywords = set()
        categories = ['variables', 'functions', 'operators', 'integrals', 'logic', 'relations']
        for category in categories:
            for target, synonyms in self.data.get(category, {}).items():
                math_keywords.update(synonyms)
        
        for segment in segments:
            if not segment.strip():
                continue
            
            segment_lower = segment.lower()
            is_math = any(keyword in segment_lower for keyword in math_keywords)
            
            if segment.strip() in ',:.;':
                is_math = False
            
            result.append((segment, is_math))
        
        return result

    def process(self, text: str) -> str:
        """Полная обработка текста с выделением островов."""
        islands = self.extract_math_islands(text)
        
        result_parts = []
        for segment, is_math in islands:
            if is_math:
                normalized = self.normalize_text(segment)
                result_parts.append(normalized)
            else:
                result_parts.append(segment)
        
        return ''.join(result_parts)


def main():
    """Тестовый запуск."""
    normalizer = Normalizer()
    
    test_cases = [
        "синус от икс",
        "икс равно игрек",
        "корень из а плюс б",
        "интеграл от синус икс де икс",
        "дельта равно нулю",
        "икс в квадрате",
        "а заглавная плюс б",
        "а плюс б всё делить на в",
        "открыть скобку а плюс б закрыть скобку",
    ]
    
    for test in test_cases:
        result = normalizer.process(test)
        print(f"{test!r} → {result!r}")


if __name__ == "__main__":
    main()