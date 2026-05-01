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

    def get_numerals(self) -> Dict[str, List[str]]:
        """Возвращает словарь числительных."""
        return self.data.get('numerals', {})

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
    """Замена слов по словарю с правильной последовательностью обработки."""

    def __init__(self, dictionary_loader: DictionaryLoader):
        self.loader = dictionary_loader
        self._reverse_map = dictionary_loader.get_reverse_map()
        self._special_phrases = dictionary_loader.get_special_phrases()

    def _handle_all(self, text: str) -> str:
        """
        Обработка all (всё/все).

        Правила:
        1. В степенях и корнях: all = закрывающая }
        2. В остальных случаях: all = закрывающая )
        """
        # all в степенях: ^{X всё} -> ^{X}
        text = re.sub(
            r'\^\{(.+?)\s+(?:всё|все|all)\s*\}',
            r'^{\1}',
            text,
            flags=re.IGNORECASE
        )

        # all в корнях: sqrt{X всё} -> sqrt{X}
        text = re.sub(
            r'sqrt\{(.+?)\s+(?:всё|все|all)\s*\}',
            r'sqrt{\1}',
            text,
            flags=re.IGNORECASE
        )

        # all в корнях со степенью: sqrt[N]{X всё} -> sqrt[N]{X}
        text = re.sub(
            r'sqrt\[(.+?)\]\{(.+?)\s+(?:всё|все|all)\s*\}',
            r'sqrt[\1]{\2}',
            text,
            flags=re.IGNORECASE
        )

        # all в обычных выражениях: expression всё -> (expression)
        while True:
            match = re.search(r'\b(?:всё|все|all)\b', text, flags=re.IGNORECASE)
            if not match:
                break

            pos = match.start()
            left_text = text[:pos].rstrip()

            # Ищем последний оператор
            op_match = re.search(
                r'\s[+\-*/]\s(?=(?:[^+\-*/]*)$)',
                left_text
            )

            if op_match:
                insert_pos = op_match.end()
                text = text[:insert_pos] + '(' + text[insert_pos:]
            else:
                text = '(' + text

            all_pos = text.find(match.group(0))
            text = text[:all_pos] + ')' + text[all_pos + len(match.group(0)):]

        return text

    def _handle_power(self, text: str) -> str:
        """
        Обработка степеней.
        Выполняется ПОСЛЕ замены числительных и all-группировки,
        ДО замены "в" на "v".
        """
        # "в степени X всё" -> ^{X}
        text = re.sub(
            r'\bв\s+степени\s+(.+?)\s+(?:всё|все|all)\b',
            r'^{\1}',
            text,
            flags=re.IGNORECASE
        )

        # "в степени X" (без all — всё до конца строки)
        text = re.sub(
            r'\bв\s+степени\s+(.+)$',
            r'^{\1}',
            text,
            flags=re.IGNORECASE
        )

        # "в минус N" -> ^{-N} (числительные уже заменены на цифры)
        text = re.sub(
            r'\bв\s+минус\s+(\d+)\b',
            r'^{-\1}',
            text,
            flags=re.IGNORECASE
        )

        # Простые степени из словаря (в квадрате, в кубе, в пятой и т.д.)
        for power, synonyms in self.loader.get_powers().items():
            for synonym in synonyms:
                pattern = re.compile(r'\b' + re.escape(synonym) + r'\b', re.IGNORECASE)
                text = pattern.sub(f'^{power}', text)

        # Дополнительные степени
        text = re.sub(r'\bквадрат\b', '^2', text, flags=re.IGNORECASE)
        text = re.sub(r'\bкуб\b', '^3', text, flags=re.IGNORECASE)

        return text

    def _handle_sqrt(self, text: str) -> str:
        """Обработка корней."""
        # Корень степени N с all
        text = re.sub(
            r'sqrt\s*\[(.+?)\]\s*(?:от|из)\s+(.+?)\s+(?:всё|все|all)\b',
            r'sqrt[\1]{\2}',
            text,
            flags=re.IGNORECASE
        )

        # Корень степени N без all
        text = re.sub(
            r'sqrt\s*\[(.+?)\]\s*(?:от|из)\s+(.+)$',
            r'sqrt[\1]{\2}',
            text,
            flags=re.IGNORECASE
        )

        # Простой корень с all
        text = re.sub(
            r'sqrt\s*(?:от|из)\s+(.+?)\s+(?:всё|все|all)\b',
            r'sqrt{\1}',
            text,
            flags=re.IGNORECASE
        )

        # Простой корень без all
        text = re.sub(
            r'sqrt\s*(?:от|из)\s+(.+)$',
            r'sqrt{\1}',
            text,
            flags=re.IGNORECASE
        )

        # Корень через "квадратный корень из"
        text = re.sub(
            r'квадратный\s+корень\s+(?:от|из)\s+(.+?)\s+(?:всё|все|all)\b',
            r'sqrt{\1}',
            text,
            flags=re.IGNORECASE
        )
        text = re.sub(
            r'квадратный\s+корень\s+(?:от|из)\s+(.+)$',
            r'sqrt{\1}',
            text,
            flags=re.IGNORECASE
        )

        return text

    def normalize(self, text: str) -> str:
        """
        Нормализовать текст.

        Порядок обработки (критически важен):
        1. Специальные фразы
        2. Дроби
        3. Производные
        4. Биномиальные коэффициенты
        5. Факториалы
        6. Числительные
        7. Замена "всё/все" на " all "
        8. Обработка all для группировки (ДО степеней!)
        9. Степени (ПОСЛЕ all-группировки, ДО замены "в" на "v")
        10. Корни
        11. Базовые замены (делить на, де)
        12. Удаление предлогов (от, из, на, до — НЕ "в"!)
        13. Обработка скобок
        14. Замена "в" на "v" (ТОЛЬКО ПОСЛЕ степеней)
        15. Замена синонимов по словарю
        16. Очистка пробелов
        """
        result = text

        # 1. Специальные фразы
        for phrase, replacement in self._special_phrases:
            result = re.sub(
                r'\b' + re.escape(phrase) + r'\b',
                replacement,
                result,
                flags=re.IGNORECASE
            )

        # 2. Дроби
        result = re.sub(
            r'\bдробь\b\s*(.+?)\s*\bна\b\s*(.+)',
            lambda m: 'frac ' + m.group(1).strip() + ',' + m.group(2).strip(),
            result,
            flags=re.IGNORECASE
        )

        # 3. Производные
        result = re.sub(
            r'\bпроизводная\b\s*\bот\b\s*(.+?)\s*\bпо\b\s*(.+)',
            lambda m: 'deriv with respect to ' + m.group(2),
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(r'\bвторую производную\b', 'second deriv', result, flags=re.IGNORECASE)
        result = re.sub(r'\bчастная\b', 'partial', result, flags=re.IGNORECASE)

        # 4. Биномиальные коэффициенты
        result = re.sub(
            r'\b(?:ц|цэ)\s*из\s*(\w+)\s*по\s*(\w+)',
            lambda m: f'binom {m.group(1)} {m.group(2)}',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'\bчисло сочетаний из\s*(\w+)\s*по\s*(\w+)',
            lambda m: f'binom {m.group(1)} {m.group(2)}',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'\bбиномиальный коэффициент из\s*(\w+)\s*по\s*(\w+)',
            lambda m: f'binom {m.group(1)} {m.group(2)}',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'\b(?:а|а из)\s*из\s*(\w+)\s*по\s*(\w+)',
            lambda m: f'A {m.group(1)} {m.group(2)}',
            result,
            flags=re.IGNORECASE
        )

        # 5. Факториалы
        result = re.sub(r'\b(\d+)\s*двойной факториал\b', r'\1!!', result, flags=re.IGNORECASE)
        result = re.sub(r'\b(\w+)\s*факториал\b', r'\1!', result, flags=re.IGNORECASE)

        # 6. Числительные
        numerals = self.loader.get_numerals()
        all_words = [(word, number) for number, words in numerals.items() for word in words]
        all_words.sort(key=lambda x: len(x[0]), reverse=True)
        for word, number in all_words:
            result = re.sub(r'\b' + re.escape(word) + r'\b', number, result, flags=re.IGNORECASE)

        # 7. Замена "всё/все" на " all " (ДО all-группировки)
        result = re.sub(r'\bвсё\b', ' all ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bвсе\b', ' all ', result, flags=re.IGNORECASE)

        # 8. Обработка all для группировки (ДО степеней)
        result = self._handle_all(result)

        # 9. Степени (ПОСЛЕ all-группировки, ДО замены "в" на "v")
        result = self._handle_power(result)

        # 10. Корни
        result = self._handle_sqrt(result)

        # 11. Базовые замены
        result = re.sub(r'\bделить на\b', ' / ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bде\b', ' d ', result, flags=re.IGNORECASE)

        # 12. Удаление предлогов (НЕ "в"!)
        for pred in ['от', 'из', 'на', 'до']:
            result = re.sub(r'\b' + pred + r'\b', ' ', result, flags=re.IGNORECASE)

        # 13. Обработка скобок
        result = re.sub(r'\bоткрывающая скобка\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрывающая скобка\b', ' ) ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bоткрыть\b', ' ( ', result, flags=re.IGNORECASE)
        result = re.sub(r'\bзакрыть\b', ' ) ', result, flags=re.IGNORECASE)

        # Неявные скобки через слово "скобка"
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

        # 14. Замена "в" на "v" (ТОЛЬКО ПОСЛЕ степеней)
        result = re.sub(r'\bв\b', ' v ', result, flags=re.IGNORECASE)

        # 15. Замена синонимов по словарю (длинные первыми)
        sorted_synonyms = sorted(self._reverse_map.keys(), key=len, reverse=True)

        for synonym in sorted_synonyms:
            target = self._reverse_map[synonym]

            # Пропускаем уже обработанные слова
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

        # 16. Очистка пробелов
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
        ("а плюс б все в степени эн", "(a + b)^{n}"),
        ("а плюс б все в эн", "(a + b)^{n}"),
        ("десять в минус пятой", "10^{-5}"),
        ("а в степени эн", "a^{n}"),
        ("икс в степени ка плюс 1", "x^{k + 1}"),
    ]

    print("Тесты нормализатора:")
    print("=" * 60)

    for test_input, expected in test_cases:
        result = normalizer.normalize(test_input)
        status = "✓" if result == expected else "✗"
        print(f"{status} {test_input!r} -> {result!r}")
        if result != expected:
            print(f"  Expected: {expected!r}")


if __name__ == "__main__":
    main()
