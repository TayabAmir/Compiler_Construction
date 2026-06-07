import json
from src.lexer import Lexer
from src.error_handler import ErrorHandler
from src.symbol_table import ScopeManager
from src.recursive_parser import RecursiveParser

with open('test/test_with_params.mj', 'r') as f:
    source = f.read()

errors = ErrorHandler()
lexer = Lexer(source, errors)
sym_table = ScopeManager()
parser = RecursiveParser(lexer, sym_table, errors)
success, ast = parser.parse()
data = sym_table.get_all_scopes_data()
print('Success:', success)
print('Number of scopes:', len(data))
for scope in data:
    print('Scope ' + str(scope['scope_level']) + ' (' + str(scope['entry_count']) + ' entries):')
    for e in scope['entries']:
        print('  ' + str(e['id']) + ': ' + e['name'] + ' (' + e['kind'] + ') scope=' + str(e['scope']))
print()
for e in errors.get_errors():
    print('Error:', e.to_dict())
