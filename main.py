from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.token import Token, TokenType
from src.lexer import Lexer
from src.error_handler import ErrorHandler, ErrorType
from src.symbol_table import ScopeManager, IdentifierKind, DataType
from src.recursive_parser import RecursiveParser
from src.ll1_parser import LL1Parser
from src.lr_parser import LRParser
from src.operator_precedence_parser import OperatorPrecedenceParser


TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")


def read_source(path: str) -> str:
    if not os.path.exists(path):
        test_path = os.path.join(TEST_DIR, path)
        if os.path.exists(test_path):
            path = test_path
        else:
            print(f"[ERROR] File not found: {path}")
            print(f"        (tried: {path} and {test_path})")
            sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def print_header(title: str):
    width = 68
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_separator():
    print("-" * 68)


def print_section(title: str):
    print()
    print(f"  >>> {title} <<<")
    print()


def run_lexer(source: str):
    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    tokens = lexer.tokenize_all()

    print_header("LEXICAL ANALYZER OUTPUT")
    print(f"  Token count: {len(tokens)}")
    print_separator()
    print(f"  {'Line':>4}  {'Col':>3}  {'Type':<25}  {'Lexeme'}")
    print_separator()
    for t in tokens:
        lexeme = t.lexeme if t.lexeme else ""
        print(f"  {t.line:>4}  {t.col:>3}  {t.type_to_string():<25}  {lexeme}")
    print_separator()
    print_summary(errors)
    return tokens


def run_ast(source: str):
    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = RecursiveParser(lexer, sym_table, errors)

    print_header("ABSTRACT SYNTAX TREE (AST) OUTPUT")
    success, ast = parser.parse()
    print(f"  Result: {'[PASS]' if success else '[FAIL]'}")
    print_separator()
    if ast:
        print("  AST (tree view):")
        _print_ast(ast, 2)
    else:
        print("  (no AST produced)")
    print_separator()
    print_summary(errors)
    return success


def _print_ast(node, indent: int = 0):
    if node is None:
        return
    prefix = "  " * indent
    label = node.node_type.value
    attrs = []
    for attr in ("name", "value", "op", "data_type", "return_type", "width"):
        if hasattr(node, attr) and getattr(node, attr) is not None:
            attrs.append(f"{attr}={getattr(node, attr)}")
    if hasattr(node, "names") and node.names:
        attrs.append(f"names={node.names}")
    attr_str = f" ({', '.join(attrs)})" if attrs else ""
    print(f"{prefix}|-- {label}{attr_str}")
    for child in node.children:
        _print_ast(child, indent + 1)


def run_recursive_parser(source: str):
    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = RecursiveParser(lexer, sym_table, errors)

    print_header("RECURSIVE DESCENT PARSER OUTPUT")
    success, _ = parser.parse()
    print(f"  Result: {'[PASS]' if success else '[FAIL]'}")
    print_separator()
    print_symbol_table(sym_table)
    print_summary(errors)
    return success


def run_ll1_parser(source: str):
    lex_errors = ErrorHandler()
    lexer = Lexer(source, lex_errors)
    tokens = lexer.tokenize_all()

    errors = ErrorHandler()
    parser = LL1Parser(errors)
    parser.initialize_microjava_grammar()
    parser.compute_sets()

    print_header("LL(1) PREDICTIVE PARSER OUTPUT")
    print(f"  Non-terminals: {len(parser.non_terminals)}, Terminals: {len(parser.terminals)}")
    result = parser.parse(tokens)
    print()
    print(f"  Result: {'[PASS]' if result['success'] else '[FAIL]'}")
    print_trace(result)
    print_summary(errors)
    return result


