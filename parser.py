#!/usr/bin/env python3
"""Parser — преобразует нормализованный текст в LaTeX с помощью Lark."""

import re
from pathlib import Path
from lark import Lark, Transformer


class LaTeXTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.funcs = {
            'sin': 'sin', 'cos': 'cos', 'tan': 'tan', 'cot': 'cot',
            'arcsin': 'arcsin', 'arccos': 'arccos', 'arctan': 'arctan',
            'sinh': 'sinh', 'cosh': 'cosh', 'tanh': 'tanh',
            'sqrt': 'sqrt', 'log': 'log', 'ln': 'ln',
        }

    def start(self, c): return c[0] if c else ""
    def expr(self, c): return c[0] if c else ""

    def primary(self, c):
        # LPAR expr RPAR -> (expr)
        if len(c) == 3 and str(c[0]) in ('LPAR', '('):
            # c[1] уже преобразован Transformer
            return f"({c[1]})"
        if len(c) == 1:
            val = c[0]
            if isinstance(val, str): return val
            if hasattr(val, 'data'):
                if val.data == 'func_call' and len(val.children) == 1:
                    inner = val.children[0]
                    if hasattr(inner, 'data') and inner.data.endswith('_call'):
                        return self._handle_tree(inner)
                return self._handle_tree(val)
            return val
        # Унарный плюс/минус
        if len(c) == 2 and str(c[0]) in ('MINUS', '-', 'PLUS', '+'):
            op_token, val = c[0], c[1]
            if str(op_token) in ('MINUS', '-'):
                return f"-{val}"
            return f"+{val}"
        return c[0]

    def LPAR(self, _): return '('
    def RPAR(self, _): return ')'

    def additive(self, c):
        if len(c) == 1: return c[0]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'PLUS': return f"{left} + {right}"
        if op_str == 'MINUS': return f"{left} - {right}"
        return left

    def multiplicative(self, c):
        if len(c) == 1: return c[0]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'MUL': return f"{left} \\cdot {right}"
        if op_str == 'DIV': return f"{left} / {right}"
        return left

    def power(self, c):
        if len(c) == 1: return c[0]
        # c = [primary, EXP, primary]
        base = c[0]
        exp = c[2]  # пропускаем EXP токен
        es = str(exp)
        return f"{base}^{es}" if len(es) == 1 else f"{base}^{{{es}}}"  

    def comparison(self, c):
        if len(c) == 1: return c[0]
        left, op_token, right = c[0], c[1], c[2]
        op_map = {
            'EQ': '=', 'NEQ': '\\neq', 'LT': '<', 'GT': '>',
            'LE': '\\leq', 'GE': '\\geq', 'SIMILAR': '\\sim',
            'APPROX': '\\approx', 'PROP': '\\propto', 'EQUIV': '\\equiv',
        }
        op = op_map.get(str(op_token), str(op_token))
        return f"{left} {op} {right}"

    def primary(self, c):
        # LPAR expr RPAR -> (expr)
        if len(c) == 3 and str(c[0]) in ('LPAR', '('):
            return f"({c[1]})"
        if len(c) == 1:
            val = c[0]
            if isinstance(val, str): return val
            if hasattr(val, 'data'):
                if val.data == 'func_call' and len(val.children) == 1:
                    inner = val.children[0]
                    if hasattr(inner, 'data') and inner.data.endswith('_call'):
                        return self._handle_tree(inner)
                return self._handle_tree(val)
            return val
        # Унарный плюс/минус
        if len(c) == 2 and str(c[0]) in ('MINUS', '-', 'PLUS', '+'):
            op_token, val = c[0], c[1]
            if str(op_token) in ('MINUS', '-'):
                return f"-{val}"
            return f"+{val}"
        return c[0]

    def LPAR(self, _): return '('
    def RPAR(self, _): return ')'

    def _handle_tree(self, tree):
        data = getattr(tree, 'data', str(tree))
        if isinstance(data, str) and data.endswith('_call'):
            fname = data.replace('_call', '')
            arg = tree.children[1] if len(tree.children) >= 2 else (tree.children[0] if tree.children else "")
            if fname == 'sqrt': return f"\\sqrt{{{arg}}}"
            return f"\\{fname}({arg})"
        elif isinstance(data, str) and data == 'all_expr':
            inner = tree.children[0] if tree.children else ""
            return f"({inner})"
        elif isinstance(data, str) and data == 'integral':
            return self._integral(tree.children)
        elif isinstance(data, str) and data == 'sum_expr':
            return self._sum(tree.children)
        elif isinstance(data, str) and data == 'product_expr':
            return self._product(tree.children)
        elif isinstance(data, str) and data == 'diff_expr':
            return f"d {tree.children[0]}" if tree.children else "d"
        elif isinstance(data, str):
            # Прямой токен (sin, cos, NUMBER и т.д.)
            return data
        return str(tree)

    def _integral(self, c):
        expr = lower = upper = diff = ""
        i = 0
        while i < len(c):
            s = str(c[i])
            if s == 'from':
                lower = self._child_to_str(c[i+1])
                i += 2
            elif s == 'to':
                upper = self._child_to_str(c[i+1])
                i += 2
            elif s == 'of':
                i += 1
            elif s == 'd':
                diff = f"d {self._child_to_str(c[i+1])}"
                i += 2
            elif str(c[i]) in ('INTEGRAL',):
                i += 1
            else:
                expr = self._child_to_str(c[i])
                i += 1
        res = "\\int" + (f"_{lower}^{upper}" if lower or upper else "") + f" {expr}"
        return f"{res} \\, {diff}" if diff else res

    def integral_body(self, c):
        """Обрабатывает integral_body: expr ('d' VARIABLE)?"""
        if len(c) == 1:
            return c[0]
        # c = [expr, D, VARIABLE]
        expr = self._child_to_str(c[0])
        var = self._child_to_str(c[2]) if len(c) > 2 else self._child_to_str(c[1])
        return f"{expr} \\, d {var}"

    def _child_to_str(self, child):
        """Преобразует child (строка или дерево) в LaTeX строку."""
        if isinstance(child, str):
            return child
        if hasattr(child, 'data'):
            return self._handle_tree(child)
        return str(child)

    def _sum(self, c):
        expr = lower = upper = ""; i = 1
        while i < len(c):
            s = str(c[i])
            if s == 'from': lower = c[i+1]; i += 2
            elif s == 'to': upper = c[i+1]; i += 2
            elif s == 'of': i += 1
            else: expr = c[i]; i += 1
        return "\\sum" + (f"_{lower}^{upper}" if lower or upper else "") + f" {expr}"

    def _product(self, c):
        expr = lower = upper = ""; i = 1
        while i < len(c):
            s = str(c[i])
            if s == 'from': lower = c[i+1]; i += 2
            elif s == 'to': upper = c[i+1]; i += 2
            elif s == 'of': i += 1
            else: expr = c[i]; i += 1
        return "\\prod" + (f"_{lower}^{upper}" if lower or upper else "") + f" {expr}"

    def func_call(self, c): return c[0] if c else ""
    def special(self, c): return c[0] if c else ""

    def NUMBER(self, n): return str(n)
    def VARIABLE(self, v): return str(v)
    def GREEK(self, g): return str(g)
    def PLUS(self, _): return "PLUS"
    def MINUS(self, _): return "MINUS"
    def MUL(self, _): return "MUL"
    def DIV(self, _): return "DIV"
    def EQ(self, _): return "EQ"
    def NEQ(self, _): return "NEQ"
    def LT(self, _): return "LT"
    def GT(self, _): return "GT"
    def LE(self, _): return "LE"
    def GE(self, _): return "GE"
    def SIMILAR(self, _): return "SIMILAR"
    def APPROX(self, _): return "APPROX"
    def PROP(self, _): return "PROP"
    def EQUIV(self, _): return "EQUIV"
    def EXP(self, _): return "EXP"
    def UNARY(self, t): return str(t)


