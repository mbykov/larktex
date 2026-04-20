from lark import Transformer, Token

class MathToLatex(Transformer):
    def _clean(self, item):
        """Рекурсивно извлекает строку из токенов и списков Lark."""
        if isinstance(item, list):
            return self._clean(item[0]) if item else ""
        if isinstance(item, Token):
            return str(item.value)
        return str(item)

    # --- Уровень сравнений (2 аргумента) ---
    def lt(self, items):
        return f"{self._clean(items[0])} < {self._clean(items[1])}"

    def le(self, items):
        return f"{self._clean(items[0])} \\le {self._clean(items[1])}"

    def gt(self, items):
        return f"{self._clean(items[0])} > {self._clean(items[1])}"

    def eq(self, items):
        return f"{self._clean(items[0])} = {self._clean(items[1])}"

    # --- Уровень арифметики (2 аргумента) ---
    def add(self, items):
        return f"{self._clean(items[0])} + {self._clean(items[1])}"

    def sub(self, items):
        return f"{self._clean(items[0])} - {self._clean(items[1])}"

    def mul(self, items):
        # Умножение обычно пишется слитно в LaTeX (например, mc^2)
        return f"{self._clean(items[0])}{self._clean(items[1])}"

    def add_unary(self, items):
        return f"+ {self._clean(items[0])}"

    def sub_unary(self, items):
        return f"- {self._clean(items[0])}"

    # --- Уровень термов (деление) ---
    def simple_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[1])}}}"

    def complex_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[1])}}}"

    # --- Уровень факторов (функции и степени) ---
    def sqrt(self, items):
        return f"\\sqrt{{{self._clean(items[0])}}}"

    def sin(self, items):
        return f"\\sin({self._clean(items[0])})"

    def pow_2(self, items):
        return f"{self._clean(items[0])}^2"

    def pow_3(self, items):
        return f"{self._clean(items[0])}^3"

    def integral_full(self, items):
        # Ожидается: [low, high, body]
        return f"\\int_{{{self._clean(items[0])}}}^{{{self._clean(items[1])}}} {self._clean(items[2])} \\, dx"

    # --- Базовые элементы ---
    def simple_var(self, items):
        val = self._clean(items)
        # Список греческих букв, требующих обратный слэш
        greeks = [
            "alpha", "beta", "gamma", "pi", "omega", "upsilon",
            "chi", "eta", "theta", "phi", "Omega", "Lambda", "Delta"
        ]
        if val in greeks:
            return f"\\{val}"
        return val

    def var(self, items): return self._clean(items)
    def num(self, items): return self._clean(items)

    def dx(self, _): return "dx"
    def dy(self, _): return "dy"
    def dz(self, _): return "dz"

    def star_mul(self, items):
      return f"{self._clean(items[0])} \\star {self._clean(items[1])}"

    def cos(self, items):
      return f"\\cos({self._clean(items)})"

    def __default__(self, data, children, meta):
        # Если правило не определено явно, пробрасываем результат вверх
        return children[0] if len(children) == 1 else children
