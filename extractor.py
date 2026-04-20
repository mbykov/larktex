import os, json, re
from lark import Lark, UnexpectedEOF, UnexpectedToken
from math_logic import MathToLatex
from num_converter import NumConverter

class MathExtractor:
    def __init__(self, i18n_dir='i18n'):
        self.norm_map = {}
        self.bridges = set()
        self.combined_num_core = {}

        # Загрузка локализации
        if os.path.exists(i18n_dir):
            for filename in os.listdir(i18n_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(i18n_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for k, v in data.items():
                            if k == "NUM_CORE":
                                for sk, sv in v.items():
                                    if sk not in self.combined_num_core: self.combined_num_core[sk] = {}
                                    self.combined_num_core[sk].update(sv)
                            elif k == "BRIDGE":
                                self.bridges.update([b.lower() for b in v])
                            elif isinstance(v, dict):
                                for key, aliases in v.items():
                                    for a in aliases: self.norm_map[a.lower()] = key

        self.num_converter = NumConverter(self.combined_num_core)

        # Инициализация парсера
        with open('math_grammar.lark', 'r', encoding='utf-8') as f:
            self.parser = Lark(f.read(), start='start')
        self.transformer = MathToLatex()

    def is_math_word(self, word):
        """Определяет, относится ли слово к математическому острову."""
        clean = re.sub(r'[^а-яёa-z0-9]', '', word.lower())
        # Служебные слова, которые не должны рвать остров
        extra_math = ["в", "на", "квадрате", "кубе", "всё", "vse"]
        return (clean in self.norm_map or
                clean.isdigit() or
                clean in self.bridges or
                clean in extra_math)

    def transform_text(self, text):
        """Разбивает текст на острова и заменяет математику на LaTeX."""
        # Предварительная замена числительных ("один" -> "1")
        text = self.num_converter.replace(text)
        words = text.split()
        if not words: return ""

        segments = []
        current_island = []

        for word in words:
            if self.is_math_word(word):
                current_island.append(word)
            else:
                if current_island:
                    segments.append({'type': 'math', 'val': current_island})
                segments.append({'type': 'text', 'val': [word]})
                current_island = []
        if current_island:
            segments.append({'type': 'math', 'val': current_island})

        result = []
        for seg in segments:
            raw_str = " ".join(seg['val'])
            if seg['type'] == 'math':
                latex = self.parse_island(raw_str)
                # Если парсер вернул ошибку, оставляем текст как есть
                result.append(f"${latex}$" if "Error" not in latex else raw_str)
            else:
                result.append(raw_str)
        return " ".join(result)

    def parse_island(self, text):
        """Нормализует остров и скармливает его Lark."""
        norm = self.normalize_island(text)
        print(f"DEBUG SIN: '{norm}'") #
        # Попытки распарсить с разным количеством закрывающих "всё"
        for i in range(6):
            try:
                tree = self.parser.parse(norm + (" VSE" * i))
                return self.transformer.transform(tree)
            except (UnexpectedEOF, UnexpectedToken):
                continue
            #
            except Exception as e:
              print(f"LARK ERROR: {e}") # Это покажет, почему SIN падает
              break
            # except Exception:
            #     break
        return "Error"

    #
    def normalize_island(self, text):
        tokens = re.findall(r'[а-яёa-z0-9]+', text.lower())
        normalized = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            # Склейка фраз
            if t == "делить" and i + 1 < len(tokens) and tokens[i+1] == "на":
                normalized.append("DIV"); i += 2; continue
            if t == "в" and i + 1 < len(tokens) and tokens[i+1] == "квадрате":
                normalized.append("POW2"); i += 2; continue

            if t.isdigit():
                normalized.append(t)
            elif t in self.norm_map:
                normalized.append(self.norm_map[t])
            elif t in self.bridges:
                normalized.append(t.upper())
            i += 1
        return " ".join(normalized)
