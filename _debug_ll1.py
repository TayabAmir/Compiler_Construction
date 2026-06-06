from __future__ import annotations

import sys, os
sys.path.insert(0, os.getcwd())
from src.ll1_parser import LL1Parser
from src.lexer import Lexer
from src.error_handler import ErrorHandler
from src.token import grammar_symbol_to_display

source = open('test/test1_valid.mj').read()
errors = ErrorHandler()
lexer = Lexer(source, errors)
tokens = lexer.tokenize_all()
print(f'Tokens ({len(tokens)}):')
for t in tokens:
    gs = t.to_grammar_symbol()
    print(f'  [{t.line},{t.col}] {t.type_to_string():25} -> grammar: {grammar_symbol_to_display(gs)}')

errors2 = ErrorHandler()
parser = LL1Parser(errors2)
parser.initialize_microjava_grammar()
parser.compute_sets()
result = parser.parse(tokens)
print(f'\nSuccess: {result["success"]}')
if errors2.has_errors():
    for e in errors2.get_errors():
        print(f'  Error: {e.message}')
for i, step in enumerate(result.get('trace', [])):
    print(f'  Step {i}: stack=[{step["stack"]}], input=[{step["input"]}], action={step["action"]}')
    if i > 50:
        print('  ... (truncated)')
        break