def run_opp_parser(source: str):
    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = OperatorPrecedenceParser(lexer, sym_table, errors)

    print_header("OPERATOR PRECEDENCE PARSER OUTPUT")
    print("  Program structure: recursive descent")
    print("  Expressions: operator-precedence (two-stack)")
    print_separator()
    print_section("OPERATOR PRECEDENCE TABLE")
    for row in OperatorPrecedenceParser.get_precedence_table():
        print(f"    {row['operator']:<12}  precedence={row['precedence']}  associativity={row['associativity']}")

    success, _ = parser.parse()
    print()
    print(f"  Result: {'[PASS]' if success else '[FAIL]'}")
    print_separator()
    print_symbol_table(sym_table)
    traces = parser.get_expression_traces()
    if traces:
        print_section("EXPRESSION PARSING TRACE (two-stack)")
        print(f"  {'#':>3}  {'Operator Stack':<22} {'Operand Stack':<28} {'Lookahead':<12} {'Action'}")
        print_separator()
        for step in traces:
            print(
                f"  {step['step']:>3}  {step['operator_stack']:<22} "
                f"{step['operand_stack']:<28} {step['lookahead']:<12} {step['action']}"
            )
        print_separator()
    print_summary(errors)
    return success


def run_lr_parser(source: str):
    lex_errors = ErrorHandler()
    lexer = Lexer(source, lex_errors)
    tokens = lexer.tokenize_all()

    errors = ErrorHandler()
    parser = LRParser(errors)
    parser.initialize_microjava_grammar()
    parser.build_parsing_tables()

    print_header("LR PARSER (SLR(1)) OUTPUT")
    state_count = len(parser.states)
    print(f"  LR(0) states: {state_count}")
    result = parser.parse(tokens)
    print()
    print(f"  Result: {'[PASS]' if result['success'] else '[FAIL]'}")
    print_lr_trace(result)
    print_summary(errors)
    return result


def run_symbol_table(source: str):
    errors = ErrorHandler()
    lexer = Lexer(source, errors)
    sym_table = ScopeManager()
    parser = RecursiveParser(lexer, sym_table, errors)

    print_header("SYMBOL TABLE MANAGER OUTPUT")
    parser.parse()
    print_separator()
    print_symbol_table(sym_table)
    print_summary(errors)


def run_full_compilation(source: str):
    print_header("FULL COMPILATION PIPELINE")
    print("  Running ALL modules on the same source...\n")

    all_errors = []

    print_section("[1/4] LEXICAL ANALYZER")
    errors1 = ErrorHandler()
    lexer = Lexer(source, errors1)
    tokens = lexer.tokenize_all()
    print(f"  Tokens: {len(tokens)}  Errors: {len(errors1.get_errors())}")
    all_errors.extend(errors1.get_errors())

    print_section("[2/4] RECURSIVE DESCENT + SYMBOL TABLE")
    errors2 = ErrorHandler()
    lexer2 = Lexer(source, errors2)
    sym_table = ScopeManager()
    parser_rd = RecursiveParser(lexer2, sym_table, errors2)
    rd_success = parser_rd.parse()
    print(f"  Parsing: {'PASS' if rd_success else 'FAIL'}")
    print(f"  Symbols: {sym_table.total_entries}")
    print(f"  Scopes:  {sum(1 for s in sym_table.get_all_scopes_data() if s['entry_count'] > 0)}")
    all_errors.extend(errors2.get_errors())

    print_section("[3/4] LL(1) PREDICTIVE PARSER")
    errors3 = ErrorHandler()
    lexer3 = Lexer(source, ErrorHandler())
    tokens3 = lexer3.tokenize_all()
    parser_ll1 = LL1Parser(errors3)
    parser_ll1.initialize_microjava_grammar()
    parser_ll1.compute_sets()
    ll1_result = parser_ll1.parse(tokens3)
    print(f"  Parsing: {'PASS' if ll1_result['success'] else 'FAIL'}")
    all_errors.extend(errors3.get_errors())

    print_section("[4/4] LR PARSER (SLR(1))")
    errors4 = ErrorHandler()
    lexer4 = Lexer(source, ErrorHandler())
    tokens4 = lexer4.tokenize_all()
    parser_lr = LRParser(errors4)
    parser_lr.initialize_microjava_grammar()
    parser_lr.build_parsing_tables()
    lr_result = parser_lr.parse(tokens4)
    print(f"  Parsing: {'PASS' if lr_result['success'] else 'FAIL'}")
    all_errors.extend(errors4.get_errors())

    print()
    print_separator()
    print(f"  COMPILATION SUMMARY")
    print_separator()
    print(f"  Total errors: {len(all_errors)}")
    lexical = sum(1 for e in all_errors if e.type == ErrorType.LEXICAL)
    syntax = sum(1 for e in all_errors if e.type == ErrorType.SYNTAX)
    semantic = sum(1 for e in all_errors if e.type == ErrorType.SEMANTIC)
    print(f"    Lexical:  {lexical}")
    print(f"    Syntax:   {syntax}")
    print(f"    Semantic: {semantic}")
    if all_errors:
        print()
        print("  Error Details:")
        for e in all_errors:
            print(f"    [{e.type.value}] Line {e.line}, Col {e.col}: {e.message}")
    print_separator()


