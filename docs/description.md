# Описание проекта LarkTeX

LarkTeX — конвертер математического текста на русском языке в формат LaTeX.

## Архитектура

```
Русский текст
    ↓
normalizer.py (нормализация)
    ↓
grammar.lark (парсинг)
    ↓
parser.py (преобразование в LaTeX)
    ↓
LaTeX код
```

---

## normalizer.py

Нормализатор преобразует русский математический текст в латинскую транскрипцию, понятную парсеру.

### Принцип работы

1. **Загрузка словарей** из `i18n/ru.json` по категориям
2. **Обработка особых фраз** (special phrases) — составные конструкции
3. **Замена слов** по словарям (функции, операторы, греческие буквы и т.д.)
4. **Очистка** — удаление лишних пробелов

### Категории словарей

| Категория | Описание | Примеры |
|-----------|----------|---------|
| `variables` | Переменные | `икс` → `x`, `йота` → `j` |
| `functions` | Математические функции | `синус` → `sin`, `косинус` → `cos` |
| `operators` | Операторы | `плюс` → `+`, `умножить` → `*` |
| `powers` | Степени | `в квадрате` → `^2`, `в кубе` → `^3` |
| `numbers` | Числа | `один` → `1`, `два` → `2` |
| `special` | Особые термины | `бесконечность` → `inf` |
| `logic` | Логические операторы | `и` → `and`, `или` → `or` |
| `relations` | Отношения | `равно` → `=`, `примерно` → `≈` |
| `integrals` | Интегралы | `интеграл` → `integral`, `де` → `d` |
| `summation` | Суммы и произведения | `сумма` → `sum`, `произведение` → `product` |
| `derivatives` | Производные | `производная` → `deriv`, `вторую производную` → `second deriv` |
| `misc` | Прочее | `frac` → `frac`, `partial` → `partial` |
| `factorials` | Факториалы | `факториал` → `!`, `двойной факториал` → `!!` |

### Особые фразы (special_phrases)

Составные конструкции, обрабатываемые до общей замены слов:

| Фраза | Замена | Пример |
|-------|--------|--------|
| `квадратный корень из` | `sqrt` | `квадратный корень из икс` → `sqrt x` |
| `дробь ... на ...` | `frac ...,...` | `дробь икс на игрек` → `frac x,y` |
| `производная от ... по ...` | `deriv with respect to ...` | `производная от икс по иксу` → `deriv with respect to x` |
| `ц из ... по ...` | `binom ... ...` | `ц из 5 по 2` → `binom 5 2` |
| `а из ... по ...` | `A ... ...` | `а из 5 по 2` → `A 5 2` |
| `... факториал` | `...!` | `эн факториал` → `n!` |
| `... двойной факториал` | `...!!` | `5 двойной факториал` → `5!!` |

### Порядок обработки

1. Особые составные фразы (`_special_phrases`)
2. Дроби (`дробь ... на ...`)
3. Производные (`производная от ... по ...`)
4. Биномиальные коэффициенты (`ц из ... по ...`)
5. Размещения (`а из ... по ...`)
6. Факториалы (`... факториал`)
7. Степени (`в квадрате`, `в кубе`)
8. Всё/все → `all`
9. Делить на → `/`
10. Де → `d`
11. Предлоги (удаление)
12. Общая замена по словарям
13. Очистка пробелов

---

## grammar.lark

Описание грамматики для LALR-парсера библиотеки Lark.

### Основные правила

```lark
start: expr

expr: comparison
comparison: additive (relation additive)?
additive: multiplicative ((PLUS | MINUS) multiplicative)*
multiplicative: power ((MUL | DIV) power)*
power: primary (EXP primary)?
primary: NUMBER | GREEK | LPAR expr RPAR | special | UNARY primary | VAR | func_call
```

### Поддерживаемые конструкции

#### Функции
```lark
func_call: sin_call | cos_call | tan_call | cot_call
         | arcsin_call | arccos_call | arctan_call | arccot_call
         | sinh_call | cosh_call | tanh_call | coth_call
         | log_call | ln_call | exp_call

sin_call: "sin" LPAR expr RPAR | "sin" VAR | "sin" GREEK
```

