import re
import logging

logger = logging.getLogger("NumConverter")

class NumConverter:
    def __init__(self, num_core):
        self.num_core = num_core
        # Сортируем ключи по длине, чтобы "двадцать один" не превратилось в "20 1"
        self.sorted_keys = sorted(num_core.keys(), key=len, reverse=True)

    def replace(self, text):
        original = text
        for word in self.sorted_keys:
            val = str(self.num_core[word])
            # Используем границы слов \b для точной замены
            pattern = r'\b' + re.escape(word) + r'\b'
            new_text = re.sub(pattern, val, text, flags=re.IGNORECASE)
            if new_text != text:
                logger.debug(f"Converted: '{word}' -> '{val}'")
                text = new_text

        if original != text:
            logger.info(f"Numeric Transformation: '{original}' -> '{text}'")
        return text
