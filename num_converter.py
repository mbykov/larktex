import re
import logging

logger = logging.getLogger("NumConverter")

class NumConverter:
    def __init__(self, num_core):
        self.num_core = num_core


    def replace(self, text):
        """Заменяет словесные числа на цифры"""
        original = text
        words = text.split()
        normalized_words = []

        for word in words:
            word_lower = word.lower()

            # Прямое попадание
            if word_lower in self.num_core:
                # logger.debug(f"Direct match: '{word}' -> {self.num_core[word_lower]}")
                normalized_words.append(str(self.num_core[word_lower]))
                continue

            # Пробуем привести к именительному падежу
            word_normalized = self._normalize_case(word_lower)
            if word_normalized in self.num_core:
                # logger.debug(f"Normalized match: '{word}' -> '{word_normalized}' -> {self.num_core[word_normalized]}")
                normalized_words.append(str(self.num_core[word_normalized]))
                continue

            # Не число — оставляем как есть
            normalized_words.append(word)

        result = " ".join(normalized_words)
        if original != result:
            logger.info(f"Numeric transformation: '{original}' -> '{result}'")
        return result

    def _normalize_case(self, word):
        """Приводит падежную форму числа к именительному падежу (только для чисел)"""
        exceptions = {
            "двух": "два",
            "трёх": "три",
            "четырёх": "четыре",
            "ноля": "ноль",
            "пяти": "пять",
            "шести": "шесть",
            "семи": "семь",
            "восьми": "восемь",
            "девяти": "девять",
            "десяти": "десять",
            "ста": "сто",
            "тысячи": "тысяча"
        }

        if word in exceptions:
            return exceptions[word]

        # Родительный падеж на -и (пяти → пять)
        if word.endswith("и") and len(word) > 2:
            candidate = word[:-1]
            if candidate in self.num_core:
                return candidate

        # Родительный падеж на -я (ноля → ноль)
        if word.endswith("я") and len(word) > 2:
            candidate = word[:-1] + "ь"
            if candidate in self.num_core:
                return candidate

        return word
