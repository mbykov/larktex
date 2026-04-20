import re

class NumConverter:
    def __init__(self, num_core_data):  # Проверьте имя здесь
        self.config = num_core_data     # И здесь
        self.bases = self.config.get("bases", {})
        self.teens = self.config.get("teens", {})
        self.suffixes = self.config.get("suffixes", {})
        self.multipliers = self.config.get("multipliers", {})

    #
    def _parse_word(self, word):
        word = word.lower()
        # 1. Сначала проверяем 11-19
        for t_word, val in self.teens.items():
            if t_word in word: return val

        # 2. Ищем множители (тысяча и т.д.)
        for m_root, m_val in self.multipliers.items():
            if m_root in word: return m_val

        # 3. Ищем базу и суффикс (пять + десят)
        base_val = 0
        # Сортируем ключи по длине, чтобы "девяност" было раньше "девят"
        sorted_bases = sorted(self.bases.items(), key=lambda x: len(x[0]), reverse=True)
        for b_root, b_val in sorted_bases:
            if b_root in word:
                # Проверяем, нет ли в этом же слове суффикса (десят/сот)
                for s_root, s_val in self.suffixes.items():
                    if s_root in word and s_root != b_root:
                        return b_val * s_val
                return b_val
        return None


    def replace(self, text):
        """Находит цепочки слов-чисел и заменяет их на итоговую цифру."""
        words = re.findall(r'[а-яёA-Za-z0-9]+', text.lower())
        new_tokens = []

        total = 0
        current_block = 0 # Накопитель для группы (например, "двести пятьдесят")
        in_number = False

        for word in words:
            val = self._parse_word(word)

            if val is not None:
                in_number = True
                # Если это множитель уровня тысячи/миллиона
                if val >= 1000:
                    if current_block == 0: current_block = 1
                    total += current_block * val
                    current_block = 0
                else:
                    # Если текущее слово меньше предыдущего (сто пять) - складываем
                    # Если больше (пять десять - оговорка) - тоже стараемся обработать
                    current_block += val
            else:
                # Если число закончилось
                if in_number:
                    new_tokens.append(str(total + current_block))
                    total = 0
                    current_block = 0
                    in_number = False
                new_tokens.append(word)

        # Если текст закончился числом
        if in_number:
            new_tokens.append(str(total + current_block))

        return " ".join(new_tokens)

# Пример использования для теста:
# conv = NumConverter(ru_i18n)
# print(conv.replace("интеграл от пятисот двадцати трех"))
# -> "интеграл от 523"
