import os
import json
import re
import logging
from typing import Dict, Set, Any, List, Tuple, Union
import lark.exceptions
from lark import Lark, Tree
from math_logic import MathToLatex
from num_converter import NumConverter

logger = logging.getLogger("MathExtractor")

class MathExtractor:
    def __init__(self, i18n_dir: str = 'i18n', lang: str = 'ru') -> None:
        self.lang: str = lang
        self.symbols_db: Dict[str, Dict[str, Any]] = {}
        self.norm_map: Dict[str, str] = {}          # слово -> токен (для простых замен)
        self.composite_map: Dict[str, str] = {}     # фраза -> токен (для многословных операторов)
        self.bridges: Set[str] = set()
        self.ignore_words: Set[str] = set()
        self.vse_aliases: Set[str] = set()
        self.math_stopwords: Set[str] = set()
        self.noise_words: Set[str] = set()
        self.de_aliases: Set[str] = set()     # алиасы для "де", "дэ"
        self.num_data: Dict[str, str] = {}      # слово -> цифра (например, "ноль" -> "0")

        self._load_language_data(i18n_dir, lang)
        self.num_converter: NumConverter = NumConverter(self.num_data)
        self.parser: Lark = self._build_parser()
        self.transformer: MathToLatex = MathToLatex(self.symbols_db)

    def _load_language_data(self, i18n_dir: str, lang: str) -> None:
        """Загружает данные конкретного языка из JSON файла"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, i18n_dir, f"{lang}.json")

        if not os.path.exists(full_path):
            logger.error(f"Language file {full_path} not found")
            return

        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Числа: "0": ["ноль", "ноля"] -> {"ноль": "0", "ноля": "0"}
        for digit, words in data.get("numbers", {}).items():
            for word in words:
                self.num_data[word.lower()] = digit

        # Символы (переменные)
        for key, info in data.get("symbols", {}).items():
            self.symbols_db[key] = info
            for alias in info.get("aliases", []):
                self.norm_map[alias.lower()] = key

        # Операторы (однословные)
        for key, info in data.get("operators", {}).items():
            for alias in info.get("aliases", []):
                self.norm_map[alias.lower()] = key

        # Составные операторы (многословные)
        for key, phrases in data.get("composite_operators", {}).items():
            for phrase in phrases:
                self.composite_map[phrase.lower()] = key

        # Структурные элементы
        struct = data.get("structural", {})

        # Мосты (предлоги: из, от, до, по, де)
        bridge_data = struct.get("BRIDGE", {})
        if isinstance(bridge_data, dict):
            for b_key, aliases in bridge_data.items():
                for alias in aliases:
                    self.norm_map[alias.lower()] = b_key
                    self.bridges.add(alias.lower())
                    # Специально для DE
                    if b_key == "DE":
                        self.de_aliases.add(alias.lower())

        # Игнорируемые слова (функция, переменная)
        self.ignore_words.update([w.lower() for w in struct.get("IGNORE", [])])

        # VSE (маркер конца выражения)
        self.vse_aliases.update([w.lower() for w in struct.get("VSE", [])])

        # Математические стоп-слова (всегда считаются математикой)
        self.math_stopwords.update([w.lower() for w in struct.get("MATH_STOPWORDS", [])])

        # Шумовые слова (удаляются препроцессором)
        self.noise_words.update(data.get("noise_words", []))

    def _build_parser(self) -> Lark:
        """Строит парсер Lark с динамической подстановкой словарей"""
        greek = [f'"{k}"' for k, v in self.symbols_db.items() if v.get("type") == "greek"]
        latin = [f'"{k}"' for k, v in self.symbols_db.items() if v.get("type") == "latin"]
        g_str = " | ".join(greek) if greek else '"EMPTY_GREEK"'
        l_str = " | ".join(latin) if latin else '"EMPTY_LATIN"'

        grammar_path = os.path.join(os.path.dirname(__file__), 'math_grammar.lark')
        with open(grammar_path, 'r', encoding='utf-8') as f:
            template = f.read()

        grammar = template.replace("{GREEK_LIST}", g_str).replace("{LATIN_LIST}", l_str)
        return Lark(grammar, start='start', parser='earley')

    def preprocess_text(self, text: str) -> str:
        """Удаляет стилевой шум (скобка, вот, так и т.д.)"""
        # text = text.lower()
        for noise in sorted(self.noise_words, key=len, reverse=True):
            pattern = r'\b' + re.escape(noise) + r'\b'
            text = re.sub(pattern, ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _is_number_word(self, word: str) -> bool:
        """Проверяет, является ли слово числом (в любом падеже)"""
        word_lower = word.lower()
        # Прямое попадание
        if word_lower in self.num_data:
            return True
        # Приводим к именительному падежу и проверяем
        normalized = self.num_converter._normalize_case(word_lower)
        return normalized in self.num_data

    def is_math_word(self, word: str) -> bool:
        """Проверяет, относится ли слово к математическому острову"""
        clean = word.lower()

        # Стоп-слова (проверяем ПЕРВЫМ — важнее bridges)
        if clean in self.math_stopwords:
            return True

        # Числа (в любом падеже)
        if self._is_number_word(clean):
            return True

        # Цифры
        if clean.isdigit():
            return True

        # VSE
        if clean in self.vse_aliases:
            return True

        # Игнорируемые слова
        if clean in self.ignore_words:
            return True

        # DE алиасы (для производных)
        if clean in self.de_aliases:
            return True

        # Из словаря нормализации (но НЕ мосты, кроме DE)
        if clean in self.norm_map:
            if clean in self.bridges and clean not in self.de_aliases:
                return False
            return True

        # Мосты (кроме DE) не считаются математикой сами по себе
        if clean in self.bridges and clean not in self.de_aliases:
            return False

        return False

    def normalize_island(self, text: str) -> str:
        """Преобразует текст математического острова в последовательность токенов"""
        logger.debug(f"normalize_island INPUT: '{text}'")

        # 1. Заменяем составные операторы (многословные фразы)
        for phrase, token in sorted(self.composite_map.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(phrase, token)

        # 2. Конвертируем числа
        text = self.num_converter.replace(text)

        # 3. Убираем стилевой шум
        text = self.preprocess_text(text)

        # 4. Разбиваем на токены
        tokens = text.split()
        logger.debug(f"Tokens: {tokens}")

        res: List[str] = []
        i = 0
        while i < len(tokens):
            word = tokens[i]

            # VSE
            if word in self.vse_aliases:
                res.append("VSE")
                i += 1
                continue

            # DE + переменная (де икс, де игрек)
            if word in self.de_aliases and i + 1 < len(tokens):
                next_word = tokens[i + 1]
                if next_word in self.norm_map:
                    res.append("DE")
                    res.append(self.norm_map[next_word])
                    i += 2
                    continue

            # Игнорируемые слова пропускаем
            if word in self.ignore_words:
                i += 1
                continue

            # Нормализация слова
            if word in self.norm_map:
                res.append(self.norm_map[word])
            elif word.isdigit():
                res.append(word)
            elif word in self.num_data:
                res.append(self.num_data[word])
            else:
                res.append(word)

            i += 1

        result = " ".join(res)
        logger.debug(f"normalize_island OUTPUT: '{result}'")
        return result

    def parse_island(self, text: str) -> Union[str, List[str]]:
        """Парсит нормализованный остров в LaTeX"""
        norm = self.normalize_island(text)
        logger.debug(f"Normalized: {norm}")
        logger.debug(f"Norm repr: {repr(norm)}")

        # Пробуем спарсить без добавления VSE
        try:
            logger.debug(f"Trying without VSE: '{norm}'")
            tree = self.parser.parse(norm)
            res = self.transformer.transform(tree)
            while isinstance(res, list):
                if len(res) == 1:
                    res = res[0]
                else:
                    res = "".join([str(x) for x in res])
            return res
        except (lark.exceptions.ParseError, AttributeError, IndexError) as exc:
            logger.debug(f"Failed without VSE: {exc}")
            pass

        # Если не получилось, пробуем с VSE в конце
        try:
            test_norm = norm + " VSE"
            logger.debug(f"Trying WITH VSE: '{test_norm}'")
            tree = self.parser.parse(test_norm)
            res = self.transformer.transform(tree)
            while isinstance(res, list):
                if len(res) == 1:
                    res = res[0]
                else:
                    res = "".join([str(x) for x in res])
            return res
        except (lark.exceptions.ParseError, AttributeError, IndexError) as exc:
            logger.error(f"Parse error: {exc}")
            return "Error"

    def transform_text(self, text: str) -> str:
        """Основной метод: сегментирует текст, парсит математические острова"""
        logger.debug(f"transform_text INPUT: '{text}'")

        # Конвертируем числа
        text = self.num_converter.replace(text)
        logger.debug(f"after num_converter: '{text}'")

        words = text.split()
        logger.debug(f"words: {words}")

        segments = []
        current = []

        for w in words:
            is_math = self.is_math_word(w)
            logger.debug(f"word: '{w}', is_math: {is_math}")
            if is_math:
                current.append(w)
            else:
                if current:
                    segments.append(('math', " ".join(current)))
                    current = []
                segments.append(('text', w))

        if current:
            segments.append(('math', " ".join(current)))

        logger.debug(f"segments: {segments}")
        # print(f"DEBUG segments: {segments}")

        result = []
        for seg_type, val in segments:
            if seg_type == 'math':
                logger.debug(f"processing math segment: '{val}'")
                latex = self.parse_island(val)
                if "Error" not in str(latex):
                    result.append(f"${latex}$")
                else:
                    result.append(val)
            else:
                result.append(val)

        final_result = " ".join(result)
        logger.debug(f"transform_text RESULT: '{final_result}'")
        return final_result
