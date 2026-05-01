#!/usr/bin/env python3
"""Parser - Lark -> AST with all support."""

import re
from pathlib import Path
from lark import Lark, Transformer, Token

from lib.ast_nodes import (
    ASTNode, NumberNode, VarNode, GreekNode, InfinityNode,
    UnaryOpNode, BinOpNode, RelationNode, ParensNode,
    FuncCallNode, PowNode, FracNode, FactorialNode, BinomNode,
    LimitNode, DerivNode, SecondDerivNode, PartialDerivNode,
    IntegralNode, SumNode, ProductNode, AllNode
)


def load_grammar():
    return open(Path(__file__).parent / "grammar.lark", encoding='utf-8').read()


class ASTBuilder(Transformer):
    """Lark Transformer -> AST."""
    #
    def curly_group(self, children):
      """Обработка фигурных скобок: {expr} -> expr (без узла скобок)"""
      if len(children) == 3:
        # ['{', expr, '}'] -> возвращаем expr
        return children[1]
      elif len(children) == 1:
        return children[0]
      return children[0] if children else None

    def CURLY_LEFT(self, t):
      return '{'

    def CURLY_RIGHT(self, t):
      return '}'

    def mult_seq(self, children):
      """Преобразует последовательность primary в цепочку умножений."""
      if len(children) == 1:
        return children[0]

      # Создаем цепочку BinOpNode('*', ...)
      result = children[0]
      for child in children[1:]:
        result = BinOpNode('*', result, child)

      return result

    def start(self, children):
        return children[0] if children else None

    def expr(self, children):
        return children[0] if children else None

    def comparison(self, children):
        if len(children) == 1:
            return children[0]
        left, op, right = children[0], children[1], children[2]
        return RelationNode(op=str(op), left=left, right=right)

    def EQ(self, t): return '='
    def NEQ(self, t): return '!='
    def LT(self, t): return '<'
    def GT(self, t): return '>'
    def LE(self, t): return '<='
    def GE(self, t): return '>='
    def SIMILAR(self, t): return 'similar'
    def APPROX(self, t): return 'approx'
    def PROP(self, t): return 'prop'
    def EQUIV(self, t): return 'equiv'

    #
    def additive(self, children):
      if len(children) == 1:
        return children[0]
      # Унарный минус/плюс в начале
      if len(children) == 2 and isinstance(children[0], Token):
        op = str(children[0])
        return UnaryOpNode(op=op, operand=children[1])
      # Бинарная операция
      left, op, right = children[0], children[1], children[2]
      return BinOpNode(op=str(op), left=left, right=right)


    def PLUS(self, t): return '+'
    def MINUS(self, t): return '-'

    def multiplicative(self, children):
        if len(children) == 1:
            return children[0]
        left, op, right = children[0], children[1], children[2]
        return BinOpNode(op=str(op), left=left, right=right)

    def MUL(self, t): return '*'
    def DIV(self, t): return '/'

    def power(self, children):
        if len(children) == 1:
            return children[0]
        base, exp = children[0], children[2]
        return PowNode(base=base, exp=exp)

    def EXP(self, t): return '^'

    def primary(self, children):
      if not children:
        return None
      # Обработка UNARY primary
      if len(children) == 2 and isinstance(children[0], str) and children[0] in ('-', '+'):
        return UnaryOpNode(op=children[0], operand=children[1])
      # Обработка круглых скобок
      if isinstance(children[0], str) and children[0] == '(':
        inner = children[1] if len(children) > 1 else NumberNode('0')
        return ParensNode(inner=inner)
      # Обработка curly_group
      if len(children) == 1 and isinstance(children[0], ASTNode):
        return children[0]
      return children[0]


    def NUMBER(self, t):
        return NumberNode(value=str(t))

    def VAR(self, t):
        return VarNode(name=str(t))

    def GREEK(self, t):
        return GreekNode(name=str(t))

    def LPAR(self, t): return '('
    def RPAR(self, t): return ')'

    def UNARY(self, t):
        return str(t)

    def special(self, children):
        return children[0] if children else None

    def func_call(self, children):
        return children[0] if children else None

    def _func_call_from_children(self, func_name, children):
        """Извлекает аргумент функции из детей трансформера."""
        arg = None
        # sin LPAR expr RPAR -> [func, '(', expr, ')']
        # sin VAR -> [func, var]
        # sin GREEK -> [func, greek]
        # sin expr -> [func, expr]
        for child in children:
            if isinstance(child, ASTNode) and not isinstance(child, Token):
                arg = child
                break
            elif isinstance(child, (VarNode, GreekNode)):
                arg = child
                break
        return FuncCallNode(func=func_name, args=[arg] if arg else [])

    def sin_call(self, children): return self._func_call_from_children('sin', children)
    def cos_call(self, children): return self._func_call_from_children('cos', children)
    def tan_call(self, children): return self._func_call_from_children('tan', children)
    def cot_call(self, children): return self._func_call_from_children('cot', children)
    def arcsin_call(self, children): return self._func_call_from_children('arcsin', children)
    def arccos_call(self, children): return self._func_call_from_children('arccos', children)
    def arctan_call(self, children): return self._func_call_from_children('arctan', children)
    def arccot_call(self, children): return self._func_call_from_children('arccot', children)
    def sinh_call(self, children): return self._func_call_from_children('sinh', children)
    def cosh_call(self, children): return self._func_call_from_children('cosh', children)
    def tanh_call(self, children): return self._func_call_from_children('tanh', children)
    def coth_call(self, children): return self._func_call_from_children('coth', children)
    def sqrt_call(self, children): return self._func_call_from_children('sqrt', children)
    def log_call(self, children): return self._func_call_from_children('log', children)
    def ln_call(self, children): return self._func_call_from_children('ln', children)
    def exp_call(self, children): return self._func_call_from_children('exp', children)

    def _extract_arg(self, children):
        if len(children) == 2:
            return children[1]
        elif len(children) == 4:
            return children[2]
        return children[1] if len(children) > 1 else None

    def sin_arg(self, children): return self._extract_arg(children)
    def cos_arg(self, children): return self._extract_arg(children)
    def tan_arg(self, children): return self._extract_arg(children)
    def cot_arg(self, children): return self._extract_arg(children)
    def arcsin_arg(self, children): return self._extract_arg(children)
    def arccos_arg(self, children): return self._extract_arg(children)
    def arctan_arg(self, children): return self._extract_arg(children)
    def arccot_arg(self, children): return self._extract_arg(children)
    def sinh_arg(self, children): return self._extract_arg(children)
    def cosh_arg(self, children): return self._extract_arg(children)
    def tanh_arg(self, children): return self._extract_arg(children)
    def coth_arg(self, children): return self._extract_arg(children)
    def sqrt_arg(self, children): return self._extract_arg(children)
    def log_arg(self, children): return self._extract_arg(children)
    def ln_arg(self, children): return self._extract_arg(children)
    def exp_arg(self, children): return self._extract_arg(children)

    def integral_body(self, children):
        # expr D? VAR? -> [expr] или [expr, 'd'] или [expr, VarNode] или [expr, 'd', VarNode]
        body = children[0] if children else NumberNode('0')
        var = None
        for child in children[1:]:
            if isinstance(child, Token):
                if str(child) == 'd':
                    continue
            elif isinstance(child, VarNode):
                var = child.name
                break
        return ('body', body, var)

    def integral(self, children):
        body = NumberNode('0')
        var = None
        for child in children:
            if isinstance(child, tuple) and child[0] == 'body':
                body = child[1]
                if child[2]:
                    var = child[2]
        return IntegralNode(body=body, var=var)

    def limit_expr(self, children):
        var = 'x'
        target = NumberNode('0')
        body = None
        for child in children:
            if isinstance(child, VarNode):
                var = child.name
            elif isinstance(child, InfinityNode):
                target = child
            elif isinstance(child, ASTNode) and child != target:
                body = child
        if body is None:
            body = NumberNode('0')
        return LimitNode(var=var, target=target, body=body)

    def limit_val(self, children):
        if children and isinstance(children[0], Token):
            val = str(children[0])
            if val == 'inf':
                return InfinityNode()
            return NumberNode(val)
        return children[0] if children else NumberNode('0')

    def limit_expr_tail(self, children):
        return children[0] if children else None

    def frac_expr(self, children):
        # frac expr COMMA expr -> [expr, Token(','), expr] (3 children after Transformer)
        # frac LPAR expr COMMA expr RPAR -> ['(', expr, Token(','), expr, ')'] (5 children)
        for i, child in enumerate(children):
            if isinstance(child, Token) and str(child) == ',':
                if i == 1:  # [expr, ',', expr]
                    numer = children[0]
                    denom = children[2]
                else:  # ['(', expr, ',', expr, ')']
                    numer = children[1]
                    denom = children[3]
                return FracNode(numer=numer, denom=denom)
        return children[0] if children else None

    def factorial_expr(self, children):
        if len(children) == 2:
            operand = children[0]
            op = str(children[1])
            return FactorialNode(operand=operand, double=(op == '!!'))
        return children[0] if children else None

    def BANG(self, t): return '!'
    def DOUBLE_BANG(self, t): return '!!'

    def binom_expr(self, children):
        if len(children) == 3:
            n, k = children[1], children[2]
            is_arr = str(children[0]) == 'A'
            return BinomNode(n=n, k=k, is_arrangement=is_arr)
        return children[0] if children else None

    def BINOM(self, t): return 'binom'
    def C_SYM(self, t): return 'C'
    def A_SYM(self, t): return 'A'

    def INF(self, t): return InfinityNode()

    def LPAR(self, t): return '('
    def RPAR(self, t): return ')'

    def diff_expr(self, children):
        return DerivNode(var='x')

    def deriv_expr(self, children):
        var = 'x'
        for child in children:
            if isinstance(child, VarNode):
                var = child.name
        if len(children) >= 3 and str(children[0]) == 'second':
            return SecondDerivNode(var=var)
        return DerivNode(var=var)

    def sum_expr(self, children):
        body = children[-1] if children else NumberNode('0')
        return SumNode(body=body)

    def product_expr(self, children):
        body = children[-1] if children else NumberNode('0')
        return ProductNode(body=body)


