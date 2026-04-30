#!/usr/bin/env python3
"""
AST узлы с методом to_latex().

Постепенная миграция на AST:
    Text → Normalizer → string → Parser → AST → Generator (to_latex) → LaTeX
"""

from dataclasses import dataclass
from typing import Union, List, Optional


@dataclass
class NumberNode:
    """Число: 123, 3.14"""
    value: str

    def to_latex(self) -> str:
        return self.value


@dataclass
class VarNode:
    """Переменная: x, y"""
    name: str

    def to_latex(self) -> str:
        return self.name


@dataclass
class GreekNode:
    """Греческая буква: alpha, beta"""
    name: str

    _latex = {
        'alpha': r'\alpha', 'beta': r'\beta', 'gamma': r'\gamma',
        'delta': r'\delta', 'epsilon': r'\epsilon', 'zeta': r'\zeta',
        'eta': r'\eta', 'theta': r'\theta', 'iota': r'\iota',
        'kappa': r'\kappa', 'lambda': r'\lambda', 'mu': r'\mu',
        'nu': r'\nu', 'xi': r'\xi', 'pi': r'\pi', 'rho': r'\rho',
        'sigma': r'\sigma', 'tau': r'\tau', 'phi': r'\phi',
        'chi': r'\chi', 'psi': r'\psi', 'omega': r'\omega',
    }

    def to_latex(self) -> str:
        return self._latex.get(self.name, self.name)


@dataclass
class InfinityNode:
    """Бесконечность: inf"""
    def to_latex(self) -> str:
        return 'inf'


@dataclass
class UnaryOpNode:
    """Унарная операция: -x, +x"""
    op: str
    operand: 'ASTNode'

    def to_latex(self) -> str:
        return f"{self.op}{self.operand.to_latex()}"


@dataclass
class BinOpNode:
    """Бинарная операция: +, -, *, /, ^"""
    op: str
    left: 'ASTNode'
    right: 'ASTNode'

    def to_latex(self) -> str:
        left = self.left.to_latex()
        right = self.right.to_latex()
        if self.op == '/':
            # Для BinOpNode '/' генерируем как a / b со скобками
            left_latex = f"({left})" if isinstance(self.left, BinOpNode) else left
            right_latex = f"({right})" if isinstance(self.right, BinOpNode) else right
            return f"{left_latex} / {right_latex}"
        elif self.op == '^':
            exp = right
            if len(exp) == 1 and exp.isdigit():
                return f"{left}^{exp}"
            return f"{left}^{{{exp}}}"
        elif self.op == '*':
            # Особый случай: d * x → d x (дифференциал)
            if isinstance(self.left, VarNode) and self.left.name == 'd':
                return f"d {right}"
            return f"{left} * {right}"
        else:
            return f"{left} {self.op} {right}"


@dataclass
class RelationNode:
    """Отношение: =, <, >, approx, ..."""
    op: str
    left: 'ASTNode'
    right: 'ASTNode'

    _latex = {
        '=': '=', '!=': r'\neq', '<': '<', '>': '>',
        '<=': r'\leq', '>=': r'\geq', 'approx': r'\approx',
        'similar': r'\sim', 'prop': r'\propto', 'equiv': r'\equiv',
    }

    def to_latex(self) -> str:
        return f"{self.left.to_latex()} {self._latex.get(self.op, self.op)} {self.right.to_latex()}"


@dataclass
class ParensNode:
    """Скобки: (expr)"""
    inner: 'ASTNode'

    def to_latex(self) -> str:
        return f"({self.inner.to_latex()})"


@dataclass
class FuncCallNode:
    """Функция: sin(x), cos(x), sqrt(x)"""
    func: str
    args: List['ASTNode']

    _latex = {
        'sin': r'\sin', 'cos': r'\cos', 'tan': r'\tan', 'cot': r'\cot',
        'arcsin': r'\arc\sin', 'arccos': r'\arc\cos', 'arctan': r'\arc\tan', 'arccot': r'\arc\cot',
        'sinh': r'\sinh', 'cosh': r'\cosh', 'tanh': r'\tanh', 'coth': r'\coth',
        'exp': r'\exp', 'log': r'\log', 'ln': r'\ln',
    }

    def to_latex(self) -> str:
        latex_func = self._latex.get(self.func, self.func)
        if self.func == 'sqrt':
            arg = self.args[0].to_latex() if self.args else ''
            return rf"\sqrt{{{arg}}}"
        elif self.func in self._latex:
            args_str = ' '.join(a.to_latex() for a in self.args)
            return f"{latex_func}({args_str})"
        else:
            args_str = ', '.join(a.to_latex() for a in self.args)
            return f"{latex_func}({args_str})"


@dataclass
class PowNode:
    """Степень: base^exp"""
    base: 'ASTNode'
    exp: 'ASTNode'

    def to_latex(self) -> str:
        base_latex = self.base.to_latex()
        exp_latex = self.exp.to_latex()
        # Всегда использовать фигурные скобки для экспоненты
        # Даже если это одна цифра: a^{2} вместо a^2
        return f"{base_latex}^{{{exp_latex}}}"


