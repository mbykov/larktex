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
            return str(item.value)
        return str(item)

    def eq(self, items): return f"{self._clean(items[0])} = {self._clean(items[2])}"
    def lt(self, items): return f"{self._clean(items[0])} < {self._clean(items[2])}"
    def le(self, items): return f"{self._clean(items[0])} \\le {self._clean(items[2])}"
    def gt(self, items): return f"{self._clean(items[0])} > {self._clean(items[2])}"

    def complex_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[2])}}}"

    def add(self, items): return f"{self._clean(items[0])} + {self._clean(items[2])}"
    def sub(self, items): return f"{self._clean(items[0])} - {self._clean(items[2])}"

    def mul(self, items): return f"{self._clean(items[0])}{self._clean(items[1])}"
    def star_mul(self, items): return f"{self._clean(items[0])} \\star {self._clean(items[2])}"
    def simple_div(self, items): return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[2])}}}"

    def add_unary(self, items): return f"+ {self._clean(items[1])}"
    def sub_unary(self, items): return f"- {self._clean(items[1])}"

    def sqrt(self, items): return f"\\sqrt{{{self._clean(items[-1])}}}"
    def sin(self, items): return f"\\sin({self._clean(items[-1])})"
    def cos(self, items): return f"\\cos({self._clean(items[-1])})"

    def pow_2(self, items): return f"{self._clean(items[0])}^2"
    def pow_3(self, items): return f"{self._clean(items[0])}^3"

    def integral_full(self, items):
        # items: [SUM, low, high, body]
        return f"\\int_{{{self._clean(items[1])}}}^{{{self._clean(items[2])}}} {self._clean(items[3])} \\, dx"

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
