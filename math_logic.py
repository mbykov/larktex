from lark import Transformer, Token

class MathToLatex(Transformer):
    def __init__(self, symbols_db):
        self.symbols_db = symbols_db

    def _clean(self, item):
        """Рекурсивно достает чистую строку из любых вложенных списков Lark."""
        if isinstance(item, list):
            if len(item) == 1:
                return self._clean(item[0])
            return "".join([self._clean(i) for i in item])
        if isinstance(item, Token):
            val = str(item.value)
            # Игнорируем служебные токены
            if val in ["OT", "DO", "IZ", "PO", "SUM", "VSE"]:
                return ""
            return val
        return str(item)

    #
    def integral_full(self, items):
      """INT [OT] base [DO] base [OT] arith_expr DE var"""
      args = []
      var = "x"  # по умолчанию

      for i, item in enumerate(items):
        if isinstance(item, Token):
            token = str(item)
            if token in ["INT", "OT", "DO", "PO"]:  # добавили PO
                continue
            if token == "DE":
                # Следующий элемент - переменная
                if i + 1 < len(items):
                    var = self._clean(items[i + 1])
                continue
        args.append(self._clean(item))

      if len(args) >= 3:
        low = args[0]
        high = args[1]
        body = args[2]
        return f"\\int_{{{low}}}^{{{high}}}{body}\\,d{var}"

      return "Error: invalid integral"


    def complex_op(self, items):
        left = self._clean(items[0])
        op = self._clean(items[2])
        right = self._clean(items[3])

        if op == "DIV":
            return f"\\frac{{{left}}}{{{right}}}"

        op_map = {
            "PLUS": "+",
            "MINUS": "-",
            "TIMES": "\\cdot",
            "EQUAL": "=",
            "LT": "<",
            "LE": "\\le",
            "GT": ">"
        }
        return f"{left}{op_map.get(op, op)}{right}"

    def simple_end(self, items):
        return self._clean(items[0])

    def eq(self, items): return f"{self._clean(items[0])}={self._clean(items[2])}"
    def lt(self, items): return f"{self._clean(items[0])}<{self._clean(items[2])}"
    def le(self, items): return f"{self._clean(items[0])}\\le{self._clean(items[2])}"
    def gt(self, items): return f"{self._clean(items[0])}>{self._clean(items[2])}"

    def add(self, items): return f"{self._clean(items[0])}+{self._clean(items[2])}"
    def sub(self, items): return f"{self._clean(items[0])}-{self._clean(items[2])}"
    def implicit_mul(self, items): return f"{self._clean(items[0])}{self._clean(items[1])}"
    def times_mul(self, items): return f"{self._clean(items[0])}\\cdot{self._clean(items[2])}"
    def simple_div(self, items): return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[2])}}}"

    def add_unary(self, items): return f"+{self._clean(items[1])}"
    def sub_unary(self, items): return f"-{self._clean(items[1])}"

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

    def var(self, items): return self._clean(items)
    def num(self, items): return self._clean(items)
    def dx(self, _): return "dx"
    def dy(self, _): return "dy"
    def dz(self, _): return "dz"

    def __default__(self, data, children, meta):
        return children if len(children) == 1 else children
