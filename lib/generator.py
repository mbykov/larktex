#!/usr/bin/env python3
"""
Generator — AST → LaTeX.

Использует метод to_latex() из AST узлов.
"""

from lib.ast_nodes import ASTNode


class Generator:
    """Генератор LaTeX из AST."""

    def generate(self, ast: ASTNode) -> str:
        """Генерирует LaTeX из AST узла."""
        if ast is None:
            return ""
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
