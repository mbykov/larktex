import logging
from lark import Transformer, Token

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger("MathLogic")

def debug_rule(expected_count=None):
    """Decorator to verify what Lark passes to the transformer"""
    def decorator(func):
        def wrapper(self, items):
            if expected_count is not None and len(items) != expected_count:
                logger.debug(f"!!! Rule '{func.__name__}' got {len(items)} items: {items}")
            else:
                logger.debug(f"Rule '{func.__name__}' items: {items}")
            return func(self, items)
        return wrapper
    return decorator

class MathToLatex(Transformer):
    def __init__(self, symbols_db):
        self.symbols_db = symbols_db

    def _clean(self, item):
        """Recursively extracts string values from Lark Tokens/Lists"""
        if isinstance(item, list):
            return self._clean(item[0]) if item else ""
        if isinstance(item, Token):
            return str(item.value)
        return str(item)

    # --- Comparisons (3 items: left, OP, right) ---
    @debug_rule(expected_count=3)
    def eq(self, items): return f"{self._clean(items[0])} = {self._clean(items[2])}"

    @debug_rule(expected_count=3)
    def lt(self, items): return f"{self._clean(items[0])} < {self._clean(items[2])}"

    @debug_rule(expected_count=3)
    def le(self, items): return f"{self._clean(items[0])} \\le {self._clean(items[2])}"

    @debug_rule(expected_count=3)
    def gt(self, items): return f"{self._clean(items[0])} > {self._clean(items[2])}"

    # --- Arithmetic (3 items: left, OP, right) ---
    @debug_rule(expected_count=3)
    def add(self, items): return f"{self._clean(items[0])} + {self._clean(items[2])}"

    @debug_rule(expected_count=3)
    def sub(self, items): return f"{self._clean(items[0])} - {self._clean(items[2])}"

    # --- Multiplication & Division ---
    @debug_rule(expected_count=2) # term factor -> mul
    def mul(self, items): return f"{self._clean(items[0])}{self._clean(items[1])}"

    @debug_rule(expected_count=3) # term STAR factor
    def star_mul(self, items): return f"{self._clean(items[0])} \\star {self._clean(items[2])}"

    @debug_rule(expected_count=3) # term DIV/PO factor
    def simple_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[2])}}}"

    @debug_rule(expected_count=4) # arith_expr VSE DIV factor
    def complex_div(self, items):
        return f"\\frac{{{self._clean(items[0])}}}{{{self._clean(items[3])}}}"

    # --- Functions (2 items: OP, factor) ---
    @debug_rule(expected_count=2)
    def sqrt(self, items):
        # Берем самый последний элемент - это всегда будет само выражение
        content = self._clean(items[-1])
        return f"\\sqrt{{{content}}}"

    @debug_rule(expected_count=None)
    def sin(self, items):
        content = self._clean(items[-1])
        return f"\\sin({content})"

    @debug_rule(expected_count=None)
    def cos(self, items):
        content = self._clean(items[-1])
        return f"\\cos({content})"

    # --- Powers (2 items: base, OP) ---
    @debug_rule(expected_count=2)
    def pow_2(self, items): return f"{self._clean(items[0])}^2"

    @debug_rule(expected_count=2)
    def pow_3(self, items): return f"{self._clean(items[0])}^3"

    # --- Integrals (4 items: SUM, low, high, body) ---
    @debug_rule(expected_count=4)
    def integral_full(self, items):
        return f"\\int_{{{self._clean(items[1])}}}^{{{self._clean(items[2])}}} {self._clean(items[3])} \\, dx"

    # --- Unary ---
    @debug_rule(expected_count=2)
    def add_unary(self, items): return f"+ {self._clean(items[1])}"

    @debug_rule(expected_count=2)
    def sub_unary(self, items): return f"- {self._clean(items[1])}"

    # --- Variables ---
    def simple_var(self, items):
        val = self._clean(items)
        # Dynamic check in symbols_db
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
