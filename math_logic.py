from lark import Transformer, Token

class MathToLatex(Transformer):
    def __init__(self, symbols_db):
        self.symbols_db = symbols_db

    #
    def _clean(self, item):
      """Рекурсивно достает чистую строку из любых вложенных списков Lark."""
      if isinstance(item, list):
        if len(item) == 1:
            return self._clean(item[0])
        # Если список из нескольких элементов, склеиваем
        cleaned = [self._clean(i) for i in item]
        return "".join([c for c in cleaned if c is not None])
      if isinstance(item, Token):
        val = str(item.value)
        # Игнорируем служебные токены
        if val in ["OT", "DO", "IZ", "PO", "SUM", "VSE", "INT", "DE"]:
            return ""
        return val
      if item is None:
        return ""
      return str(item)

    #
    def integral_full(self, items):
      args = []
      var = "x"

      for i, item in enumerate(items):
        if isinstance(item, Token):
            token = str(item)
            if token in ["INT", "OT", "DO", "PO"]:
                continue
            if token == "DE":
                if i + 1 < len(items):
                    var = self._clean(items[i + 1])
                continue
        cleaned = self._clean(item)
        if cleaned and cleaned != "None":
            args.append(cleaned)

      # Отладка
      # print(f"DEBUG integral_full: args={args}, var={var}")

      # Вариант 1: с пределами
      if len(args) >= 3:
        low = args[0]
        high = args[1]
        # Тело - всё, что после high, до var (но var уже отдельно)
        body_parts = args[2:]
        # Убираем var из конца, если он там есть
        if body_parts and body_parts[-1] == var:
            body_parts = body_parts[:-1]
        body = "".join(body_parts)
        return f"\\int_{{{low}}}^{{{high}}}{body}\\,d{var}"

      # Вариант 2: без пределов
      if len(args) >= 1:
        body_parts = args[:-1] if args[-1] == var else args
        body = "".join(body_parts)
        return f"\\int {body}\\,d{var}"

      return "Error: invalid integral"

    #
    def integral(self, items):
      """INT [OT] arith_expr [PO] DE var"""
      args = []
      var = "x"

      for i, item in enumerate(items):
        if isinstance(item, Token):
            token = str(item)
            if token in ["INT", "OT", "PO"]:
                continue
            if token == "DE":
                if i + 1 < len(items):
                    var = self._clean(items[i + 1])
                continue
        cleaned = self._clean(item)
        if cleaned and cleaned != "None":
            args.append(cleaned)

      body = "".join(args[:-1]) if args and args[-1] == var else "".join(args)
      return f"\\int {body}\\,d{var}"


    def complex_op(self, items):
        left = self._clean(items[0])
        op = self._clean(items[2])
        right = self._clean(items[3])

        if op == "DIV":
          return f"\\frac{{{left}}}{{{right}}}"

        if op == "SLASH":
          return f"({left}) / {right}"

        op_map = {
            "PLUS": " + ",
            "MINUS": " - ",
            "TIMES": " \\times ",
            "CDOT": "\\cdot ",
            "DIV": " \\div ",  # для "делить" без VSE
            "EQUAL": " = ",
            "NEQ": " \\neq ",
            "LT": " < ",
            "GT": " > ",
            "LE": " \\le ",
            "GE": " \\ge ",
            "PM": " \\pm ",
            "MP": " \\mp ",
            "SLASH": " / "
        }
        return f"{left}{op_map.get(op, op)}{right}"

    def simple_end(self, items):
        return self._clean(items[0])

    def eq(self, items): return f"{self._clean(items[0])} = {self._clean(items[2])}"
    def neq(self, items): return f"{self._clean(items[0])} \\neq {self._clean(items[2])}"
    def lt(self, items): return f"{self._clean(items[0])} < {self._clean(items[2])}"
    def le(self, items): return f"{self._clean(items[0])} \\le {self._clean(items[2])}"
    def gt(self, items): return f"{self._clean(items[0])} > {self._clean(items[2])}"

    def pm(self, items): return f"{self._clean(items[0])} \\pm {self._clean(items[2])}"
    def mp(self, items): return f"{self._clean(items[0])} \\mp {self._clean(items[2])}"

    def ge(self, items):
     return f"{self._clean(items[0])} \\ge {self._clean(items[2])}"

    def add(self, items): return f"{self._clean(items[0])} + {self._clean(items[2])}"
    def sub(self, items): return f"{self._clean(items[0])} - {self._clean(items[2])}"
    def implicit_mul(self, items): return f"{self._clean(items[0])}{self._clean(items[1])}"
    def times_mul(self, items): return f"{self._clean(items[0])} \\times {self._clean(items[2])}"
    def cdot_mul(self, items): return f"{self._clean(items[0])} \\cdot {self._clean(items[2])}"

    def simple_div(self, items): return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[2])}}}"

    def add_unary(self, items): return f" + {self._clean(items[1])}"
    def sub_unary(self, items): return f" - {self._clean(items[1])}"

    def sqrt(self, items): return f"\\sqrt{{{self._clean(items[-1])}}}"
    def sin(self, items): return f"\\sin({self._clean(items[-1])})"
    def cos(self, items): return f"\\cos({self._clean(items[-1])})"

    def pow_2(self, items): return f"{self._clean(items[0])}^2"
    def pow_3(self, items): return f"{self._clean(items[0])}^3"

    def derivative(self, items):
      """DE var PO DE var"""
      # items: [DE, y, PO, DE, x]
      numerator = self._clean(items[1])
      denominator = self._clean(items[4])
      return f"\\frac{{d{numerator}}}{{d{denominator}}}"

    def simple_var(self, items):
        val = self._clean(items)
        info = self.symbols_db.get(val)
        if info and info.get("type") == "greek":
            return f"\\{val}"
        return val


    def laplacian(self, items):
      return f"\\Delta {self._clean(items[0])}"

    def var(self, items): return self._clean(items)
    def num(self, items): return self._clean(items)
    def dx(self, _): return "dx"
    def dy(self, _): return "dy"
    def dz(self, _): return "dz"

    def __default__(self, data, children, meta):
        return children if len(children) == 1 else children
