# LarkTex — Русский математический текст в LaTeX

Конвертер математического текста на русском языке в LaTeX с поддержкой правила `all` для группировки выражений.

## Быстрый старт

```bash
# CLI режим
python client.py "синус икс"
# → \sin(x)

# Batch режим
echo '{"input": "корень из а"}' | python server.py
# → {"latex": "\\sqrt{a}", "status": "ok"}

# Тесты
bash tests/run_test.sh
```

## Основные возможности

- ✅ Русский математический текст → LaTeX
- ✅ Правило `all` для группировки выражений: `"а плюс б всё"` → `(a + b)`
- ✅ Функции: `синус`, `косинус`, `тангенс`, `логарифм`, `экспонента`
- ✅ Дроби: `дробь а на б` → `\frac{a}{b}`
- ✅ Степени: `икс в квадрате` → `x^2`
- ✅ Корни: `корень из а` → `\sqrt{a}`
- ✅ Интегралы, пределы, производные
- ✅ Факториалы, биномиальные коэффициенты

## Архитектура

```
Текст → Normalizer → Парсер → AST → Generator → LaTeX
```

- `lib/normalizer.py` — замена русских слов на латинские символы
- `lib/parser.py` — Lark грамматика → AST
- `lib/generator.py` — AST → LaTeX
- `server.py` / `client.py` — сервис через stdin/stdout

## Документация

- [Подробное описание правил](docs/description.md)
- [Нормализация текста](docs/normalizer.md)

## Тестирование

```bash
# Все тесты (26 случаев)
python tests/test_lib.py

# Через server.py
bash tests/run_test.sh

# pytest
pytest tests/test_lib.py -v
```

## Лицензия

MIT