def print_grammar_info():
    errors = ErrorHandler()
    parser_ll1 = LL1Parser(errors)
    parser_ll1.initialize_microjava_grammar()
    parser_ll1.compute_sets()

    print_header("GRAMMAR & PARSING TABLES")

    print_section("MICROJAVA GRAMMAR")
    for lhs, prods in parser_ll1.grammar.items():
        for prod in prods:
            rhs = " ".join(prod) if prod != ["epsilon"] else "epsilon"
            print(f"    {lhs} -> {rhs}")

    print_first_sets(parser_ll1)
    print_follow_sets(parser_ll1)
    print_ll1_table(parser_ll1)

    errors_lr = ErrorHandler()
    parser_lr = LRParser(errors_lr)
    parser_lr.initialize_microjava_grammar()
    parser_lr.build_parsing_tables()

    print_lr_states(parser_lr)
    print_action_table(parser_lr)
    print_goto_table(parser_lr)


def print_first_sets(parser: LL1Parser):
    print_section("FIRST SETS")
    for nt in sorted(parser.non_terminals):
        fs = parser.first.get(nt, set())
        print(f"    FIRST({nt}) = {{ {', '.join(sorted(fs))} }}")


def print_follow_sets(parser: LL1Parser):
    print_section("FOLLOW SETS")
    for nt in sorted(parser.non_terminals):
        fs = parser.follow.get(nt, set())
        print(f"    FOLLOW({nt}) = {{ {', '.join(sorted(fs))} }}")


def print_ll1_table(parser: LL1Parser):
    print_section("LL(1) PARSING TABLE")
    table = parser.get_parse_table_data()
    if not table or not table.get("terminals"):
        print("    (empty)")
        return
    print(f"    {'NT/Terminal':<20}", end="")
    for t in table["terminals"]:
        print(f"{t:<15}", end="")
    print()
    print(f"    {'-'*20}", end="")
    for _ in table["terminals"]:
        print(f"{'-'*15}", end="")
    print()
    for row in table["rows"]:
        nt = row["non_terminal"]
        print(f"    {nt:<20}", end="")
        for t in table["terminals"]:
            val = row.get(t, "")
            print(f"{val if val else '--':<15}", end="")
        print()


def print_lr_states(parser: LRParser):
    print_section("LR(0) STATES")
    states = parser.get_states_info()
    for st in states:
        print(f"  State {st['id']}:")
        for item in st["items"]:
            print(f"    {item}")
        for sym, dest in st["transitions"].items():
            print(f"    --> {sym} -> State {dest}")
        print()