@dataclass
class SqrtNode:
    """Корень: sqrt[degree]{radicand}"""
    radicand: 'ASTNode'
    degree: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        radicand_latex = self.radicand.to_latex()
        if self.degree:
            degree_latex = self.degree.to_latex()
            return rf"\sqrt[{degree_latex}]{{{radicand_latex}}}"
        return rf"\sqrt{{{radicand_latex}}}"


@dataclass
class FracNode:
    """Дробь: numer/denom"""
    numer: 'ASTNode'
    denom: 'ASTNode'

    def to_latex(self) -> str:
        return rf"\frac{{{self.numer.to_latex()}}}{{{self.denom.to_latex()}}}"


@dataclass
class FactorialNode:
    """Факториал: n!, n!!"""
    operand: 'ASTNode'
    double: bool = False

    def to_latex(self) -> str:
        return f"{self.operand.to_latex()}{'!!' if self.double else '!'}"


@dataclass
class BinomNode:
    """Бином: C(n,k) или A(n,k)"""
    n: 'ASTNode'
    k: 'ASTNode'
    is_arrangement: bool = False

    def to_latex(self) -> str:
        n_latex = self.n.to_latex()
        k_latex = self.k.to_latex()
        if self.is_arrangement:
            return rf"\frac{{{n_latex}!}}{{({n_latex} - {k_latex})!}}"
        return rf"\binom{{{n_latex}}}{{{k_latex}}}"


@dataclass
class LimitNode:
    """Предел: lim_{x->a} body"""
    var: str
    target: 'ASTNode'
    body: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        target_latex = self.target.to_latex()
        if self.body:
            return rf"\lim_{{{self.var} \to {target_latex}}} {self.body.to_latex()}"
        return rf"\lim_{{{self.var} \to {target_latex}}}"


@dataclass
class DerivNode:
    """Производная: d/dx"""
    var: str
    expr: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        if self.expr:
            return rf"\frac{{d}}{{d{self.var}}} {self.expr.to_latex()}"
        return rf"\frac{{d}}{{d{self.var}}}"


@dataclass
class SecondDerivNode:
    """Вторая производная: d^2/dx^2"""
    var: str
    expr: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        if self.expr:
            return rf"\frac{{d^2}}{{d{self.var}^2}} {self.expr.to_latex()}"
        return rf"\frac{{d^2}}{{d{self.var}^2}}"


@dataclass
class PartialDerivNode:
    """Частная производная: d/dx"""
    var: str
    expr: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        if self.expr:
            return rf"\frac{{\partial}}{{\partial {self.var}}} {self.expr.to_latex()}"
        return rf"\frac{{\partial}}{{\partial {self.var}}}"


@dataclass
class IntegralNode:
    """Интеграл: ∫"""
    body: 'ASTNode'
    lower: Optional['ASTNode'] = None
    upper: Optional['ASTNode'] = None
    var: Optional[str] = None

    def to_latex(self) -> str:
        body_latex = self.body.to_latex()
        bounds = ''
        if self.lower or self.upper:
            lower_latex = self.lower.to_latex() if self.lower else ''
            upper_latex = self.upper.to_latex() if self.upper else ''
            bounds = f"_{{{lower_latex}}}^{{{upper_latex}}}"
        result = rf"\int{bounds} {body_latex}"
        if self.var:
            result += rf" \, d {self.var}"
        return result


@dataclass
class SumNode:
    """Сумма: Σ"""
    body: 'ASTNode'
    lower: Optional['ASTNode'] = None
    upper: Optional['ASTNode'] = None
    var: Optional[str] = None

    def to_latex(self) -> str:
        body_latex = self.body.to_latex()
        bounds = ''
        if self.lower or self.upper:
            lower_latex = self.lower.to_latex() if self.lower else ''
            upper_latex = self.upper.to_latex() if self.upper else ''
            bounds = f"_{{{lower_latex}}}^{{{upper_latex}}}"
        var_part = f"_{{{self.var}}}" if self.var else ''
        return rf"\sum{var_part}{bounds} {body_latex}"


@dataclass
class ProductNode:
    """Произведение: Π"""
    body: 'ASTNode'
    lower: Optional['ASTNode'] = None
    upper: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        body_latex = self.body.to_latex()
        bounds = ''
        if self.lower or self.upper:
            lower_latex = self.lower.to_latex() if self.lower else ''
            upper_latex = self.upper.to_latex() if self.upper else ''
            bounds = f"_{{{lower_latex}}}^{{{upper_latex}}}"
        return rf"\prod{bounds} {body_latex}"


@dataclass
class AllNode:
    """Маркер 'all' — весь/вся/всё"""
    operand: Optional['ASTNode'] = None

    def to_latex(self) -> str:
        if self.operand:
            return f"({self.operand.to_latex()})"
        return ''


ASTNode = Union[
    NumberNode, VarNode, GreekNode, InfinityNode,
    UnaryOpNode, BinOpNode, RelationNode, ParensNode,
    FuncCallNode, PowNode, SqrtNode, FracNode, FactorialNode, BinomNode,
    LimitNode, DerivNode, SecondDerivNode, PartialDerivNode,
    IntegralNode, SumNode, ProductNode, AllNode,
]
