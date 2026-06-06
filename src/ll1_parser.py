from __future__ import annotations

from .token import Token, TokenType
from .error_handler import ErrorHandler, ErrorType


class LL1Parser:
    def __init__(self, errors: ErrorHandler):
        self.errors = errors
        self.grammar: dict[str, list[list[str]]] = {}
        self.non_terminals: set[str] = set()
        self.terminals: set[str] = set()
        self.start_symbol = "Program"
        self.first: dict[str, set[str]] = {}
        self.follow: dict[str, set[str]] = {}
        self.parse_table: dict[tuple[str, str], list[str]] = {}

    def _is_non_terminal(self, s: str) -> bool:
        return s in self.non_terminals

    def _is_terminal(self, s: str) -> bool:
        return s in self.terminals or s == "epsilon" or s == "$"

    @staticmethod
    def _vec_to_str(v: list[str]) -> str:
        if not v:
            return "[]"
        if v == ["epsilon"]:
            return "[eps]"
        parts = []
        for s in v:
            parts.append("eps" if s == "epsilon" else s)
        return "[" + " ".join(parts) + "]"

    @staticmethod
    def _set_to_str(s: set[str]) -> str:
        return "{ " + ", ".join(sorted(s)) + " }"

    def initialize_microjava_grammar(self):
        self.grammar = {
            "Program": [["KW_PROGRAM", "id", "Declarations", "SYM_LBRACE", "MethodList", "SYM_RBRACE"]],
            "Declarations": [["ConstDecl", "Declarations"], ["VarDecl", "Declarations"], ["ClassDecl", "Declarations"], ["epsilon"]],
            "ConstDecl": [["KW_FINAL", "Type", "id", "SYM_ASSIGN", "ConstVal", "SYM_SEMICOL"]],
            "ConstVal": [["NUMBER"], ["CHAR_CONST"]],
            "VarDecl": [["Type", "id", "VarDeclTail"]],
            "VarDeclTail": [["SYM_COMMA", "id", "VarDeclTail"], ["SYM_SEMICOL"]],
            "ClassDecl": [["KW_CLASS", "id", "SYM_LBRACE", "VarDeclList", "SYM_RBRACE"]],
            "VarDeclList": [["VarDecl", "VarDeclList"], ["epsilon"]],
            "MethodList": [["MethodDecl", "MethodList"], ["epsilon"]],
            "MethodDecl": [["MethodHeader", "id", "SYM_LPAREN", "FormPars", "SYM_RPAREN", "VarDeclList", "Block"]],
            "MethodHeader": [["Type"], ["KW_VOID"]],
            "FormPars": [["Type", "id", "FormParsTail"], ["epsilon"]],
            "FormParsTail": [["SYM_COMMA", "Type", "id", "FormParsTail"], ["epsilon"]],
            "Type": [["id", "ArrayOpt"]],
            "ArrayOpt": [["SYM_LBRACK", "SYM_RBRACK"], ["epsilon"]],
            "Block": [["SYM_LBRACE", "StatementList", "SYM_RBRACE"]],
            "StatementList": [["Statement", "StatementList"], ["epsilon"]],
            "Statement": [["Designator", "StmtTail"], ["IfStmt"], ["WhileStmt"], ["ReturnStmt"], ["ReadStmt"], ["PrintStmt"], ["Block"], ["SYM_SEMICOL"]],
            "StmtTail": [["SYM_ASSIGN", "Expr", "SYM_SEMICOL"], ["ActPars", "SYM_SEMICOL"]],
            "IfStmt": [["KW_IF", "SYM_LPAREN", "Condition", "SYM_RPAREN", "Statement", "ElseOpt"]],
            "ElseOpt": [["KW_ELSE", "Statement"], ["epsilon"]],
            "WhileStmt": [["KW_WHILE", "SYM_LPAREN", "Condition", "SYM_RPAREN", "Statement"]],
            "ReturnStmt": [["KW_RETURN", "ReturnTail"]],
            "ReturnTail": [["Expr", "SYM_SEMICOL"], ["SYM_SEMICOL"]],
            "ReadStmt": [["KW_READ", "SYM_LPAREN", "Designator", "SYM_RPAREN", "SYM_SEMICOL"]],
            "PrintStmt": [["KW_PRINT", "SYM_LPAREN", "Expr", "PrintTail"]],
            "PrintTail": [["SYM_COMMA", "NUMBER", "SYM_RPAREN", "SYM_SEMICOL"], ["SYM_RPAREN", "SYM_SEMICOL"]],
            "Designator": [["id", "DesignatorTail"]],
            "DesignatorTail": [["SYM_DOT", "id", "DesignatorTail"], ["SYM_LBRACK", "Expr", "SYM_RBRACK", "DesignatorTail"], ["epsilon"]],
            "ActPars": [["SYM_LPAREN", "ExprList", "SYM_RPAREN"]],
            "ExprList": [["Expr", "ExprListTail"], ["epsilon"]],
            "ExprListTail": [["SYM_COMMA", "Expr", "ExprListTail"], ["epsilon"]],
            "Condition": [["Expr", "Relop", "Expr"]],
            "Relop": [["OP_EQ"], ["OP_NEQ"], ["OP_GT"], ["OP_GE"], ["OP_LT"], ["OP_LE"]],
            "Expr": [["ExprPrime"]],
            "ExprPrime": [["OP_MINUS", "Term", "ExprAddTail"], ["Term", "ExprAddTail"]],
            "ExprAddTail": [["OP_PLUS", "Term", "ExprAddTail"], ["OP_MINUS", "Term", "ExprAddTail"], ["epsilon"]],
            "Term": [["Factor", "TermMulTail"]],
            "TermMulTail": [["OP_MULT", "Factor", "TermMulTail"], ["OP_DIV", "Factor", "TermMulTail"], ["OP_MOD", "Factor", "TermMulTail"], ["epsilon"]],
            "Factor": [["KW_NEW", "id", "NewArrayOpt"], ["NUMBER"], ["CHAR_CONST"], ["SYM_LPAREN", "Expr", "SYM_RPAREN"], ["Designator", "FactorCallOpt"]],
            "FactorCallOpt": [["ActPars"], ["epsilon"]],
            "NewArrayOpt": [["SYM_LBRACK", "Expr", "SYM_RBRACK"], ["epsilon"]],
        }

        self.non_terminals = set(self.grammar.keys())

        self.terminals = {
            "KW_PROGRAM", "id", "SYM_LBRACE", "SYM_RBRACE", "KW_FINAL", "SYM_ASSIGN",
            "NUMBER", "CHAR_CONST", "SYM_SEMICOL", "SYM_COMMA", "KW_CLASS",
            "KW_VOID", "SYM_LPAREN", "SYM_RPAREN", "SYM_LBRACK", "SYM_RBRACK",
            "SYM_DOT", "KW_IF", "KW_ELSE", "KW_WHILE", "KW_RETURN", "KW_READ",
            "KW_PRINT", "OP_EQ", "OP_NEQ", "OP_GT", "OP_GE", "OP_LT", "OP_LE",
            "OP_PLUS", "OP_MINUS", "OP_MULT", "OP_DIV", "OP_MOD", "KW_NEW", "$",
        }

        self.start_symbol = "Program"

    def _compute_first(self, X: str) -> set[str]:
        if X in self.first:
            return self.first[X]
        result: set[str] = set()

        if self._is_terminal(X):
            result.add(X)
            return result

        if X not in self.grammar:
            return result

        for production in self.grammar[X]:
            if production == ["epsilon"]:
                result.add("epsilon")
                continue
            all_have_epsilon = True
            for symbol in production:
                first_of_symbol = self._compute_first(symbol)
                for t in first_of_symbol:
                    if t != "epsilon":
                        result.add(t)
                if "epsilon" not in first_of_symbol:
                    all_have_epsilon = False
                    break
            if all_have_epsilon:
                result.add("epsilon")

        self.first[X] = result
        return result

    def _compute_follow(self):
        self.follow[self.start_symbol].add("$")
        changed = True
        while changed:
            changed = False
            for lhs, productions in self.grammar.items():
                for production in productions:
                    if production == ["epsilon"]:
                        continue
                    for i, B in enumerate(production):
                        if not self._is_non_terminal(B):
                            continue
                        old_size = len(self.follow[B])
                        first_beta: set[str] = set()
                        all_have_epsilon = True
                        for j in range(i + 1, len(production)):
                            first_of_symbol = self._compute_first(production[j])
                            for t in first_of_symbol:
                                if t != "epsilon":
                                    first_beta.add(t)
                            if "epsilon" not in first_of_symbol:
                                all_have_epsilon = False
                                break
                        for t in first_beta:
                            self.follow[B].add(t)
                        if i == len(production) - 1 or all_have_epsilon:
                            for t in self.follow[lhs]:
                                self.follow[B].add(t)
                        if len(self.follow[B]) > old_size:
                            changed = True

    def _build_parsing_table(self):
        self.parse_table.clear()
        for lhs, productions in self.grammar.items():
            for production in productions:
                first_set: set[str] = set()
                has_epsilon = False

                if production == ["epsilon"]:
                    has_epsilon = True
                else:
                    all_have_epsilon = True
                    for symbol in production:
                        first_of_symbol = self._compute_first(symbol)
                        for t in first_of_symbol:
                            if t != "epsilon":
                                first_set.add(t)
                        if "epsilon" not in first_of_symbol:
                            all_have_epsilon = False
                            break
                    if all_have_epsilon:
                        has_epsilon = True

                for terminal in first_set:
                    self.parse_table[(lhs, terminal)] = production

                if has_epsilon:
                    for terminal in self.follow[lhs]:
                        if (lhs, terminal) not in self.parse_table:
                            self.parse_table[(lhs, terminal)] = production

    def compute_sets(self):
        self.first.clear()
        self.follow.clear()
        for nt in self.non_terminals:
            self._compute_first(nt)
            self.follow[nt] = set()
        self._compute_follow()
        self._build_parsing_table()

    def _convert_tokens(self, tokens: list[Token]) -> list[str]:
        result = []
        for t in tokens:
            if t.type == TokenType.EOF:
                result.append("$")
                break
            result.append(t.to_grammar_symbol())
        if not result or result[-1] != "$":
            result.append("$")
        return result

    def parse(self, tokens: list[Token]) -> dict:
        input_tokens = self._convert_tokens(tokens)
        stack = ["$", self.start_symbol]
        ip = 0
        trace = []
        success = True

        while stack:
            stack_str = "[" + " ".join(reversed([x for x in stack if x != "$"][::-1] if len([x for x in stack if x != "$"]) > 0 else []))
            actual_stack = [x for x in stack if x != "$"]
            stack_str = " ".join(actual_stack) if actual_stack else "$"
            # Rebuild properly
            temp = list(stack)
            stack_str = " ".join(temp)

            input_str = " ".join(input_tokens[ip:]) if ip < len(input_tokens) else "$"

            X = stack.pop()
            a = input_tokens[ip] if ip < len(input_tokens) else "$"

            step = {"stack": stack_str, "input": input_str, "action": ""}

            if X == "$" and a == "$":
                step["action"] = "ACCEPT"
                trace.append(step)
                success = True
                break
            elif X == a:
                step["action"] = f"Match {X}"
                trace.append(step)
                ip += 1
            elif self._is_terminal(X):
                step["action"] = f"ERROR: Expected {X}, found {a}"
                trace.append(step)
                self.errors.report(ErrorType.SYNTAX, f"LL(1): Expected {X}, found {a}", 0, 0)
                success = False
                while ip < len(input_tokens) and input_tokens[ip] != X:
                    ip += 1
            elif self._is_non_terminal(X):
                key = (X, a)
                if key in self.parse_table:
                    production = self.parse_table[key]
                    step["action"] = f"{X} -> {self._vec_to_str(production)}"
                    trace.append(step)
                    if not (production == ["epsilon"]):
                        for sym in reversed(production):
                            stack.append(sym)
                else:
                    step["action"] = f"ERROR: No production for M[{X}, {a}]"
                    trace.append(step)
                    self.errors.report(ErrorType.SYNTAX, f"LL(1): No production for {X} with {a}", 0, 0)
                    success = False
            else:
                step["action"] = f"ERROR: Unexpected symbol {X}"
                trace.append(step)
                success = False

        return {
            "success": success,
            "trace": trace,
        }

    def get_first_sets(self) -> dict[str, str]:
        return {nt: self._set_to_str(self.first.get(nt, set())) for nt in sorted(self.non_terminals)}

    def get_follow_sets(self) -> dict[str, str]:
        return {nt: self._set_to_str(self.follow.get(nt, set())) for nt in sorted(self.non_terminals)}

    def get_parse_table_data(self) -> list[dict]:
        rows = []
        used_terminals = sorted({t for (_, t) in self.parse_table})
        for nt in sorted(self.non_terminals):
            row = {"non_terminal": nt}
            for t in used_terminals:
                key = (nt, t)
                if key in self.parse_table:
                    prod = self.parse_table[key]
                    row[t] = f"{nt} -> {self._vec_to_str(prod)}"
                else:
                    row[t] = "--"
            rows.append(row)
        return {"terminals": used_terminals, "rows": rows}