def print_action_table(parser: LRParser):
    print_section("ACTION TABLE (SLR(1))")
    table = parser.get_action_table_data()
    if not table or not table.get("terminals"):
        print("    (empty)")
        return
    print(f"    {'State':<8}", end="")
    for t in table["terminals"]:
        print(f"{t:<12}", end="")
    print()
    print(f"    {'-'*8}", end="")
    for _ in table["terminals"]:
        print(f"{'-'*12}", end="")
    print()
    for row in table["rows"]:
        print(f"    {row['state']:<8}", end="")
        for t in table["terminals"]:
            val = row.get(t, "")
            print(f"{val if val else '':<12}", end="")
        print()


def print_goto_table(parser: LRParser):
    print_section("GOTO TABLE (SLR(1))")
    table = parser.get_goto_table_data()
    if not table or not table.get("non_terminals"):
        print("    (empty)")
        return
    print(f"    {'State':<8}", end="")
    for nt in table["non_terminals"]:
        print(f"{nt:<15}", end="")
    print()
    print(f"    {'-'*8}", end="")
    for _ in table["non_terminals"]:
        print(f"{'-'*15}", end="")
    print()
    for row in table["rows"]:
        print(f"    {row['state']:<8}", end="")
        for nt in table["non_terminals"]:
            val = row.get(nt, "")
            print(f"{val if val else '':<15}", end="")
        print()


def print_trace(result: dict):
    trace = result.get("trace", [])
    if not trace:
        return
    print()
    print_separator()
    print(f"  {'Stack':<35} {'Input':<20} {'Action'}")
    print_separator()
    for step in trace:
        stack = step.get("stack", "")
        inp = step.get("input", "")
        action = step.get("action", "")
        print(f"  {stack:<35} {inp:<20} {action}")
    print_separator()


def print_lr_trace(result: dict):
    trace = result.get("trace", [])
    if not trace:
        return
    print()
    print_separator()
    print(f"  {'State Stack':<25} {'Sym Stack':<20} {'Input':<20} {'Action'}")
    print_separator()
    for step in trace:
        ss = step.get("state_stack", "")
        syms = step.get("sym_stack", "")
        inp = step.get("input", "")
        action = step.get("action", "")
        print(f"  {ss:<25} {syms:<20} {inp:<20} {action}")
    print_separator()


def print_symbol_table(sym_table: ScopeManager):
    scopes = sym_table.get_all_scopes_data()
    print(f"  Symbol Table (All Scopes):")
    if not scopes or all(s["entry_count"] == 0 for s in scopes):
        print("    (no symbols declared)")
        return
    for scope in scopes:
        if scope["entry_count"] == 0:
            continue
        print(f"\n    Scope {scope['scope_level']} ({scope['entry_count']} entries):")
        print(f"    {'#':<4} {'Name':<20} {'Kind':<12} {'Type':<12} {'Line':<6}")
        print(f"    {'-'*54}")
        for e in scope["entries"]:
            print(f"    {e['id']:<4} {e['name']:<20} {e['kind']:<12} {e['type']:<12} {e['line']:<6}")


def print_summary(errors: ErrorHandler):
    s = errors.get_summary()
    if s["total"] > 0:
        print(f"  Errors: {s['total']} (Lexical: {s['lexical']}, Syntax: {s['syntax']}, Semantic: {s['semantic']})")
        for e in errors.get_errors():
            msg = f"    [{e.type.value}] Line {e.line}, Col {e.col}: {e.message}"
            if e.recovery_action:
                msg += f" | Recovery: {e.recovery_action}"
            print(msg)
    else:
        print("  No errors.")


