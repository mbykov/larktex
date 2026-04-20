#!/usr/bin/env python3
import readline
import subprocess
import tempfile
import os
from extractor import MathExtractor

# Настройка readline для поддержки истории
histfile = os.path.join(os.path.expanduser("~"), ".math_extractor_history")
try:
    readline.read_history_file(histfile)
    readline.set_history_length(1000)
except FileNotFoundError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)

def latex_to_svg_and_show(latex_code, view=True):
    # Используем XeLaTeX: он идеально понимает русский и формулы одновременно
    full_tex = f"""\\documentclass[12pt]{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\setmainfont{{Liberation Serif}} % Или другой системный шрифт, например DejaVu Serif
\\thispagestyle{{empty}}
\\begin{{document}}
\\huge
{latex_code}
\\end{{document}}"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(full_tex)
        tex_file = f.name
        base_path = tex_file[:-4]
        work_dir = os.path.dirname(tex_file)

    try:
        # 1. Запускаем xelatex
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', f'-output-directory={work_dir}', tex_file],
            capture_output=True, text=True
        )

        pdf_file = f'{base_path}.pdf'

        if not os.path.exists(pdf_file):
            print("\n❌ XeLaTeX Fatal Error!")
            print(result.stdout[-500:]) # Показать конец лога
            return None

        # 2. PDF -> SVG
        svg_file = f'{base_path}.svg'
        subprocess.run(
            ['dvisvgm', '--no-fonts', '--pdf', '--exact', pdf_file, '-o', svg_file],
            check=True, capture_output=True
        )

        if view and os.path.exists(svg_file):
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(['inkview', svg_file], stdout=devnull, stderr=devnull)

        return svg_file

    except Exception as e:
        print(f"\nSystem Error: {e}")
    finally:
        # Убираем за собой
        for ext in ['.tex', '.pdf', '.log', '.aux', '.xdv']:
            try: os.remove(base_path + ext)
            except: pass

def main():
    ex = MathExtractor()
    print("--- Math2Latex Debugger ---")
    print("Вводите формулу словами (Ctrl+C для выхода)")

    while True:
        try:
            user_input = input(">>> ").strip()
            if not user_input:
                continue

            #
            result = ex.transform_text(user_input) # <--- Сменили метод

            print(f"LaTeX: {result}")

            if "Error" not in result:
                latex_to_svg_and_show(result)
            else:
                print(f"Скип визуализации из-за ошибки.")

        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()
