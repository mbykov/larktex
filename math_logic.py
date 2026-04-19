from lark import Transformer, Token, Tree

class MathToLatex(Transformer):
    GREEK = {
        "alpha": r"\alpha", "beta": r"\beta", "gamma": r"\gamma", "pi": r"\pi"
    }

    def _get_val(self, n):
        # If it's a list (from !rule), take the first element
        if isinstance(n, list):
            n = n[0]
        # If it's a Tree (because of nested rules), we need its first child
        if isinstance(n, Tree):
            n = n.children[0]
        # If it's a Token, return its string value
        return n.value if hasattr(n, 'value') else str(n)

    def simple_var(self, n):
        val = self._get_val(n)
        return self.GREEK.get(val, val)

    def var(self, n):
        # This rule acts as a passthrough for spec_var and simple_var
        return n[0]

    def num(self, n):
        return self._get_val(n)

    def dx(self, n): return "dx"
    def dy(self, n): return "dy"
    def dz(self, n): return "dz"

    def add(self, n): return f"{n[0]} + {n[2]}"
    def sub(self, n): return f"{n[0]} - {n[2]}"
    def eq(self, n):  return f"{n[0]} = {n[2]}"
    def mul(self, n): return f"{n[0]}{n[1]}"

    def simple_div(self, n): return rf"\frac{{{n[0]}}}{{{n[2]}}}"
    def complex_div(self, n): return rf"\frac{{{n[0]}}}{{{n[3]}}}"

    def pow_2(self, n): return f"{n[0]}^2"
    def pow_3(self, n): return f"{n[0]}^3"
    def complex_pow_2(self, n): return rf"({n[0]})^2"
    def complex_pow_3(self, n): return rf"({n[0]})^3"

    def sqrt(self, n): return rf"\sqrt{{{n[1]}}}"
    def sin(self, n): return rf"\sin({n[1]})"

    def integral(self, n):
        # [INT, base, DO, base, expr] -> indices 1, 3, 4
        return rf"\int_{{{n[1]}}}^{{{n[3]}}} {n[4]} \, dx"

    def start(self, n): return n[0]
    def UNKNOWN(self, n):
        # Возвращаем слово, обернутое в \text{} или выделенное звездами
        # return rf"\text{{[{n.value}]}}"
        return r"\color{red}{?}" # Или просто красный вопрос
