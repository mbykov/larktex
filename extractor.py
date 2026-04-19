import json
import re
import os
from lark import Lark, UnexpectedEOF, UnexpectedToken
from math_logic import MathToLatex

class MathExtractor:
    def __init__(self, i18n_dir='i18n'):
        self.norm_map = {}
        # Safely read all JSON files
        if os.path.exists(i18n_dir):
            for filename in os.listdir(i18n_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(i18n_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # We iterate through the dictionary (categories)
                        for cat_name, cat_content in data.items():
                            if isinstance(cat_content, dict):
                                for key, aliases in cat_content.items():
                                    for alias in aliases:
                                        self.norm_map[alias.lower()] = key

        with open('math_grammar.lark', 'r', encoding='utf-8') as f:
            self.parser = Lark(f.read(), start='start')
        self.transformer = MathToLatex()

    def normalize(self, text):
        # Удаляем "в" перед "квадрате/кубе" и "на" в "умножить на" для простоты
        text = re.sub(r'\b(в|на|из|от|of|by)\b', '', text.lower())
        tokens = re.findall(r'[а-яёa-z0-9]+', text)
        normalized = []
        for t in tokens:
            normalized.append(self.norm_map.get(t, t))
        return " ".join(normalized)

    def transform(self, text):
        norm_text = self.normalize(text)
        # Отладочный принт, чтобы видеть, что уходит в Lark
        # print(f"DEBUG: {norm_text}")
        for i in range(6):
            try:
                current_text = norm_text + (" VSE" * i)
                tree = self.parser.parse(current_text)
                return self.transformer.transform(tree)
            except (UnexpectedEOF, UnexpectedToken):
                continue
            except Exception as e:
                return f"Error: {e}"
        return "Error: Cannot parse"
