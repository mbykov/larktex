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

    def multiplicative(self, c):
        if len(c) == 1: return c[0]
        # c = [multiplicative, MUL/DIV, power, ALL_GROUP?]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'MUL': result = f"{left}{right}"  # Убираем \cdot
        elif op_str == 'DIV': result = f"({left} / {right})"
        else: result = f"{left}"
        return result

    def additive(self, c):
        if len(c) == 1: return c[0]
        # c = [additive, PLUS/MINUS, multiplicative, ALL_GROUP?]
        left, op, right = c[0], c[1], c[2]
        op_str = str(op)
        if op_str == 'PLUS': result = f"({left} + {right})"
        elif op_str == 'MINUS': result = f"({left} - {right})"
        else: result = f"{left}"
        return result

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
    def ALL_GROUP(self, _): return ')'  # "all" → закрывающая скобка

    def _handle_tree(self, tree):
        data = getattr(tree, 'data', str(tree))
        if isinstance(data, str) and data.endswith('_call'):
            fname = data.replace('_call', '')
            arg = tree.children[1] if len(tree.children) >= 2 else (tree.children[0] if tree.children else "")
            if fname == 'sqrt': return f"\\sqrt{{{arg}}}"
            return f"\\{fname}({arg})"
        elif isinstance(data, str) and data.endswith('_pow'):
            fname = data.replace('_pow', '')
            power = tree.children[1] if len(tree.children) >= 2 else tree.children[0]
            arg = tree.children[2] if len(tree.children) >= 3 else (tree.children[1] if len(tree.children) >= 2 else "")
            if fname == 'sqrt': return f"sqrt^{power}{{{arg}}}"
            return f"{fname}^{power} {arg}"
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

    def parse(self, text: str) -> str:
        # Проверяем, есть ли "all" в тексте
        if ' all ' in text:
            # Используем post-processing для "all"
            return self._balance_all(text)
        else:
            # Обычный парсинг
            parsed = str(self.parser.parse(self._add_parens(text))).strip()
            return parsed

    def _add_parens(self, text: str) -> str:
        """Добавляет скобки к функциям, если их нет."""
        r = text
        
        # Сначала обработать функции со степенью: "cos^2 \theta" -> "cos^2 \theta" (без скобок для греческих)
        for f in sorted(self.funcs, key=len, reverse=True):
            # Для греческих букв: cos^2 \theta -> cos^2 \theta (без скобок)
            pattern_greek = rf'\b{f}\^(\d+)\s+(\\[a-z]+)'
            def repl_greek(match):
                power = match.group(1)
                arg = match.group(2)
                return f'{f}^{power} {arg}'
            r = re.sub(pattern_greek, repl_greek, r, flags=re.IGNORECASE)
            
            # Для переменных: cos^2 x -> cos^2(x)
            pattern_var = rf'\b{f}\^(\d+)\s+([a-zA-Z0-9])'
            def repl_var(match):
                power = match.group(1)
                arg = match.group(2)
                return f'{f}^{power}({arg})'
            r = re.sub(pattern_var, repl_var, r, flags=re.IGNORECASE)
        
        # Затем обработать обычные функции: "cos x" -> "cos(x)"
        for f in sorted(self.funcs, key=len, reverse=True):
            # Для греческих букв: cos \theta -> cos \theta (без скобок)
            pattern_greek = rf'\b{f}\s+(\\[a-z]+)'
            def repl_greek(match):
                arg = match.group(1)
                return f'{f} {arg}'
            r = re.sub(pattern_greek, repl_greek, r, flags=re.IGNORECASE)
            
            # Для выражений с операторами: cos x + y -> cos(x + y)
            pattern_expr = rf'\b{f}\s+((?:(?![+\-*/^=<>!]).)+)'
            def repl(match):
                arg = match.group(1).strip()
                if arg.startswith('('):
                    return match.group(0)
                return f'{f}({arg})'
            r = re.sub(pattern_expr, repl, r, flags=re.IGNORECASE)
        
        # Добавить явное умножение между числом и греческой буквой/переменной: "2 \theta" -> "2*\theta"
        # Но не после функции со степенью: "cos^2 \theta" остаётся без *
        # Проверяем: число не должно быть после ^N
        r = re.sub(r'(\d)(?<!\^\d)\s+(\\[a-z]+)', r'\1*\2', r, flags=re.IGNORECASE)
        r = re.sub(r'(\d)(?<!\^\d)\s+([a-zA-Z0-9])', r'\1*\2', r, flags=re.IGNORECASE)
        
        return r

    def _balance_all(self, original: str) -> str:
        """
        Добавляет скобки для группировки "all".
        
        Правила:
        - Группируем последовательность: операнд [оператор операнд]*
        - Останавливаемся перед именем функции без оператора
        """
        import re
        
        funcs = {'sin', 'cos', 'tan', 'cot', 'arcsin', 'arccos', 'arctan',
                 'sinh', 'cosh', 'tanh', 'sqrt', 'log', 'ln', 'integral', 'sum', 'product'}
        
        result = original
        
        while ' all ' in result:
            idx = result.find(' all ')
            
            # Идём влево
            start = idx
            in_group = False
            
            while start > 0:
                ch = result[start-1]
                
                if ch in ' 	':
                    start -= 1
                elif ch in '+-*/':
                    start -= 1
                    in_group = True
                elif ch.isalnum() or ch in 'α-ωΑ-Ω':
                    # Читаем имя/число
                    end = start
                    while start > 0 and (result[start-1].isalnum() or result[start-1] in 'α-ωΑ-Ω'):
                        start -= 1
                    word = result[start:end]
                    
                    # Если это функция и нет оператора перед ней — стоп
                    if word.lower() in funcs and not in_group:
                        start = end  # Возвращаемся назад
                        break
                    
                    in_group = True
                else:
                    break
            
            # Добавляем скобки
            if in_group:
                result = result[:start] + '(' + result[start:idx].strip() + ')' + result[idx+5:]
            else:
                result = result[:idx] + result[idx+5:]
        
        # Парсим результат без "all"
        result = re.sub(r'\ball\b', '', result).strip()
        return str(self.parser.parse(self._add_parens(result))).strip()


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