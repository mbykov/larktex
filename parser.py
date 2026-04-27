#!/usr/bin/env python3
"""Parser — преобразует нормализованный текст в LaTeX с помощью Lark."""

import re
from pathlib import Path
from lark import Lark, Transformer


class LaTeXTransformer(Transformer):
    def start(self, c): return c[0] if c else ""
    def expr(self, c): return c[0] if c else ""

    def primary(self, c):
        if len(c) == 3 and str(c[0]) in ('LPAR', '('):
            return f"({c[1]})"
        if len(c) == 1:
            val = c[0]
            if isinstance(val, str): return val
            if hasattr(val, 'data'):
                return self._handle_tree(val)
            return val
        if len(c) == 2 and str(c[0]) in ('MINUS', '-', 'PLUS', '+'):
            op_token, val = c[0], c[1]
            if str(op_token) in ('MINUS', '-'):
                return f"-{val}"
            return f"+{val}"
        return c[0]

    def LPAR(self, _): return '('
    def RPAR(self, _): return ')'

    def multiplicative(self, c):
        if len(c) == 1: return c[0]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'MUL': result = f"{left}{right}"
        elif op_str == 'DIV': result = f"({left} / {right})"
        else: result = f"{left}"
        return result

    def additive(self, c):
        if len(c) == 1: return c[0]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'PLUS': result = f"({left} + {right})"
        elif op_str == 'MINUS': result = f"({left} - {right})"
        else: result = f"{left}"
        return result

    def multiplicative(self, c):
        if len(c) == 1: return c[0]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'MUL': result = f"{left}{right}"
        elif op_str == 'DIV': result = f"({left} / {right})"
        else: result = f"{left}"
        return result

    def power(self, c):
        if len(c) == 1: return c[0]
        base = c[0]
        exp = c[2]
        es = str(exp)
        return f"{base}^{es}" if len(es) == 1 else f"{base}^{{{es}}}"

    def all_expr(self, c):
        # all_expr: expr all → (expr)
        if c:
            return f"({c[0]})"
        return ""

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

    def _handle_tree(self, tree):
        data = getattr(tree, 'data', str(tree))
        
        # Обработка func_call: [sin_call] → передаём sin_call дальше
        if isinstance(data, str) and data == 'func_call':
            if tree.children:
                return self._handle_tree(tree.children[0])  # sin_call
            return ""
        
        # Обработка вызовов функций (sin_call, cos_call, exp_call и т.д.)
        if isinstance(data, str) and data.endswith('_call'):
            func_name = data.replace('_call', '')
            if tree.children:
                arg_tree = tree.children[0]  # exp_arg
                arg = self._child_to_str(arg_tree)
            else:
                arg = ""
            
            if func_name == 'exp':
                return f"\\exp({arg})"
            elif func_name == 'sqrt':
                return f"\\sqrt{{{arg}}}"
            else:
                return f"\\{func_name}({arg})"
        
        # Обработка аргументов функций (exp_arg, sin_arg и т.д.)
        # exp_arg: exp LPAR expr RPAR | exp VAR | exp GREEK
        # children: [exp, LPAR, expr, RPAR] (len=4) или [exp, VAR] (len=2) или [exp, GREEK] (len=2)
        if isinstance(data, str) and data.endswith('_arg'):
            if tree.children and len(tree.children) > 1:
                if len(tree.children) == 4:  # LPAR expr RPAR
                    return self._child_to_str(tree.children[2])  # expr
                else:  # VAR или GREEK (len=2)
                    arg_child = tree.children[1]
                    # Проверка: это токен VAR или дерево GREEK?
                    if isinstance(arg_child, str):
                        return arg_child
                    if hasattr(arg_child, 'data'):
                        # Это может быть дерево с GREEK внутри
                        return self._child_to_str(arg_child)
                    return str(arg_child)
            return ""
        
        if isinstance(data, str) and data == 'limit_expr':
            # limit_expr: "lim" ("as")? VAR TENDS_TO limit_val limit_expr_tail
            # limit_expr_tail: ("of")? primary
            # children с "as": ["as", VARIABLE, "tends_to", limit_val_tree, limit_expr_tail_tree] = 5
            # children без "as": [VARIABLE, "tends_to", limit_val_tree, limit_expr_tail_tree] = 4
            if len(tree.children) == 5 and str(tree.children[0]) == 'as':
                var = self._child_to_str(tree.children[1])
                limit_val_tree = tree.children[3]
                tail_tree = tree.children[4]
            elif len(tree.children) == 4:
                var = self._child_to_str(tree.children[0])
                limit_val_tree = tree.children[2]
                tail_tree = tree.children[3]
            else:
                return f"\\lim_{{?}} ?"  # Ошибка в структуре
            
            # Получаем значение из limit_val_tree (это дерево limit_val с одним ребенком: NUMBER/VAR/GREEK/INF)
            if hasattr(limit_val_tree, 'data') and limit_val_tree.children:
                limit_val = self._child_to_str(limit_val_tree.children[0])
            else:
                limit_val = str(limit_val_tree)
            
            # limit_expr_tail: ("of")? primary
            if hasattr(tail_tree, 'data') and tail_tree.data == 'limit_expr_tail':
                if len(tail_tree.children) == 1:
                    body = tail_tree.children[0]  # primary
                else:
                    body = tail_tree.children[1]  # "of", primary
            else:
                body = tail_tree
            
            expr = self._child_to_str(body) if body else ""
            return f"\\lim_{{{var} \\to {limit_val}}} {expr}"
        
        if isinstance(data, str):
            return data
        return str(tree)

    def _child_to_str(self, child):
        if isinstance(child, str):
            return child
        if hasattr(child, 'data'):
            return self._handle_tree(child)
        return str(child)

    def integral(self, c):
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
            elif hasattr(c[i], 'data') and c[i].data == 'integral_body':
                # integral_body: primary ("d" VAR)?
                body = c[i]
                if len(body.children) >= 1:
                    expr = self._child_to_str(body.children[0])
                if len(body.children) >= 2:
                    # [primary, VAR] или [primary, "d", VAR]
                    if str(body.children[1]) == 'd' and len(body.children) >= 3:
                        diff = f"d {self._child_to_str(body.children[2])}"
                    elif len(body.children) == 2:  # [primary, VAR] без "d"
                        diff = f"d {self._child_to_str(body.children[1])}"
                i += 1
            elif str(c[i]) in ('INTEGRAL',):
                i += 1
            else:
                expr = self._child_to_str(c[i])
                i += 1
        res = "\\int" + (f"_{lower}^{upper}" if lower or upper else "") + f" {expr}"
        return f"{res} \\, {diff}" if diff else res

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

    def parse(self, text: str) -> str:
        # Обработка "all" через post-processing
        if ' all ' in text:
            text = self._balance_all(text)
        parsed = str(self.parser.parse(text)).strip()
        return parsed

    def _balance_all(self, text: str) -> str:
        """Заменяет 'expr all' на '(expr)'."""
        result = text
        while ' all ' in result:
            idx = result.find(' all ')
            # Идём влево от 'all', собираем выражение до оператора или начала строки
            start = idx
            depth = 0
            
            # Идём влево, пока не найдём оператор на уровне 0 или начало строки
            while start > 0:
                ch = result[start - 1]
                if ch == ')':
                    depth += 1
                    start -= 1
                elif ch == '(':
                    depth -= 1
                    start -= 1
                elif depth == 0 and ch in '+-*/':
                    # Нашли оператор — выражение начинается после него
                    # Но нужно включить и сам оператор в скобки
                    start -= 1  # включаем оператор
                    # Теперь идём дальше влево до следующего оператора или начала
                    while start > 0:
                        ch2 = result[start - 1]
                        if ch2 == ')':
                            depth += 1
                            start -= 1
                        elif ch2 == '(':
                            depth -= 1
                            start -= 1
                        elif depth == 0 and ch2 in '+-*/':
                            start -= 1  # включаем этот оператор
                            break
                        else:
                            start -= 1
                    break
                elif result[start - 1] == ' ':
                    start -= 1
                else:
                    start -= 1
            
            # Добавляем скобки и удаляем ' all'
            expr = result[start:idx].strip()
            result = result[:start] + '(' + expr + ')' + result[idx+5:]
            # Рекурсивно обрабатываем результат
            result = self._balance_all(result)
            break
        return result

    def parse(self, text: str) -> str:
        # Обработка "all" через post-processing
        if ' all ' in text:
            text = self._balance_all(text)
        parsed = str(self.parser.parse(text)).strip()
        return parsed


def main():
    p = Parser()
    tests = [
        "sin x", "cos x", "exp x", "sqrt x",
        "sin(x)", "x = y", "sqrt(a) + b", "x^2",
        "a + b * c", "x approx y", "sin(x + y)",
        "-x", "x + y * z", "a - b - c"
    ]
    for t in tests:
        try: print(f"{t!r} → {p.parse(t)!r}")
        except Exception as e: print(f"{t!r} → ERROR: {e}")


if __name__ == "__main__":
    main()