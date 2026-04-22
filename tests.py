import json
import sys
import os
import logging
from typing import Optional, List, Tuple, Dict, Any
from extractor import MathExtractor
from lark import Lark

logging.basicConfig(level=logging.WARNING, force=True)

def _debug_transform(ex: MathExtractor, text: str) -> Tuple[str, Dict[str, Any]]:
    info: Dict[str, Any] = {}
    step1 = ex.num_converter.replace(text)
    info['num_converted'] = step1
    
    words = step1.split()
    segments: List[Tuple[str, str]] = []
    current: List[str] = []
    
    for w in words:
        if ex.is_math_word(w):
            current.append(w)
        else:
            if current:
                segments.append(('math', ' '.join(current)))
                current = []
            segments.append(('text', w))
    if current:
        segments.append(('math', ' '.join(current)))
    
    info['segments'] = segments
    info['words'] = words
    
    math_segments_debug = []
    for seg_type, val in segments:
        if seg_type == 'math':
            norm = ex.normalize_island(val)
            info['island_normalized'] = norm
            latex = None
            error = None
            with_vse = False
            
            try:
                tree = ex.parser.parse(norm)
                latex = ex.transformer.transform(tree)
                if isinstance(latex, list):
                    latex = latex[0] if len(latex) == 1 else ''.join(latex)
            except Exception:
                try:
                    tree = ex.parser.parse(norm + ' VSE')
                    latex = ex.transformer.transform(tree)
                    if isinstance(latex, list):
                        latex = latex[0] if len(latex) == 1 else ''.join(latex)
                    with_vse = True
                except Exception as e2:
                    error = str(e2)
            
            math_segments_debug.append({
                'input': val,
                'normalized': norm,
                'latex': latex,
                'error': error,
                'with_vse': with_vse
            })
    
    info['math_segments'] = math_segments_debug
    
    result_parts = []
    for seg_type, val in segments:
        if seg_type == 'math':
            seg_data = next((s for s in math_segments_debug if s['input'] == val), None)
            if seg_data and seg_data.get('latex'):
                latex = seg_data['latex']
                if isinstance(latex, list):
                    latex = latex[0] if len(latex) == 1 else ''.join(latex)
                result_parts.append('$' + latex + '$')
            else:
                result_parts.append(val)
        else:
            result_parts.append(val)
    
    raw_result = ' '.join(result_parts)
    info['raw_result'] = raw_result
    result = raw_result.replace('$', '')
    info['final_result'] = result
    
    return result, info

def run_tests(filepath: str) -> None:
    ex = MathExtractor()
    passed = 0
    total = 0

    if not os.path.exists(filepath):
        print(f"Error: file {filepath} not found.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            text = data.get('input')
            expected = data.get('expected')

            if not text or not expected:
                print(f"Line {line_num}: Missing 'input' or 'expected' field")
                continue

            result, debug_info = _debug_transform(ex, text)

            if result == expected:
                print(f"PASS (line {line_num}): {text}")
                passed += 1
            else:
                print(f"\nFAIL (line {line_num}):")
                print(f"  Input:       {text}")
                print(f"  Expected:    {expected}")
                print(f"  Got:         {result}")
                print(f"  Raw output:  {debug_info.get('raw_result', 'N/A')}")
                print(f"  Num conv:    {debug_info.get('num_converted', 'N/A')}")
                print(f"  Segments:    {debug_info.get('segments', 'N/A')}")
                print(f"  Words:       {debug_info.get('words', 'N/A')}")
                
                math_segs = debug_info.get('math_segments', [])
                if math_segs:
                    print(f"  Math islands:")
                    for i, seg in enumerate(math_segs, 1):
                        error = seg.get('error')
                        if error:
                            print(f"    [{i}] Input: {seg['input']}")
                            print(f"        Normalized: {seg['normalized']}")
                            print(f"        Error: {error}")
                        else:
                            vse_mark = " (with VSE)" if seg.get('with_vse') else ""
                            print(f"    [{i}] Input: {seg['input']} -> {seg['latex']}{vse_mark}")
                
                sys.exit(1)

            total += 1

        except json.JSONDecodeError as e:
            print(f"JSON error (line {line_num}): {e}")
            print(f"   Content: {line}")
            sys.exit(1)
        except ValueError as e:
            print(f"ValueError (line {line_num}): {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error (line {line_num}): {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print(f"\nSummary: {passed}/{total} tests passed.")

if __name__ == "__main__":
    path_to_file = sys.argv[1] if len(sys.argv) > 1 else 'tests.jsonl'
    run_tests(path_to_file)