#### Интегралы
```lark
integral: "integral" ("from" expr "to" expr)? ("of")? integral_body
integral_body: primary ("d" VAR)?
```

#### Суммы и произведения
```lark
sum_expr: "sum" ("from" expr "to" expr)? ("of")? primary
product_expr: "product" ("from" expr "to" expr)? ("of")? primary
```

#### Пределы
```lark
limit_expr: "lim" ("as")? VAR TENDS_TO limit_val limit_expr_tail
limit_val: NUMBER | VAR | GREEK | INF
limit_expr_tail: ("of")? primary
```

#### Дроби
```lark
frac_expr: "frac" LPAR expr "," expr RPAR | "frac" expr "," expr
```

#### Производные
```lark
deriv_expr: "deriv" ("with" "respect" "to")? VAR
          | "partial" ("with" "respect" "to")? VAR
          | "second" "deriv" ("with" "respect" "to")? VAR
```

#### Факториалы
```lark
factorial_expr: primary "!" | primary "!!"
```

#### Биномиальные коэффициенты и размещения
```lark
binom_expr: BINOM NUMBER NUMBER
          | C_SYM NUMBER NUMBER
          | A_SYM NUMBER NUMBER

BINOM: "binom"
C_SYM: "C"
A_SYM: "A"
```

### Токены

| Токен | Описание |
|-------|----------|
| `VAR` | Латинские переменные (a-z) |
| `GREEK` | Греческие буквы (альфа, бета, ...) |
| `NUMBER` | Числа (0-9) |
| `COMMA` | Запятая (`,`) |
| `UNARY` | Унарные операторы (`-`, `+`) |
| `TENDS_TO` | Стремится к (`tends_to`) |
| `INF` | Бесконечность (`inf`) |

---

## parser.py

Transformer, преобразующий AST (абстрактное синтаксическое дерево) от Lark в LaTeX код.

### Основные методы

| Метод | Описание |
|-------|----------|
| `parse(text: str) → str` | Преобразует нормализованный текст в LaTeX |
| `expr(c)` | Обработка выражений |
| `comparison(c)` | Обработка сравнений |
| `func_call(c)` | Обработка вызовов функций |
| `integral(c)` | Обработка интегралов |
| `limit_expr(c)` | Обработка пределов |
| `frac_expr(c)` | Обработка дробей |
| `deriv_expr(c)` | Обработка производных |
| `factorial_expr(c)` | Обработка факториалов |
| `binom_expr(c)` | Обработка биномиальных коэффициентов |

### Примеры преобразования

| Нормализованный текст | LaTeX |
|-----------------------|-------|
| `sin x` | `\sin(x)` |
| `x^2` | `x^2` |
| `sqrt a` | `\sqrt{a}` |
| `integral x d x` | `\int x \, d x` |
| `lim x tends_to inf of exp x` | `\lim_{x \to inf} \exp(x)` |
| `frac x,y` | `\frac{x}{y}` |
| `deriv with respect to x` | `\frac{d}{dx}` |
| `n!` | `n!` |
| `binom 5 2` | `\binom{5}{2}` |
| `A 5 2` | `\frac{5!}{(5 - 2)!}` |

---

## Расширяемость

### Добавление новых функций

1. **Добавить синонимы** в `i18n/ru.json` (например, в секцию `functions`)
2. **Добавить правило** в `grammar.lark` (например, `new_func_call`)
3. **Добавить метод** в `parser.py` (например, `def new_func_call(self, c): ...`)

### Добавление новых особых фраз

1. **Добавить в `_special_phrases`** в `normalizer.py` (список кортежей `(phrase, replacement)`)

---

## Тестирование

Все тесты находятся в `tests/expected_latex.jsonl`. Формат:

```json
{"input": "синус икс", "expected": "\\sin(x)"}
{"input": "ц из 5 по 2", "expected": "\\binom{5}{2}"}
```

Запуск тестов:

```bash
uv run python -c "
import json
from larktex import LarktexEngine

engine = LarktexEngine.get_instance()
with open('tests/expected_latex.jsonl') as f:
    for line in f:
        test = json.loads(line)
        result = engine.process(test['input'])
        assert result == test['expected'], f'{test[\"input\"]}: {result} != {test[\"expected\"]}'
print('Все тесты пройдены!')
"
```