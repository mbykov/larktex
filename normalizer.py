#!/usr/bin/env python3
"""
Normalizer — преобразует русский математический текст в латиницу.

Структура:
    DictionaryLoader — загрузка словарей
    TextNormalizer — замена слов по словарю
    MathIslandExtractor — выделение мат. фрагментов
    Normalizer — обёртка для координации
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set


class DictionaryLoader:
    """Загрузка и управление словарями."""

    def __init__(self, i18n_dir: str = "i18n"):
        self.i18n_dir = Path(i18n_dir)
        self.data: Dict[str, Any] = {}
        self._reverse_map: Dict[str, str] = {}
        self._special_phrases: List[Tuple[str, str]] = []
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
            'integrals', 'summation', 'derivatives', 'misc', 'factorials'
        ]
        
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
                    if target in greek_to_latex:
                        self._reverse_map[synonym.lower()] = greek_to_latex[target]
                    else:
                        self._reverse_map[synonym.lower()] = target
        
        misc_items = self.data.get('misc', {})
        for target, synonyms in misc_items.items():
            if target == 'open_paren':
                for synonym in synonyms:
                    if synonym.lower() in ['открыть скобку', 'открыть']:
                        self._reverse_map[synonym.lower()] = '('
            elif target == 'close_paren':
                for synonym in synonyms:
                    if synonym.lower() in ['закрыть скобку', 'закрыть']:
                        self._reverse_map[synonym.lower()] = ')'
            elif target == 'all':
                for synonym in synonyms:
                    self._reverse_map[synonym.lower()] = 'all'
        
        self._special_phrases = [
            ('квадратный корень из', 'sqrt'),
        ]

    def get_reverse_map(self) -> Dict[str, str]:
        """Возвращает обратное отображение синонимов."""
        return self._reverse_map

    def get_special_phrases(self) -> List[Tuple[str, str]]:
        """Возвращает особые составные фразы."""
        return self._special_phrases

    def get_powers(self) -> Dict[str, List[str]]:
        """Возвращает словарь степеней."""
        return self.data.get('powers', {})

    def get_data(self) -> Dict[str, Any]:
        """Возвращает загруженные данные."""
        return self.data

    def get_math_keywords(self) -> Set[str]:
        """Возвращает набор математических ключевых слов."""
        math_keywords = set()
        excluded_categories = {'noise_words', 'stop_words', 'misc', 'prepositions'}
        
        categories = ['variables', 'functions', 'operators', 'integrals', 'logic', 'relations', 'numbers', 'special', 'powers']
        for category in categories:
            if category in excluded_categories:
                continue
            for target, synonyms in self.data.get(category, {}).items():
                math_keywords.update(synonyms)
        
        for target, synonyms in self.data.get('variables', {}).items():
            if len(target) == 1 and target.isalpha():
                math_keywords.add(target.lower())
        
        return math_keywords


class TextNormalizer:
    """Только замена слов по словарю."""

    def __init__(self, dictionary_loader: DictionaryLoader):
        self.loader = dictionary_loader
        self._reverse_map = dictionary_loader.get_reverse_map()
        self._special_phrases = dictionary_loader.get_special_phrases()

    def normalize(self, text: str) -> str:
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
        
        for phrase, replacement in self._special_phrases:
            result = re.sub(r'\b' + re.escape(phrase) + r'\b', replacement, result, flags=re.IGNORECASE)
        
        result = re.sub(r'\bдробь\b\s*(.+?)\s*\bна\b\s*(.+)', lambda m: 'frac ' + m.group(1).strip() + ',' + m.group(2).strip(), result, flags=re.IGNORECASE)
        
        result = re.sub(r'\bпроизводная\b\s*\bот\b\s*(.+?)\s*\bпо\b\s*(.+)', lambda m: 'deriv with respect to ' + m.group(2), result, flags=re.IGNORECASE)
        result = re.sub(r'\bвторую производную\b', 'second deriv', result, flags=re.IGNORECASE)
        result = re.sub(r'\bчастная\b', 'partial', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\b(?:ц|цэ)\s*из\s*(\w+)\s*по\s*(\w+)', lambda m: f'binom {m.group(1)} {m.group(2)}', result, flags=re.IGNORECASE)
        result = re.sub(r'\bчисло сочетаний из\s*(\w+)\s*по\s*(\w+)', lambda m: f'binom {m.group(1)} {m.group(2)}', result, flags=re.IGNORECASE)
        result = re.sub(r'\bбиномиальный коэффициент из\s*(\w+)\s*по\s*(\w+)', lambda m: f'binom {m.group(1)} {m.group(2)}', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\b(?:а|а из)\s*из\s*(\w+)\s*по\s*(\w+)', lambda m: f'A {m.group(1)} {m.group(2)}', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\b(\d+)\s*двойной факториал\b', r'\1!!', result, flags=re.IGNORECASE)
        result = re.sub(r'\b(\w+)\s*факториал\b', r'\1!', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\bderiv\b\s*\bот\b', 'deriv', result, flags=re.IGNORECASE)
        result = re.sub(r'\bпо\b', 'with respect to', result, flags=re.IGNORECASE)
        result = re.sub(r'\bderiv\b\s*(.+?)\b(по|w\.?r\.?t\.?)\b\s*(.+)', lambda m: 'deriv with respect to ' + m.group(3), result, flags=re.IGNORECASE)
        
        for power, synonyms in self.loader.get_powers().items():
            for synonym in synonyms:
                if 'в ' in synonym or synonym.startswith('в '):
                    pattern = re.compile(r'\b' + re.escape(synonym) + r'\b', re.IGNORECASE)
                    result = pattern.sub(f'^{power}', result)
        
        pattern = re.compile(r'\bквадрат\b', re.IGNORECASE)
        result = pattern.sub('^2', result)
        pattern = re.compile(r'\bкуб\b', re.IGNORECASE)
        result = pattern.sub('^3', result)
        
        result = re.sub(r'\bвсё\b', ' all ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bвсе\b', ' all ', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\bделить на\b', ' / ', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\bде\b', ' d ', result, flags=re.IGNORECASE)
        
        for pred in ['от', 'из', 'на', 'до']:
            result = re.sub(r'\b' + pred + r'\b', ' ', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\bоткрывающая скобка\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрывающая скобка\b', ' ) ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bоткрыть\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть\b', ' ) ', result, flags=re.IGNORECASE)
        
        paren_pattern = re.compile(r'\bскобка\b', re.IGNORECASE)
        paren_matches = list(paren_pattern.finditer(result))
        
        if paren_matches:
            paren_positions = [(m.start(), m.end()) for m in paren_matches]
            total_parens = len(paren_positions)
            
            if total_parens % 2 == 1:
                raise ValueError(f"Нечетное число скобок: {total_parens}")
            
            new_result = []
            last_end = 0
            for i, (start, end) in enumerate(paren_positions):
                new_result.append(result[last_end:start])
                if i % 2 == 0:
                    new_result.append(' ( ')
                else:
                    new_result.append(' ) ')
                last_end = end
            new_result.append(result[last_end:])
            result = ''.join(new_result)
        
        result = re.sub(r'\bв\b', ' v ', result, flags=re.IGNORECASE)
        
        sorted_synonyms = sorted(self._reverse_map.keys(), key=len, reverse=True)
        
        for synonym in sorted_synonyms:
            target = self._reverse_map[synonym]
            
            if synonym in ['открыть скобку', 'закрыть скобку', 'открыть', 'закрыть']:
                continue
            if 'в ' in synonym:
                continue
            if synonym in ['от', 'из', 'на', 'до', 'в', 'делить на', 'де', 'всё', 'все', 'all']:
                continue
            if len(synonym) == 1 and synonym.isascii() and synonym.isalpha():
                continue
            
            pattern = re.compile(r'\b' + re.escape(synonym) + r'\b', re.IGNORECASE)
            if target.startswith('\\'):
                result = pattern.sub(lambda m: target, result)
            else:
                result = pattern.sub(target, result)
        
        result = re.sub(r'\ball\s*$', 'all * 1', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\s+\^', '^', result)
        result = re.sub(r'\(\s+', '(', result)
        result = re.sub(r'\s+\)', ')', result)
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result


class MathIslandExtractor:
    """Выделение математических фрагментов из текста."""

    def __init__(self, dictionary_loader: DictionaryLoader):
        self.loader = dictionary_loader
        self._math_keywords = dictionary_loader.get_math_keywords()
        self._sorted_keywords = sorted(self._math_keywords, key=len, reverse=True)

    def extract(self, text: str) -> List[Tuple[str, bool]]:
        """Выделить математические сегменты из текста."""
        first_split = re.split(r'([,.:;])', text)
        
        result = []
        
        for segment in first_split:
            if not segment.strip():
                continue
            
            if segment.strip() in ',:.;':
                result.append((segment, False))
                continue
            
            segment_lower = segment.lower()
            
            math_spans = []
            for keyword in self._sorted_keywords:
                keyword_lower = keyword.lower()
                pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b')
                for match in pattern.finditer(segment_lower):
                    math_spans.append((match.start(), match.end()))
            
            if not math_spans:
                result.append((segment, False))
                continue
            
            math_spans.sort()
            merged_spans = [math_spans[0]]
            for span in math_spans[1:]:
                last = merged_spans[-1]
                if span[0] <= last[1]:
                    merged_spans[-1] = (last[0], max(last[1], span[1]))
                else:
                    merged_spans.append(span)
            
            pos = 0
            in_math = False
            math_start = 0
            math_end = 0
            
            for span_start, span_end in merged_spans:
                if not in_math:
                    if pos < span_start:
                        text_before = segment[pos:span_start]
                        if text_before.strip():
                            result.append((text_before, False))
                    in_math = True
                    math_start = span_start
                
                math_end = span_end
                pos = span_end
            
            if in_math:
                math_island = segment[math_start:math_end]
                result.append((math_island, True))
        
        if len(result) > 1:
            merged_result = []
            i = 0
            while i < len(result):
                seg, is_math = result[i]
                if not is_math:
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


class Normalizer:
    """Обёртка для координации компонентов нормализации."""

    def __init__(self, i18n_dir: str = "i18n"):
        self.loader = DictionaryLoader(i18n_dir)
        self.text_normalizer = TextNormalizer(self.loader)
        self.island_extractor = MathIslandExtractor(self.loader)

    def process(self, text: str) -> str:
        """Полная обработка текста с выделением островов."""
        islands = self.island_extractor.extract(text)
        
        result_parts = []
        for segment, is_math in islands:
            if is_math:
                normalized = self.text_normalizer.normalize(segment)
                result_parts.append(normalized)
            else:
                result_parts.append(segment)
        
        return ''.join(result_parts)

    def normalize(self, text: str) -> str:
        """Нормализовать текст без выделения островов."""
        return self.text_normalizer.normalize(text)

    # Методы-обёртки для совместимости с существующим кодом
    def normalize_text(self, text: str) -> str:
        """Алиас для normalize()."""
        return self.normalize(text)
    
    def extract_math_islands(self, text: str) -> List[Tuple[str, bool]]:
        """Алиас для island_extractor.extract()."""
        return self.island_extractor.extract(text)


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