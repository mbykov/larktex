from lark import Transformer, Token

class MathToLatex(Transformer):
    def _clean(self, item):
        if isinstance(item, list):
            item = item[0] if item else ""
        return str(item.value) if isinstance(item, Token) else str(item)

    def add(self, items): return f"{self._clean(items[0])} + {self._clean(items[1])}"
    def sub(self, items): return f"{self._clean(items[0])} - {self._clean(items[1])}"
    def eq(self, items):  return f"{self._clean(items[0])} = {self._clean(items[1])}"
    def mul(self, items): return f"{self._clean(items[0])}{self._clean(items[1])}"

    def simple_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[1])}}}"

    def complex_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[1])}}}"

    def sqrt(self, items): return f"\\sqrt{{{self._clean(items[0])}}}"
    def sin(self, items):  return f"\\sin({self._clean(items[0])})"

    def integral_full(self, items):
        return f"\\int_{{{self._clean(items[0])}}}^{{{self._clean(items[1])}}} {self._clean(items[2])} \\, dx"

    def pow_2(self, items): return f"{self._clean(items[0])}^2"

    def simple_var(self, items):
        val = self._clean(items[0])
        # Если это греческая буква, добавляем слэш
        if val in ["alpha", "beta", "gamma", "pi"]:
            return f"\\{val}"
        return val

    def var(self, items): return self._clean(items[0])
    def num(self, items): return self._clean(items[0])
    def dx(self, _): return "dx"
    def dy(self, _): return "dy"
    def dz(self, _): return "dz"

    def __default__(self, data, children, meta):
        return children
