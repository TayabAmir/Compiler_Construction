import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))

from src.lexer import Lexer
from src.error_handler import ErrorHandler
from src.symbol_table import ScopeManager
from src.recursive_parser import RecursiveParser

test_dir = os.path.join(os.path.dirname(__file__), 'test')
mj_files = sorted(glob.glob(os.path.join(test_dir, '*.mj')))

for fp in mj_files:
    fname = os.path.basename(fp)
    with open(fp, 'r') as f:
        source = f.read()

    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = RecursiveParser(lexer, sym_table, errors)
    success, ast = parser.parse()
    data = sym_table.get_all_scopes_data()

    print(f'=== {fname} ===')
    print(f'  Success: {success}')
    for scope in data:
        kinds = [e['kind'] for e in scope['entries']]
        names = [e['name'] for e in scope['entries']]
        print(f'  Scope {scope["scope_level"]} ({scope["entry_count"]} entries): {list(zip(names, kinds))}')
    errs = errors.get_errors()
    if errs:
        for e in errs:
            d = e.to_dict()
            print(f'  Error: [{d["type"]}] line {d["line"]} - {d["message"]}')
    print()
