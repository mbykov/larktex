import os, json, re, logging
from lark import Lark, UnexpectedEOF, UnexpectedToken
from math_logic import MathToLatex
from num_converter import NumConverter

logger = logging.getLogger("Extractor")
# logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

class MathExtractor:
    def __init__(self, i18n_dir='i18n'):
        self.norm_map = {}
        self.bridges = set()
        self.ignore_words = set()  # Инициализируем здесь
        self.combined_num_core = {}

        self._load_i18n(i18n_dir)
        self._validate_dictionaries()
        #
        if os.path.exists(i18n_dir):
            for filename in os.listdir(i18n_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(i18n_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for k, v in data.items():
                            if k == "NUM_CORE":
                                self.combined_num_core.update(v)
                            elif k == "BRIDGE":
                                self.bridges.update([b.lower() for b in v])
                            elif k == "IGNORE":
                                # Наполняем список игнорируемых слов
                                self.ignore_words.update([w.lower() for w in v])
                            elif isinstance(v, dict):
                                for key, aliases in v.items():
                                    for a in aliases: self.norm_map[a.lower()] = key
        # ... остальной код (парсер, конвертер)

        self.num_converter = NumConverter(self.combined_num_core)
        with open('math_grammar.lark', 'r', encoding='utf-8') as f:
            self.parser = Lark(f.read(), start='start')
        self.transformer = MathToLatex()

    #
    def _validate_dictionaries(self):
        required = {
            'PLUS', 'MINUS', 'EQUAL', 'DIV', 'SQRT', 'SIN', 'SUM',
            'VSE', 'OT', 'DO', 'IZ', 'PO'
        }

        # Собираем всё, что у нас есть, и приводим к ВЕРХНЕМУ регистру
        actual = {val.upper() for val in self.norm_map.values()}
        actual.update({b.upper() for b in self.bridges})

        missing = required - actual
        if missing:
            error_msg = f"CRITICAL ERROR: Missing i18n aliases for tokens: {missing}"
            # Для отладки:
            print(f"Actually loaded tokens: {actual}")
            raise ValueError(error_msg)


    #
    def _load_i18n(self, i18n_dir):
        # 1. Проверяем, где мы находимся
        cwd = os.getcwd()
        # print(f"DEBUG: Current Working Directory: {cwd}")

        full_path = os.path.abspath(i18n_dir)
        # print(f"DEBUG: Looking for folder: {full_path}")

        if not os.path.exists(full_path):
            print(f"DEBUG: FOLDER NOT FOUND!")
            # Посмотрим, что вообще есть в корне
            # print(f"DEBUG: Contents of {cwd}: {os.listdir(cwd)}")
            return

        files = os.listdir(full_path)
        # print(f"DEBUG: Files in i18n: {files}")

        for filename in files:
            if filename.endswith('.json'):
                path = os.path.join(full_path, filename)
                # print(f"DEBUG: Opening file: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                        # print(f"DEBUG: File size: {len(content)} characters")
                        data = json.loads(content)

                        def walk(d):
                            for k, v in d.items():
                                if k == "NUM_CORE": self.combined_num_core.update(v)
                                elif k == "BRIDGE": self.bridges.update([b.lower() for b in v])
                                elif k == "IGNORE": self.ignore_words.update([w.lower() for w in v])
                                elif isinstance(v, dict):
                                    walk(v)
                                elif isinstance(v, list):
                                    for alias in v:
                                        self.norm_map[alias.lower()] = k
                                        # print(f"DEBUG: Mapped {alias} -> {k}")
                        walk(data)
                    except Exception as e:
                        print(f"DEBUG: JSON ERROR in {filename}: {e}")

        # print(f"DEBUG: Final norm_map size: {len(self.norm_map)}")

    #
    def is_math_word(self, word):
      clean = re.sub(r'[^а-яёa-z0-9]', '', word.lower())
      # Добавь "не" и "превышает" сюда
      extra_math = ["в", "на", "квадрате", "кубе", "всё", "vse", "не", "превышает"]
      return (clean in self.norm_map or
            clean.isdigit() or
            clean in self.bridges or
            clean in extra_math or
            clean in self.ignore_words)

    def transform_text(self, text):
        logger.info(f"--- Processing: '{text}' ---")

        # 1. Числа
        processed_text = self.num_converter.replace(text)
        words = processed_text.split()

        # 2. Острова
        segments = []
        current = []
        for w in words:
            if self.is_math_word(w): current.append(w)
            else:
                if current: segments.append(('math', " ".join(current)))
                segments.append(('text', w))
                current = []
        if current: segments.append(('math', " ".join(current)))

        # 3. Трансформация
        result = []
        for stype, val in segments:
            if stype == 'math':
                latex = self.parse_island(val)
                if "Error" not in latex:
                    result.append(f"${latex}$")
                else:
                    logger.warning(f"Failed to parse island: '{val}'")
                    result.append(val)
            else:
                result.append(val)

        return " ".join(result)

    #
    def parse_island(self, text):
        norm = self.normalize_island(text)

        # Проверка на пустой или слишком короткий остров после нормализации
        if not norm.strip() or norm in ["SIN", "PLUS", "SQRT"]: # и другие одиночки
            return "Error"

        for i in range(6):
            try:
                test_str = norm + (" VSE" * i)
                tree = self.parser.parse(test_str)
                return self.transformer.transform(tree)
            except Exception as e:
                if i == 0:
                    # Формируем красивый отчет об ошибке
                    print(f"\n[!] НЕВЕРНЫЙ ТЕКСТ ФОРМУЛЫ: '{text}'")
                    print(f"    Нормализовано как: '{norm}'")

                    # Если Lark может показать место ошибки (UnexpectedToken/UnexpectedCharacters)
                    if hasattr(e, 'get_context'):
                        print("    Ошибка здесь:")
                        print(e.get_context(test_str, span=10))
                    else:
                        print(f"    Детали: {str(e)[:100]}")
                continue
        return "Error"

    #
    def normalize_island(self, text):
        tokens = re.findall(r'[а-яёa-z0-9]+', text.lower())
        normalized = []
        i = 0
        while i < len(tokens):
            t = tokens[i]

            # Пропускаем стилистический шум
            if t in self.ignore_words:
                i += 1
                continue

            # Склейка фраз (например, "делить на")
            if t == "делить" and i+1 < len(tokens) and tokens[i+1] == "на":
                normalized.append("DIV"); i += 2; continue
            if t == "в" and i+1 < len(tokens) and tokens[i+1] == "квадрате":
                normalized.append("POW2"); i += 2; continue
            # В методе normalize_island класса MathExtractor:
            if t == "не" and i + 1 < len(tokens) and tokens[i+1] == "превышает":
              normalized.append("LE")
              i += 2
              continue

            if t.isdigit(): normalized.append(t)
            elif t in self.norm_map: normalized.append(self.norm_map[t])
            elif t in self.bridges: normalized.append(t.upper())
            i += 1
        return " ".join(normalized)
