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
    clean_latex = latex_code.replace('$', '')

    # Using 'article' instead of 'standalone' to avoid missing package errors
    full_tex = f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{xcolor}}  % <--- ADD THIS
\\thispagestyle{{empty}}
\\begin{{document}}
\\huge
${clean_latex}$
\\end{{document}}"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(full_tex)
        tex_file = f.name
        base_path = tex_file[:-4]
        work_dir = os.path.dirname(tex_file)

    try:
        # Run pdflatex
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', f'-output-directory={work_dir}', tex_file],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print("--- LaTeX Error Log ---")
            print(result.stdout)
            return None

        pdf_file = f'{base_path}.pdf'
        svg_file = f'{base_path}.svg'

        # dvisvgm with --pDC (page data crop) to remove empty space around the formula
        subprocess.run(
            ['dvisvgm', '--no-fonts', '--pdf', '--exact', pdf_file, '-o', svg_file],
            check=True, capture_output=True
        )

        if view and os.path.exists(svg_file):
            subprocess.Popen(['inkview', svg_file])

        return svg_file

    except Exception as e:
        print(f"System Error: {e}")
    finally:
        for ext in ['.tex', '.pdf', '.log', '.aux']:
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

            result = ex.transform(user_input)
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
