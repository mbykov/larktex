#!/usr/bin/env python3
"""Тесты для нормализатора с детализированным выводом."""

import json
import sys
from pathlib import Path

# Добавить корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalizer import Normalizer


# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'


def load_test_cases(jsonl_path: Path):
    """Загрузить тесты из JSONL файла."""
    tests = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    test_data = json.loads(line)
                    test_data['_line_num'] = line_num
                    tests.append(test_data)
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга строки {line_num}: {e}")
                    sys.exit(1)
    return tests


def main():
    """Запуск тестов с детализированным выводом."""
    # Путь к файлу с тестами
    tests_dir = Path(__file__).parent
    jsonl_file = tests_dir / "expected_norm.jsonl"
    
    if not jsonl_file.exists():
        print(f"Ошибка: файл {jsonl_file} не найден")
        sys.exit(1)
    
    # Инициализировать нормализатор
    i18n_dir = tests_dir.parent / "i18n"
    if not i18n_dir.exists():
        print(f"Ошибка: директория {i18n_dir} не найдена")
        sys.exit(1)
    
    normalizer = Normalizer(i18n_dir=str(i18n_dir))
    
    # Загрузить тесты
    test_cases = load_test_cases(jsonl_file)
    
    if not test_cases:
        print("Нет тестов для выполнения")
        sys.exit(1)
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for i, tc in enumerate(test_cases):
        input_text = tc.get('input', '')
        expected = tc.get('expected', '')
        line_num = tc.get('_line_num', '?')
        
        # Выполнить нормализацию
        actual = normalizer.normalize_text(input_text)
        
        # Проверить результат
        if actual == expected:
            print(f"{GREEN}✓{RESET} {input_text} - {expected}")
            passed += 1
        else:
            # Сохранить информацию о failed тесте
            failed_tests.append({
                'line_num': line_num,
                'input': input_text,
                'expected': expected,
                'actual': actual
            })
            failed += 1
    
    # Вывести отладочную информацию для failed тестов
    if failed_tests:
        print(f"\n{RED}{'=' * 70}{RESET}")
        print(f"{RED}НЕ ПРОЙДЕННЫЕ ТЕСТЫ{RESET}")
        print(f"{RED}{'=' * 70}{RESET}")
        
        for ft in failed_tests:
            print(f"\n{RED}--- Тест (строка {ft['line_num']}) ---{RESET}")
            print(f"  Input:    {ft['input']!r}")
            print(f"  Expected: {ft['expected']!r}")
            print(f"  Actual:   {ft['actual']!r}")
            
            # Показать различия
            print(f"\n  Различия:")
            print(f"    Ожидаемая длина: {len(ft['expected'])}")
            print(f"    Фактическая длина: {len(ft['actual'])}")
            
            # Показать посимвольно
            min_len = min(len(ft['expected']), len(ft['actual']))
            for pos in range(min_len):
                if ft['expected'][pos] != ft['actual'][pos]:
                    print(f"    Первая разница на позиции {pos}:")
                    print(f"      Expected[{pos}]: {ft['expected'][pos]!r} (ord={ord(ft['expected'][pos])})")
                    print(f"      Actual[{pos}]:   {ft['actual'][pos]!r} (ord={ord(ft['actual'][pos])})")
                    
                    # Показать контекст вокруг различия
                    ctx_start = max(0, pos - 10)
                    ctx_end_exp = min(len(ft['expected']), pos + 10)
                    ctx_end_act = min(len(ft['actual']), pos + 10)
                    print(f"\n    Контекст (Expected): ...{ft['expected'][ctx_start:ctx_end_exp]!r}...")
                    print(f"    Контекст (Actual):   ...{ft['actual'][ctx_start:ctx_end_act]!r}...")
                    break
            
            # Показать diff-подобный вывод
            print(f"\n  Пошаговое сравнение токенов:")
            exp_tokens = ft['expected'].split()
            act_tokens = ft['actual'].split()
            
            max_tokens = max(len(exp_tokens), len(act_tokens))
            for j in range(max_tokens):
                exp_tok = exp_tokens[j] if j < len(exp_tokens) else "(нет)"
                act_tok = act_tokens[j] if j < len(act_tokens) else "(нет)"
                marker = "✓" if exp_tok == act_tok else "✗"
                print(f"    [{j:2d}] {marker} Expected: {exp_tok!r:15} Actual: {act_tok!r}")
            
            print(f"{RED}{'=' * 70}{RESET}")
    
    # Итоговая статистика
    print(f"\n{'=' * 60}")
    print(f"ИТОГИ: {passed} пройдено, {failed} не пройдено из {len(test_cases)}")
    print(f"{'=' * 60}")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
