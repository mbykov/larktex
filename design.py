#!/usr/bin/env python3
"""
Design — финальное оформление LaTeX.

Выполняется ПОСЛЕ normalizer и parser (Lark):
1. Проверяет баланс скобок
2. Добавляет обратную косую черту перед функциями (\sin, \cos и т.д.)
3. Возвращает готовый LaTeX
"""

import re
from typing import Optional, Tuple


# Функции, которым нужна обратная косая черта в LaTeX
LATEX_FUNCS = [
    'sin', 'cos', 'tan', 'cot', 'arccot',
    'arcsin', 'arccos', 'arctan',
    'sinh', 'cosh', 'tanh', 'coth',
    'log', 'ln', 'exp', 'sqrt', 'lim',
]


def check_parentheses_balance(text: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет баланс скобок.
    
    Возвращает:
        (True, None) если всё ок
        (False, error_message) если ошибка
    """
    open_count = text.count('(')
    close_count = text.count(')')
    
    if open_count != close_count:
        if open_count > close_count:
            missing = ')' * (open_count - close_count)
            return False, f"Не хватает закрывающих скобок: {missing}"
        else:
            missing = '(' * (close_count - open_count)
            return False, f"Не хватает открывающих скобок: {missing}"
    
    # Проверка порядка: ")" не может быть перед "("
    balance = 0
    for char in text:
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
            if balance < 0:
                return False, "Закрывающая скобка встречается до открывающей"
    
    return True, None


def reduce_nested_parens(text: str) -> str:
    """
    Убирает лишние вложенные скобки: (((a + b))) → (a + b)
    Также убирает внешние скобки если всё выражение в них: (a + b) → a + b
    И убирает скобки вокруг правого операнда после операторов: a = (b + c) → a = b + c
    """
    # Убираем ((X)) на (X) где X содержит любые символы кроме сбалансированных скобок
    prev = None
    current = text
    while prev != current:
        prev = current
        current = re.sub(r'\(\(([^()]*(?:\([^()]*\)[^()]*)*)\)\)', r'(\1)', current)
    
    # Убираем внешние скобки если всё выражение в них
    while len(current) >= 2 and current[0] == '(' and current[-1] == ')':
        inner = current[1:-1]
        balance = 0
        valid = True
        for ch in inner:
            if ch == '(':
                balance += 1
            elif ch == ')':
                balance -= 1
                if balance < 0:
                    valid = False
                    break
        
        if balance == 0 and valid:
            current = inner
        else:
            break
    
    # Убираем скобки вокруг правого операнда после операторов: a = (b + c) → a = b + c
    # Находим паттерн: оператор (сбалансированные скобки) и убираем скобки
    prev = None
    while prev != current:
        prev = current
        # Паттерн: оператор followed by ( ... )
        current = re.sub(r'([=+\-*/])\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)', r'\1 \2', current)
    
    return current


def add_latex_escapes(text: str) -> str:
    r"""
    Добавляет обратную косую черту и скобки к функциям LaTeX.
    
    Примеры:
        "sin x" -> "\sin(x)"
        "sin(x)" -> "\sin(x)"
        "sqrt a + b" -> "\sqrt{a + b}"
        "cos y + sin x" -> "\cos(y) + \sin(x)"
    """
    # Сначала убираем лишние скобки
    text = reduce_nested_parens(text)
    
    result = text
    
    # Обработка sqrt отдельно (фигурные скобки)
    pattern_sqrt = r'\bsqrt\s*\(([^()]+)\)'
    def sqrt_replace(m):
        return r'\sqrt{' + m.group(1) + '}'
    result = re.sub(pattern_sqrt, sqrt_replace, result, flags=re.IGNORECASE)
    
    # Остальные функции: sin x -> sin(x) -> \sin(x)
    for func in sorted(LATEX_FUNCS, key=len, reverse=True):
        # Проверяем: sin^2 \theta -> \sin^2 \theta (без скобок)
        pattern_power = rf'\b{func}\^(\d+)\s+(\\[a-z]+)'
        def add_backslash_power(m):
            return f'\\{func}^{m.group(1)} {m.group(2)}'
        result = re.sub(pattern_power, add_backslash_power, result, flags=re.IGNORECASE)
        
        # sin \theta -> \sin \theta (без скобок)
        pattern_no_parens = rf'\b{func}\s+(\\[a-z]+)'
        def add_backslash(m):
            return f'\\{func} {m.group(1)}'
        result = re.sub(pattern_no_parens, add_backslash, result, flags=re.IGNORECASE)
        
        # sin x -> sin(x) -> \sin(x) для переменных
        pattern = rf'\b{func}\s+([a-zA-Z0-9])'
        def add_parens(m):
            return f'{func}({m.group(1)})'
        result = re.sub(pattern, add_parens, result, flags=re.IGNORECASE)
    
    # Добавляем обратную косую черту: sin(x) -> \sin(x)
    for func in LATEX_FUNCS:
        pattern = rf'(?<!\\){func}\('
        replacement = '\\\\' + func + '('
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result



def design(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Преобразует текст в LaTeX (финальное оформление).
    
    Args:
        text: Текст после parser/Lark, например "(a + b) / v"
    
    Returns:
        (latex, error)
        - (latex, None) если всё ок
        - (None, error_message) если ошибка
    """
    # Проверяем баланс скобок
    balanced, error = check_parentheses_balance(text)
    if not balanced:
        return None, f"Ошибка скобок в '{text}': {error}"
    
    # Убираем лишние скобки
    text = reduce_nested_parens(text)
    
    # Добавляем LaTeX-экранирование функций
    latex = add_latex_escapes(text)
    
    return latex, None


def main():
    """Тестовый запуск."""
    test_cases = [
        "(a + b) / v",
        "\\sin(x)",
        "\\sqrt{a + b}",
        "(a + b",  # Ошибка: не хватает )
        "a + b)",  # Ошибка: не хватает (
        "\\sin(x) + \\cos(y)",
        "integral x d x",
    ]
    
    for test in test_cases:
        result, error = design(test)
        if error:
            print(f"{test!r} → ERROR: {error}")
        elif result:
            print(f"{test!r} → {result!r}")
        else:
            print(f"{test!r} → (no changes)")


if __name__ == "__main__":
    main()