def load_grammar():
    return open(Path(__file__).parent / "grammar.lark", encoding='utf-8').read()


class Parser:
    def __init__(self):
        self.parser = Lark(load_grammar(), parser='lalr', transformer=LaTeXTransformer())
        self.funcs = ['sin', 'cos', 'tan', 'cot', 'arcsin', 'arccos', 'arctan',
                      'sinh', 'cosh', 'tanh', 'sqrt', 'log', 'ln']

    def _add_parens(self, text):
        """Добавляет скобки к функциям, если их нет."""
        r = text
        for f in sorted(self.funcs, key=len, reverse=True):
            pattern = rf'\b{f}\s+([^\s(]+)'
            r = re.sub(pattern, rf'{f}(\1)', r, flags=re.IGNORECASE)
        return r

    def parse(self, text: str) -> str:
        return str(self.parser.parse(self._add_parens(text))).strip()


def main():
    p = Parser()
    tests = [
        "sin(x)", "x = y", "sqrt(a) + b", "x^2",
        "integral(sin(x)) d x", "integral from 0 to 1 of x d x",
        "sin(x^2)", "a + b * c", "x approx y", "sin(x + y)",
        "-x", "x + y * z", "a - b - c"
    ]
    for t in tests:
        try: print(f"{t!r} → {p.parse(t)!r}")
        except Exception as e: print(f"{t!r} → ERROR: {e}")


if __name__ == "__main__":
    main()