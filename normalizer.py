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
            'integrals', 'summation'
        ]
        
        # Маппинг греческих букв на LaTeX-термины
        greek_to_latex = {
            'α': '\\alpha', 'β': '\\beta', 'γ': '\\gamma', 'δ': '\\delta',
            'ε': '\\epsilon', 'ζ': '\\zeta', 'η': '\\eta', 'θ': '\\theta',
            'ι': '\\iota', 'κ': '\\kappa', 'λ': '\\lambda', 'μ': '\\mu',
            'ν': '\\nu', 'ξ': '\\xi', 'π': '\\pi', 'ρ': '\\rho',
            'σ': '\\sigma', 'τ': '\\tau', 'φ': '\\phi', 'χ': '\\chi',
            'ψ': '\\psi', 'ω': '\\omega'
        }
        
        for category in categories_to_process:
            items = self.data.get(category, {})
            for target, synonyms in items.items():
                for synonym in synonyms:
                    # Если цель - греческая буква, мапим на LaTeX
                    if target in greek_to_latex:
                        self._reverse_map[synonym.lower()] = greek_to_latex[target]
                    else:
                        self._reverse_map[synonym.lower()] = target
        
        # Особая обработка misc: open_paren -> '(', close_paren -> ')'
        misc_items = self.data.get('misc', {})
        for target, synonyms in misc_items.items():
            if target == 'open_paren':
                for synonym in synonyms:
                    # Явные команды открывающей скобки
                    if synonym.lower() in ['открыть скобку', 'открыть']:
                        self._reverse_map[synonym.lower()] = '('
            elif target == 'close_paren':
                for synonym in synonyms:
                    # Явные команды закрывающей скобки
                    if synonym.lower() in ['закрыть скобку', 'закрыть']:
                        self._reverse_map[synonym.lower()] = ')'
            elif target == 'all':
                for synonym in synonyms:
                    self._reverse_map[synonym.lower()] = 'all'

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
        
        # 1.1 Обработка "квадрат" и "куб" без предлога "в" (для конструкций типа "синус квадрат")
        # "квадрат", "в квадрате" -> ^2
        pattern = re.compile(r'\bквадрат\b', re.IGNORECASE)
        result = pattern.sub('^2', result)
        # "куб" -> ^3
        pattern = re.compile(r'\bкуб\b', re.IGNORECASE)
        result = pattern.sub('^3', result)
        
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
        result = re.sub(r'\bоткрывающая скобка\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрывающая скобка\b', ' ) ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bоткрыть\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть\b', ' ) ', result, flags=re.IGNORECASE)
        
        # 6.1 Обработка простого слова "скобка":
        # - первая "скобка" → "(", последняя → ")"
        # - внутренние: нечетные → "(", четные → ")"
        # - ошибка если: первая не "(", последняя не ")", нечетное число скобок
        paren_pattern = re.compile(r'\bскобка\b', re.IGNORECASE)
        paren_matches = list(paren_pattern.finditer(result))
        
        if paren_matches:
            paren_positions = [(m.start(), m.end()) for m in paren_matches]
            total_parens = len(paren_positions)
            
            if total_parens % 2 == 1:
                raise ValueError(f"Нечетное число скобок: {total_parens}")
            
            # Заменяем: нечетные (0, 2, 4...) → "(", четные (1, 3, 5...) → ")"
            new_result = []
            last_end = 0
            for i, (start, end) in enumerate(paren_positions):
                new_result.append(result[last_end:start])
                if i % 2 == 0:  # 0, 2, 4... → открывающая
                    new_result.append(' ( ')
                else:  # 1, 3, 5... → закрывающая
                    new_result.append(' ) ')
                last_end = end
            new_result.append(result[last_end:])
            result = ''.join(new_result)
        
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
            # Для LaTeX терминов используем lambda чтобы избежать интерпретации backslash
            if target.startswith('\\'):
                result = pattern.sub(lambda m: target, result)
            else:
                result = pattern.sub(target, result)
        
        # 9. Очистка пробелов (сохраняем пробелы вокруг операторов)
        result = re.sub(r'\s+\^', '^', result)  # Пробел перед ^ удаляем
        result = re.sub(r'\(\s+', '(', result)  # Пробел после ( удаляем
        result = re.sub(r'\s+\)', ')', result)  # Пробел перед ) удаляем
        
        result = re.sub(r'\s+', ' ', result).strip()  # Остальные пробелы нормализуем
        
        return result

    def extract_math_islands(self, text: str) -> List[Tuple[str, bool]]:
        """Выделить математические сегменты из текста."""
        # Сначала разбить по пунктуации
        first_split = re.split(r'([,.:;])', text)
        
        # Ключевые слова для определения мат-островов (исключаем noise_words, misc)
        math_keywords = set()
        # Исключаем эти категории из мат-ключей
        excluded_categories = {'noise_words', 'stop_words', 'misc', 'prepositions'}
        
        categories = ['variables', 'functions', 'operators', 'integrals', 'logic', 'relations', 'numbers', 'special', 'powers']
        for category in categories:
            if category in excluded_categories:
                continue
            for target, synonyms in self.data.get(category, {}).items():
                math_keywords.update(synonyms)
        
        # Добавляем одиночные буквы из variables как мат-ключи (для выделения островов)
        for target, synonyms in self.data.get('variables', {}).items():
            # Добавляем односимвольные переменные
            if len(target) == 1 and target.isalpha():
                math_keywords.add(target.lower())
        
        # Сортируем ключевые слова по длине (длинные первыми)
        sorted_keywords = sorted(math_keywords, key=len, reverse=True)
        
        result = []
        
        for segment in first_split:
            if not segment.strip():
                continue
            
            # Если это разделитель — не математика
            if segment.strip() in ',:.;':
                result.append((segment, False))
                continue
            
            segment_lower = segment.lower()
            
            # Найти все позиции математических ключевых слов (полные слова)
            math_spans = []
            for keyword in sorted_keywords:
                keyword_lower = keyword.lower()
                # Используем \b для границ слов
                pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b')
                for match in pattern.finditer(segment_lower):
                    math_spans.append((match.start(), match.end()))
            
            if not math_spans:
                # Нет математики — весь сегмент как текст
                result.append((segment, False))
                continue
            
            # Сортируем и объединяем перекрывающиеся спаны
            math_spans.sort()
            merged_spans = [math_spans[0]]
            for span in math_spans[1:]:
                last = merged_spans[-1]
                # Объединяем если перекрываются или смежные
                if span[0] <= last[1]:
                    merged_spans[-1] = (last[0], max(last[1], span[1]))
                else:
                    merged_spans.append(span)
            
            # Разбиваем сегмент: объединяем мат-фрагменты в один остров,
            # если между ними только пробелы
            pos = 0
            in_math = False
            math_start = 0
            math_end = 0
            
            for span_start, span_end in merged_spans:
                if not in_math:
                    # Начинаем новый мат-остров
                    # Если есть текст перед мат-фрагментом — добавляем его
                    if pos < span_start:
                        text_before = segment[pos:span_start]
                        if text_before.strip():
                            result.append((text_before, False))
                    in_math = True
                    math_start = span_start
                
                # Расширяем мат-остров (включая промежуточный текст)
                math_end = span_end
                pos = span_end
            
            # Добавляем весь мат-остров с промежуточным текстом
            if in_math:
                math_island = segment[math_start:math_end]
                result.append((math_island, True))
        
        # Объединяем смежные TEXT-фрагменты
        if len(result) > 1:
            merged_result = []
            i = 0
            while i < len(result):
                seg, is_math = result[i]
                if not is_math:
                    # Начинаем TEXT-блок, объединяем все смежные TEXT-фрагменты
                    combined_text = seg
                    i += 1
                    while i < len(result) and not result[i][1]:
                        combined_text += result[i][0]
                        i += 1
                    merged_result.append((combined_text, False))
                else:
                    merged_result.append((seg, is_math))
                    i += 1
            result = merged_result
        
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