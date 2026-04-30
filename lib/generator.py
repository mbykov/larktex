#!/usr/bin/env python3
"""
Generator — AST → LaTeX.

Использует метод to_latex() из AST узлов.
Правила:
- Степени всегда с фигурными скобками: x^{3}
- Удаление избыточных внешних скобок вокруг FracNode, SqrtNode и т.д.
"""

from lib.ast_nodes import (
    ASTNode, ParensNode, FracNode, BinOpNode, UnaryOpNode,
    FuncCallNode, PowNode, SqrtNode, FactorialNode, VarNode,
    NumberNode, GreekNode, AllNode
)


class Generator:
    """Генератор LaTeX из AST."""

    def _strip_redundant_parens(self, ast: ASTNode) -> ASTNode:
        """Рекурсивно удалить внешние скобки вокруг самоограниченных узлов."""
        if isinstance(ast, BinOpNode):
            return BinOpNode(
                ast.op,
                self._strip_redundant_parens(ast.left),
                self._strip_redundant_parens(ast.right)
            )
        elif isinstance(ast, UnaryOpNode):
            return UnaryOpNode(ast.op, self._strip_redundant_parens(ast.operand))
        elif isinstance(ast, FuncCallNode):
            if ast.func == 'sqrt' and len(ast.args) == 1:
                return SqrtNode(self._strip_redundant_parens(ast.args[0]))
            return FuncCallNode(ast.func, [self._strip_redundant_parens(a) for a in ast.args])
        elif isinstance(ast, PowNode):
            return PowNode(
                self._strip_redundant_parens(ast.base),
                self._strip_redundant_parens(ast.exp)
            )
        elif isinstance(ast, SqrtNode):
            return SqrtNode(
                self._strip_redundant_parens(ast.radicand),
                ast.degree and self._strip_redundant_parens(ast.degree)
            )
        elif isinstance(ast, FactorialNode):
            return FactorialNode(
                self._strip_redundant_parens(ast.operand),
                ast.double
            )
        elif isinstance(ast, ParensNode):
            # Убрать скобки вокруг самоограниченных узлов: FracNode, SqrtNode, AllNode, PowNode
            if isinstance(ast.inner, (FracNode, SqrtNode, AllNode, PowNode, FactorialNode, FuncCallNode)):
                return self._strip_redundant_parens(ast.inner)
            # Убрать скобки вокруг VarNode, NumberNode, GreekNode
            if isinstance(ast.inner, (VarNode, NumberNode, GreekNode)):
                return self._strip_redundant_parens(ast.inner)
            # Иначе вернуть скобки
            return ParensNode(self._strip_redundant_parens(ast.inner))
        return ast

    def generate(self, ast: ASTNode) -> str:
        """Генерирует LaTeX из AST узла."""
        if ast is None:
            return ""
        ast = self._strip_redundant_parens(ast)
        return ast.to_latex()


def generate(ast: ASTNode) -> str:
    """Удобная функция-обёртка."""
    return Generator().generate(ast)


def main():
    """Тестовый запуск."""
    from lib.parser import Parser
    from lib.ast_nodes import (
        NumberNode, VarNode, BinOpNode, FuncCallNode
    )

    # Прямые тесты AST
    tests = [
        (NumberNode("123"), "123"),
        (VarNode("x"), "x"),
        (BinOpNode("+", VarNode("a"), VarNode("b")), "a + b"),
        (FuncCallNode("sin", [VarNode("x")]), r"\sin(x)"),
    ]

    g = Generator()
    for ast, expected in tests:
        result = g.generate(ast)
        status = "✓" if result == expected else "✗"
        print(f"{status} {ast!r} → {result!r}")

    # Тест через парсер
    p = Parser()
    parse_tests = [
        "sin x",
        "x^2",
        "a + b",
        "d x",  # дифференциал
        "frac d x,x^2",  # дробь с дифференциалом
    ]
    print("\nТест через парсер:")
    for t in parse_tests:
        try:
            ast = p.parse(t)
            latex = g.generate(ast)
            print(f"  {t!r} → {latex!r}")
        except Exception as e:
            print(f"  {t!r} → ERROR: {e}")


if __name__ == "__main__":
    main()