class Parser:
    def __init__(self):
        self.parser = Lark(load_grammar(), parser='lalr', transformer=ASTBuilder())

    def parse(self, text: str) -> ASTNode:
        if ' all' in text:
            text = self._balance_all(text)
        ast = self.parser.parse(text)
        return self._strip_trivial_mult_one(ast)

    def _balance_all(self, text: str) -> str:
        # all в конце -> (expr) * 1
        if re.search(r'\ball\s*$', text, flags=re.IGNORECASE):
            text = re.sub(r'\s+all\s*$', '', text, flags=re.IGNORECASE)
            text = '(' + text.strip() + ') * 1'

        while ' all ' in text:
            idx = text.find(' all ')
            start = idx
            depth = 0

            while start > 0:
                ch = text[start - 1]
                if ch == ')':
                    depth += 1
                    start -= 1
                elif ch == '(':
                    depth -= 1
                    start -= 1
                elif depth == 0 and ch in '+-*/':
                    start -= 1
                    while start > 0:
                        ch2 = text[start - 1]
                        if ch2 == ')':
                            depth += 1
                            start -= 1
                        elif ch2 == '(':
                            depth -= 1
                            start -= 1
                        elif depth == 0 and ch2 in '+-*/':
                            start -= 1
                            break
                        else:
                            start -= 1
                    break
                elif text[start - 1] == ' ':
                    start -= 1
                else:
                    start -= 1

            expr = text[start:idx].strip()
            text = text[:start] + '(' + expr + ')' + text[idx+5:]
            text = self._balance_all(text)
            break
        return text

    def _strip_trivial_mult_one(self, node: ASTNode) -> ASTNode:
        """Удаляет '* 1' из AST."""
        if isinstance(node, BinOpNode) and node.op == '*':
            if isinstance(node.right, NumberNode) and node.right.value == '1':
                return node.left
        if hasattr(node, '__dataclass_fields__'):
            from dataclasses import fields
            for field in fields(node):
                value = getattr(node, field.name)
                if isinstance(value, ASTNode):
                    setattr(node, field.name, self._strip_trivial_mult_one(value))
                elif isinstance(value, list):
                    setattr(node, field.name, [self._strip_trivial_mult_one(v) if isinstance(v, ASTNode) else v for v in value])
        return node


def main():
    p = Parser()
    tests = [
        "sin x", "cos y", "x^2", "a + b", "x = y",
        "frac 1, 2", "binom 5 2", "n!", "a + b all",
        "a + b all / c", "a + b all * c all ^ 2"
    ]
    for t in tests:
        try:
            ast = p.parse(t)
            print(f"{t!r} -> {ast!r}")
        except Exception as e:
            print(f"{t!r} -> ERROR: {e}")


if __name__ == "__main__":
    main()