def interactive_mode():
    print_header("INTERACTIVE COMPILER MODE")
    print("  Type or paste MicroJava source code.")
    print("  Enter an empty line (just press Enter) to finish.")
    print("  Type 'exit' to quit.")
    print()

    lines = []
    print("  Enter source code (empty line to finish):")
    while True:
        try:
            line = input("  ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip() == "" and len(lines) > 0 and lines[-1].strip() == "":
            break
        if line.strip().lower() == "exit":
            return
        lines.append(line)

    source = "\n".join(lines)

    if not source.strip():
        print("  No source entered.")
        return

    print("\n  Choose module to run:")
    print("    1. Lexical Analyzer")
    print("    2. Recursive Descent Parser")
    print("    3. Abstract Syntax Tree (AST)")
    print("    4. LL(1) Predictive Parser")
    print("    5. LR Parser (SLR(1))")
    print("    6. Operator Precedence Parser")
    print("    7. Symbol Table Manager")
    print("    8. Full Compilation (All)")
    print("    9. Grammar Info & Tables")
    print("   10. All of the above")
    print()
    try:
        choice = input("  Enter choice (1-8): ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "6"

    if choice == "1":
        run_lexer(source)
    elif choice == "2":
        run_recursive_parser(source)
    elif choice == "3":
        run_ast(source)
    elif choice == "4":
        run_ll1_parser(source)
    elif choice == "5":
        run_lr_parser(source)
    elif choice == "6":
        run_opp_parser(source)
    elif choice == "7":
        run_symbol_table(source)
    elif choice == "8":
        run_full_compilation(source)
    elif choice == "9":
        print_grammar_info()
    elif choice == "10":
        run_lexer(source)
        run_recursive_parser(source)
        run_ast(source)
        run_ll1_parser(source)
        run_lr_parser(source)
        run_opp_parser(source)
        run_symbol_table(source)
    else:
        print("  Invalid choice.")


def main():
    if len(sys.argv) < 2:
        print()
        print(f"  MicroJava Compiler - CS-471L Compiler Construction Lab")
        print(f"  UET Lahore, Spring 2026")
        print()
        print("  Usage:")
        print(f"    python {os.path.basename(__file__)} <module> [source_file]")
        print()
        print("  Modules:")
        print("    lexer        Run lexical analyzer")
        print("    recursive    Run recursive descent parser")
        print("    ast          Show abstract syntax tree (AST)")
        print("    ll1          Run LL(1) predictive parser")
        print("    lr           Run LR parser (SLR(1))")
        print("    opp          Run operator precedence parser")
        print("    symbol_table Run symbol table manager")
        print("    full         Run full compilation pipeline")
        print("    grammar      Show grammar info & parsing tables")
        print("    interactive  Interactive mode (type code manually)")
        print()
        print("  Examples:")
        print(f"    python {os.path.basename(__file__)} lexer test\\test_simple.mj")
        print(f"    python {os.path.basename(__file__)} ast test_simple.mj")
        print(f"    python {os.path.basename(__file__)} ll1 test_simple.mj")
        print(f"    python {os.path.basename(__file__)} grammar")
        print(f"    python {os.path.basename(__file__)} interactive")
        print()
        return

    module = sys.argv[1].lower()

    if module == "interactive":
        interactive_mode()
        return

    if module == "grammar":
        print_grammar_info()
        return

    if len(sys.argv) < 3:
        print("[ERROR] Please provide a source file path.")
        print(f"  Usage: python {os.path.basename(__file__)} {module} <source_file>")
        print(f"  Or:    python {os.path.basename(__file__)} interactive")
        sys.exit(1)

    filepath = sys.argv[2]
    source = read_source(filepath)

    if module == "lexer":
        run_lexer(source)
    elif module == "recursive":
        run_recursive_parser(source)
    elif module == "ast":
        run_ast(source)
    elif module == "ll1":
        run_ll1_parser(source)
    elif module == "lr":
        run_lr_parser(source)
    elif module == "opp":
        run_opp_parser(source)
    elif module == "symbol_table":
        run_symbol_table(source)
    elif module == "full":
        run_full_compilation(source)
    else:
        print(f"[ERROR] Unknown module: '{module}'")
        print(f"  Available: lexer, recursive, ast, ll1, lr, opp, symbol_table, full, grammar, interactive")
        sys.exit(1)


if __name__ == "__main__":
    main()
