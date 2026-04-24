#!/usr/bin/env python3
"""
Normalizer — преобразует русский математический текст в латиницу.

Этапы:
1. Загрузка словарей синонимов и метаданных
2. Нормализация падежных форм к базовой форме
3. Замена синонимов на латинские символы/слова
4. Выделение математических "островов" из обычного текста
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any


class Normalizer:
    """Нормализатор математического текста."""

    def __init__(self, i18n_dir: str = "i18n"):
        self.i18n_dir = Path(i18n_dir)
        self.synonyms: Dict[str, Dict[str, List[str]]] = {}
        self.lang_data: Dict[str, Any] = {}
        self._reverse_map: Dict[str, str] = {}
        
        self._load_resources()

    def _load_resources(self) -> None:
        """Загрузить словари синонимов и метаданные языка."""
        # Загружаем synonyms_ru.json
        synonyms_file = self.i18n_dir / "synonyms_ru.json"
        if synonyms_file.exists():
            with open(synonyms_file, 'r', encoding='utf-8') as f:
                self.synonyms = json.load(f)
        
        # Загружаем ru.json
        lang_file = self.i18n_dir / "ru.json"
        if lang_file.exists():
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.lang_data = json.load(f)
        
        # Создаём обратное отображение: синоним -> нормальная форма
        self._build_reverse_map()

    def _build_reverse_map(self) -> None:
        """Создать обратное отображение для быстрой замены."""
        for category, items in self.synonyms.items():
            for target, synonyms in items.items():
                for synonym in synonyms:
                    # Все синонимы отображаются на одну нормальную форму
                    self._reverse_map[synonym.lower()] = target

    def normalize_case(self, word: str) -> str:
        """
        Нормализовать падежную форму слова к базовой.
        
        Ищет слово в синонимах и возвращает каноническую форму.
        """
        word_lower = word.lower()
        
        # Ищем точное совпадение в обратном отображении
        if word_lower in self._reverse_map:
            return self._reverse_map[word_lower]
        
        # Попытка найти по частичному совпадению (для составных форм)
        for synonym, target in self._reverse_map.items():
            if synonym in word_lower or word_lower in synonym:
                return target
        
        return word  # Возвращаем как есть, если не найдено

    def normalize_text(self, text: str) -> str:
        """
        Нормализовать весь текст: заменить все синонимы на латиницу.
        
        Порядок замен:
        1. Сначала заменяем "в квадрате", "в кубе" и т.д. (степени с "в")
        2. Затем удаляем предлоги (от, из, на)
        3. Заменяем "де" на "d" (дифференциал)
        4. Заменяем "открыть скобку" и "закрыть скобку"
        5. Длинные слова сначала (чтобы избежать частичных замен)
        6. Падежные формы -> базовая форма
        7. Базовая форма -> латиница
        8. Очистка лишних пробелов
        """
        result = text
        
        # Сначала обрабатываем "в квадрате", "в кубе" и т.д. (до удаления "в")
        for power, synonyms in self.synonyms.get('powers', {}).items():
            for synonym in synonyms:
                if 'в' in synonym:  # Фразы типа "в квадрате"
                    pattern = re.compile(
                        r'\b' + re.escape(synonym) + r'\b',
                        re.IGNORECASE
                    )
                    result = pattern.sub(f'^{power}', result)
        
        # Сначала удаляем предлоги (они не нужны в LaTeX)
        for pred in ['от', 'из', 'на', 'до']:
            result = re.sub(r'\b' + pred + r'\b', ' ', result, flags=re.IGNORECASE)
        
        # Заменяем "де" на "d" (дифференциал)
        result = re.sub(r'\bде\b', 'd', result, flags=re.IGNORECASE)
        
        # Обработка "открыть скобку" и "закрыть скобку"
        result = re.sub(r'\bоткрыть скобку\b', '(', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть скобку\b', ')', result, flags=re.IGNORECASE)
        
        # Сортируем ключи по длине (убывание) для замены длинных слов первыми
        sorted_synonyms = sorted(self._reverse_map.keys(), key=len, reverse=True)
        
        for synonym in sorted_synonyms:
            target = self._reverse_map[synonym]
            # Пропускаем предлоги и служебные слова
            if synonym in ['от', 'из', 'на', 'в', 'де', 'до']:
                continue
            # Пропускаем уже обработанные конструкции
            if synonym in ['открыть скобку', 'закрыть скобку']:
                continue
            # Пропускаем фразы со "в" (они уже обработаны)
            if 'в ' in synonym or synonym.startswith('в '):
                continue
            # Пропускаем "д" если target — "D" (чтобы не перезаписывать дифференциал "d")
            if synonym == 'д' and target == 'D':
                continue
            # Пропускаем однобуквенные латинские символы (чтобы не менять x → X)
            if len(synonym) == 1 and synonym.isascii() and synonym.isalpha():
                continue
            # Заменяем с учётом регистра
            pattern = re.compile(
                r'\b' + re.escape(synonym) + r'\b',
                re.IGNORECASE
            )
            result = pattern.sub(target, result)
        
        # Очистка лишних пробелов (несколько пробелов → один)
        # Убираем пробелы перед "^" и после "("
        result = re.sub(r'\s+\^', '^', result)  # "x ^2" → "x^2"
        result = re.sub(r'\(\s+', '(', result)   # "( x" → "(x"
        result = re.sub(r'\s+\)', ')', result)   # "y )" → "y)"
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result

    def extract_math_islands(self, text: str) -> List[Tuple[str, bool]]:
        """
        Выделить математические "острова" из текста.
        
        Возвращает список кортежей (сегмент, is_mathematical).
        
        Эвристика: сегмент считается математическим, если содержит:
        - Известные функции (синус, корень, логарифм)
        - Известные переменные (икс, дельта, лямбда)
        - Математические операторы (плюс, умножить, в степени)
        """
        # Простая эвристика: разбиваем по запятым и точкам
        # и проверяем каждый сегмент
        
        segments = re.split(r'([,.:;])', text)
        result = []
        
        math_keywords = set()
        for category, items in self.synonyms.items():
            if category in ['functions', 'variables', 'operators', 'integrals', 'logic']:
                for target, synonyms in items.items():
                    math_keywords.update(synonyms)
        
        for i, segment in enumerate(segments):
            if not segment.strip():
                continue
            
            # Проверяем, содержит ли сегмент математические ключевые слова
            segment_lower = segment.lower()
            is_math = any(
                keyword in segment_lower 
                for keyword in math_keywords
            )
            
            # Если это разделитель — он не математический
            if segment.strip() in ',:.;':
                is_math = False
            
            result.append((segment, is_math))
        
        return result

    def normalize_segment(self, text: str) -> str:
        """
        Нормализовать один математический сегмент.
        
        Применяет полную цепочку нормализации.
        """
        # 1. Нормализация падежей и замена на латиницу
        result = self.normalize_text(text)
        
        # 2. Обработка специальных конструкций
        result = self._handle_special_constructs(result)
        
        return result

    def _handle_special_constructs(self, text: str) -> str:
        """Обработать специальные математические конструкции."""
        result = text
        
        # Обработка "в квадрате", "в кубе" и т.д.
        for power, synonyms in self.synonyms.get('powers', {}).items():
            for synonym in synonyms:
                # "в квадрате" -> "^2", "квадрат" -> "^2"
                pattern = re.compile(
                    r'\b' + re.escape(synonym) + r'\b',
                    re.IGNORECASE
                )
                result = pattern.sub(f'^{power}', result)
        
        # Обработка "открыть скобку" и "закрыть скобку"
        result = re.sub(r'\bоткрыть скобку\b', '(', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть скобку\b', ')', result, flags=re.IGNORECASE)
        
        # Удаление "заглавная" после переменной (она уже учтена в словаре)
        result = re.sub(r'\bзаглавная\b', '', result, flags=re.IGNORECASE)
        
        # Очистка лишних пробелов
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result

    def process(self, text: str) -> str:
        """
        Полная обработка текста:
        1. Выделение математических островов
        2. Нормализация только математических сегментов
        3. Сборка результата
        """
        islands = self.extract_math_islands(text)
        
        result_parts = []
        for segment, is_math in islands:
            if is_math:
                normalized = self.normalize_segment(segment)
                result_parts.append(normalized)
            else:
                result_parts.append(segment)
        
        return ''.join(result_parts)


def main():
    """Тестовый запуск нормализатора."""
    normalizer = Normalizer()
    
    test_cases = [
        "синус от икс",
        "икс равно игрек",
        "корень из а плюс б",
        "интеграл от синус икс де икс",
        "дельта равно нулю",
    ]
    
    for test in test_cases:
        result = normalizer.process(test)
        print(f"{test!r} → {result!r}")


if __name__ == "__main__":
    main()
