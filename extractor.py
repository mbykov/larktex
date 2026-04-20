import os, json, re, logging
from lark import Lark
from math_logic import MathToLatex
from num_converter import NumConverter

class MathExtractor:
    def __init__(self, i18n_dir='i18n'):
        self.symbols_db = {}
        self.norm_map = {}
        self.bridges = set()
        self.ignore_words = set()
        self.num_data = {}

        self._load_all_i18n(i18n_dir)
        self.num_converter = NumConverter(self.num_data)
        self.parser = self._build_parser()
        self.transformer = MathToLatex(self.symbols_db)

    def _load_all_i18n(self, i18n_dir):
        full_path = os.path.abspath(i18n_dir)
        if not os.path.exists(full_path): return

        for filename in os.listdir(full_path):
            if not filename.endswith('.json'): continue
            with open(os.path.join(full_path, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.num_data.update(data.get("numbers", {}))

                # Загрузка символов
                for key, info in data.get("symbols", {}).items():
                    self.symbols_db[key] = info
                    for a in info["aliases"]:
                        self.norm_map[a.lower()] = key

                # Загрузка операторов
                for key, info in data.get("operators", {}).items():
                    for a in info["aliases"]:
                        self.norm_map[a.lower()] = key

                # Структурные слова
                struct = data.get("structural", {})
                # If BRIDGE is a dict: "IZ": ["из"]
                bridge_data = struct.get("BRIDGE", {})
                if isinstance(bridge_data, dict):
                    for b_key, aliases in bridge_data.items():
                        for a in aliases:
                            self.norm_map[a.lower()] = b_key
                            self.bridges.add(a.lower())


    def _build_parser(self):
        greek = [f'"{k}"' for k, v in self.symbols_db.items() if v.get("type") == "greek"]
        latin = [f'"{k}"' for k, v in self.symbols_db.items() if v.get("type") == "latin"]

        g_str = " | ".join(greek) if greek else '"EMPTY_GREEK"'
        l_str = " | ".join(latin) if latin else '"EMPTY_LATIN"'

        with open('math_grammar.lark', 'r', encoding='utf-8') as f:
            template = f.read()

        grammar = template.replace("{GREEK_LIST}", g_str).replace("{LATIN_LIST}", l_str)
        return Lark(grammar, start='start')

    #
    def is_math_word(self, word):
        clean = re.sub(r'[^а-яёa-z0-9]', '', word.lower())
        # Add common bridge words manually if they aren't recognized yet
        extra = ["в", "на", "из", "от", "до", "по", "не", "превышает"]
        return (clean in self.norm_map or
                clean.isdigit() or
                clean in self.bridges or
                clean in self.ignore_words or
                clean in extra)

    #
    def normalize_island(self, text):
      tokens = re.findall(r'[а-яёa-z0-9]+', text.lower())
      res = []
      i = 0
      while i < len(tokens):
        t = tokens[i]
        if t in self.ignore_words:
          i += 1; continue

        # Сначала проверяем сложные склейки... (не превышает и т.д.)

        if t.isdigit():
          res.append(t)
        elif t in self.norm_map:
          # Теперь "из" найдет в norm_map ключ "IZ"
          res.append(self.norm_map[t])
        i += 1
      return " ".join(res)

    def transform_text(self, text):
        text = self.num_converter.replace(text)
        words = text.split()
        segments, current = [], []

        for w in words:
            if self.is_math_word(w): current.append(w)
            else:
                if current: segments.append(('math', " ".join(current)))
                segments.append(('text', w))
                current = []
        if current: segments.append(('math', " ".join(current)))

        result = []
        for stype, val in segments:
            if stype == 'math':
                latex = self.parse_island(val)
                result.append(f"${latex}$" if "Error" not in latex else val)
            else: result.append(val)
        return " ".join(result)

    def parse_island(self, text):
        norm = self.normalize_island(text)
        for i in range(6):
            try:
                tree = self.parser.parse(norm + (" VSE" * i))
                return self.transformer.transform(tree)
            except: continue
        return "Error"
