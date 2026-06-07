from __future__ import annotations

from .token import Token, TokenType
from .error_handler import ErrorHandler, ErrorType


class LRItem:
    def __init__(self, lhs: str, prod: list[str], dot_pos: int = 0):
        self.lhs = lhs
        self.prod = prod
        self.dot_pos = dot_pos

    def __lt__(self, other: "LRItem") -> bool:
        if self.lhs != other.lhs:
            return self.lhs < other.lhs
        if self.dot_pos != other.dot_pos:
            return self.dot_pos < other.dot_pos
        return self.prod < other.prod

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LRItem):
            return False
        return self.lhs == other.lhs and self.prod == other.prod and self.dot_pos == other.dot_pos

    def __hash__(self) -> int:
        return hash((self.lhs, tuple(self.prod), self.dot_pos))

    def __repr__(self) -> str:
        parts = []
        for i, s in enumerate(self.prod):
            if i == self.dot_pos:
                parts.append("·")
            parts.append(s)
        if self.dot_pos == len(self.prod):
            parts.append("·")
        return f"{self.lhs} -> {' '.join(parts)}"


class LRState:
    def __init__(self, id_: int, items: set[LRItem]):
        self.id = id_
        self.items = items
        self.transitions: dict[str, int] = {}


class LRParser:
    def __init__(self, errors: ErrorHandler):
        self.errors = errors
        self.grammar: dict[str, list[list[str]]] = {}
        self.non_terminals: set[str] = set()
        self.terminals: set[str] = set()
        self.start_symbol = "S'"
        self.augmented_start = "S'"

        self.action: dict[int, dict[str, str]] = {}
        self.goto_table: dict[int, dict[str, int]] = {}
        self.states: list[LRState] = []

        self.follow: dict[str, set[str]] = {}
        self.first_cache: dict[str, set[str]] = {}
        self.prod_numbers: dict[str, int] = {}
        self.prod_list: list[tuple[str, list[str]]] = []

    def _is_non_terminal(self, s: str) -> bool:
        return s in self.non_terminals

    def _is_terminal(self, s: str) -> bool:
        return s in self.terminals or s == "epsilon" or s == "$"

    @staticmethod
    def _set_to_str(s: set[str]) -> str:
        return "{ " + ", ".join(sorted(s)) + " }"

    def initialize_microjava_grammar(self):
        self.grammar = {
            "S'": [["Program"]],

            "Program": [
                [
                    "KW_PROGRAM",
                    "id",
                    "DeclSeq",
                    "SYM_LBRACE",
                    "MethodSeq",
                    "SYM_RBRACE"
                ]
            ],
            "DeclSeq": [
                ["Decl", "DeclSeq"],
                ["epsilon"]
            ],

            "Decl": [
                ["ConstDecl"],
                ["VarDecl"],
                ["ClassDecl"]
            ],

            "ConstDecl": [
                [
                    "KW_FINAL",
                    "Type",
                    "id",
                    "SYM_ASSIGN",
                    "ConstValue",
                    "SYM_SEMICOL"
                ]
            ],

            "ConstValue": [
                ["NUMBER"],
                ["CHAR_CONST"]
            ],

            "VarDecl": [
                [
                    "Type",
                    "id",
                    "VarTail",
                    "SYM_SEMICOL"
                ]
            ],

            "VarTail": [
                ["SYM_COMMA", "id", "VarTail"],
                ["epsilon"]
            ],

            "ClassDecl": [
                [
                    "KW_CLASS",
                    "id",
                    "SYM_LBRACE",
                    "ClassFields",
                    "SYM_RBRACE"
                ]
            ],

            "ClassFields": [
                ["VarDecl", "ClassFields"],
                ["epsilon"]
            ],

            "Type": [
                ["id", "ArrayOpt"]
            ],

            "ArrayOpt": [
                ["SYM_LBRACK", "SYM_RBRACK"],
                ["epsilon"]
            ],

            "MethodSeq": [
                ["MethodDecl", "MethodSeq"],
                ["epsilon"]
            ],

            "MethodDecl": [
                [
                    "MethodType",
                    "id",
                    "SYM_LPAREN",
                    "FormParsOpt",
                    "SYM_RPAREN",
                    "LocalDecls",
                    "Block"
                ]
            ],

            "MethodType": [
                ["KW_VOID"],
                ["Type"]
            ],

            "FormParsOpt": [
                ["FormPars"],
                ["epsilon"]
            ],

            "FormPars": [
                ["Type", "id", "FormParsTail"]
            ],

            "FormParsTail": [
                ["SYM_COMMA", "Type", "id", "FormParsTail"],
                ["epsilon"]
            ],

            "LocalDecls": [
                ["VarDecl", "LocalDecls"],
                ["epsilon"]
            ],

            "Block": [
                [
                    "SYM_LBRACE",
                    "StmtSeq",
                    "SYM_RBRACE"
                ]
            ],

            "StmtSeq": [
                ["Stmt", "StmtSeq"],
                ["epsilon"]
            ],

            "Stmt": [

                ["Designator", "StmtTail"],

                [
                    "KW_IF",
                    "SYM_LPAREN",
                    "Condition",
                    "SYM_RPAREN",
                    "Stmt",
                    "ElsePart"
                ],

                [
                    "KW_WHILE",
                    "SYM_LPAREN",
                    "Condition",
                    "SYM_RPAREN",
                    "Stmt"
                ],

                [
                    "KW_RETURN",
                    "ReturnTail"
                ],

                [
                    "KW_READ",
                    "SYM_LPAREN",
                    "Designator",
                    "SYM_RPAREN",
                    "SYM_SEMICOL"
                ],

                [
                    "KW_PRINT",
                    "SYM_LPAREN",
                    "Expr",
                    "PrintTail"
                ],

                ["Block"],

                ["SYM_SEMICOL"]
            ],

            "StmtTail": [
                [
                    "SYM_ASSIGN",
                    "Expr",
                    "SYM_SEMICOL"
                ],

                [
                    "ActPars",
                    "SYM_SEMICOL"
                ]
            ],

            "ElsePart": [
                ["KW_ELSE", "Stmt"],
                ["epsilon"]
            ],

            "ReturnTail": [
                ["Expr", "SYM_SEMICOL"],
                ["SYM_SEMICOL"]
            ],

            "PrintTail": [
                [
                    "SYM_COMMA",
                    "NUMBER",
                    "SYM_RPAREN",
                    "SYM_SEMICOL"
                ],

                [
                    "SYM_RPAREN",
                    "SYM_SEMICOL"
                ]
            ],
            "ActPars": [
                [
                    "SYM_LPAREN",
                    "ExprList",
                    "SYM_RPAREN"
                ]
            ],

            "ExprList": [
                ["Expr", "ExprListTail"],
                ["epsilon"]
            ],

            "ExprListTail": [
                [
                    "SYM_COMMA",
                    "Expr",
                    "ExprListTail"
                ],
                ["epsilon"]
            ],

            "Condition": [
                [
                    "Expr",
                    "Relop",
                    "Expr"
                ]
            ],

            "Relop": [
                ["OP_EQ"],
                ["OP_NEQ"],
                ["OP_GT"],
                ["OP_GE"],
                ["OP_LT"],
                ["OP_LE"]
            ],
            "Expr": [
                ["ExprPrefix", "Term", "ExprTail"]
            ],

            "ExprPrefix": [
                ["OP_MINUS"],
                ["epsilon"]
            ],

            "ExprTail": [
                ["OP_PLUS", "Term", "ExprTail"],
                ["OP_MINUS", "Term", "ExprTail"],
                ["epsilon"]
            ],

            "Term": [
                ["Factor", "TermTail"]
            ],

            "TermTail": [
                ["OP_MULT", "Factor", "TermTail"],
                ["OP_DIV", "Factor", "TermTail"],
                ["OP_MOD", "Factor", "TermTail"],
                ["epsilon"]
            ],
            "Factor": [

                ["NUMBER"],

                ["CHAR_CONST"],

                [
                    "Designator",
                    "FactorTail"
                ],

                [
                    "KW_NEW",
                    "id",
                    "NewTail"
                ],

                [
                    "SYM_LPAREN",
                    "Expr",
                    "SYM_RPAREN"
                ]
            ],

            "FactorTail": [
                ["ActPars"],
                ["epsilon"]
            ],

            "NewTail": [
                [
                    "SYM_LBRACK",
                    "Expr",
                    "SYM_RBRACK"
                ],
                ["epsilon"]
            ],
            "Designator": [
                [
                    "id",
                    "DesignatorTail"
                ]
            ],

            "DesignatorTail": [

                [
                    "SYM_DOT",
                    "id",
                    "DesignatorTail"
                ],

                [
                    "SYM_LBRACK",
                    "Expr",
                    "SYM_RBRACK",
                    "DesignatorTail"
                ],

                ["epsilon"]
            ]
        }

        self.non_terminals = set(self.grammar.keys())
        self.terminals = {
            "KW_PROGRAM",
            "KW_CLASS",
            "KW_FINAL",
            "KW_NEW",

            "KW_VOID",
            "KW_IF",
            "KW_ELSE",
            "KW_WHILE",
            "KW_RETURN",
            "KW_READ",
            "KW_PRINT",

            "id",
            "NUMBER",
            "CHAR_CONST",

            "SYM_LPAREN",
            "SYM_RPAREN",
            "SYM_LBRACK",
            "SYM_RBRACK",
            "SYM_LBRACE",
            "SYM_RBRACE",

            "SYM_ASSIGN",
            "SYM_SEMICOL",
            "SYM_COMMA",
            "SYM_DOT",

            "OP_EQ",
            "OP_NEQ",
            "OP_GT",
            "OP_GE",
            "OP_LT",
            "OP_LE",

            "OP_PLUS",
            "OP_MINUS",
            "OP_MULT",
            "OP_DIV",
            "OP_MOD",

            "$"
        }

        self.start_symbol = "S'"
        self.augmented_start = "S'"

    def _closure(self, items: set[LRItem]) -> set[LRItem]:
        result = set(items)
        queue = list(items)

        while queue:
            item = queue.pop(0)
            if item.dot_pos < len(item.prod):
                next_sym = item.prod[item.dot_pos]
                if self._is_non_terminal(next_sym):
                    for prod in self.grammar[next_sym]:
                        actual_prod = [] if prod == ["epsilon"] else prod
                        new_item = LRItem(next_sym, actual_prod, 0)
                        if new_item not in result:
                            result.add(new_item)
                            queue.append(new_item)
        return result

    def _goto(self, items: set[LRItem], X: str) -> set[LRItem]:
        result: set[LRItem] = set()
        for item in items:
            if item.dot_pos < len(item.prod) and item.prod[item.dot_pos] == X:
                new_item = LRItem(item.lhs, item.prod, item.dot_pos + 1)
                result.add(new_item)
        return self._closure(result)

    def _compute_first(self, X: str) -> set[str]:
        if X in self.first_cache:
            return self.first_cache[X]
        result: set[str] = set()
        if self._is_terminal(X):
            result.add(X)
            return result
        if X not in self.grammar:
            return result

        for prod in self.grammar[X]:
            if prod == ["epsilon"]:
                result.add("epsilon")
                continue
            all_eps = True
            for sym in prod:
                fs = self._compute_first(sym)
                for t in fs:
                    if t != "epsilon":
                        result.add(t)
                if "epsilon" not in fs:
                    all_eps = False
                    break
            if all_eps:
                result.add("epsilon")

        self.first_cache[X] = result
        return result

    def _compute_follow(self):
        self.follow.clear()
        for nt in self.non_terminals:
            self.follow[nt] = set()
        self.follow["Program"].add("$")

        changed = True
        while changed:
            changed = False
            for lhs, productions in self.grammar.items():
                for prod in productions:
                    if prod == ["epsilon"]:
                        continue
                    for i, B in enumerate(prod):
                        if not self._is_non_terminal(B):
                            continue
                        old_size = len(self.follow[B])
                        first_beta: set[str] = set()
                        all_eps = True
                        for j in range(i + 1, len(prod)):
                            fs = self._compute_first(prod[j])
                            for t in fs:
                                if t != "epsilon":
                                    first_beta.add(t)
                            if "epsilon" not in fs:
                                all_eps = False
                                break
                        for t in first_beta:
                            self.follow[B].add(t)
                        if i == len(prod) - 1 or all_eps:
                            for t in self.follow[lhs]:
                                self.follow[B].add(t)
                        if len(self.follow[B]) > old_size:
                            changed = True

    def build_parsing_tables(self):
        self.states.clear()
        self.action.clear()
        self.goto_table.clear()
        self.prod_numbers.clear()
        self.prod_list.clear()
        self.follow.clear()
        self.first_cache.clear()

        pn = 0
        for lhs, productions in self.grammar.items():
            for prod in productions:
                if prod == ["epsilon"]:
                    key = f"{lhs}->epsilon"
                    self.prod_numbers[key] = pn
                    self.prod_list.append((lhs, []))
                else:
                    key = f"{lhs}->" + " ".join(prod) + " "
                    self.prod_numbers[key] = pn
                    self.prod_list.append((lhs, prod))
                pn += 1

        start_item = LRItem("S'", ["Program"], 0)
        start_closure = self._closure({start_item})

        initial = LRState(0, start_closure)
        self.states.append(initial)

        queue = [0]
        all_symbols = self.non_terminals | self.terminals

        while queue:
            sid = queue.pop(0)
            next_symbols: set[str] = set()
            for item in self.states[sid].items:
                if item.dot_pos < len(item.prod):
                    next_symbols.add(item.prod[item.dot_pos])

            for X in next_symbols:
                next_items = self._goto(self.states[sid].items, X)
                if not next_items:
                    continue

                existing_id = -1
                for i, state in enumerate(self.states):
                    if state.items == next_items:
                        existing_id = i
                        break

                if existing_id == -1:
                    new_state = LRState(len(self.states), next_items)
                    self.states.append(new_state)
                    queue.append(new_state.id)
                    self.states[sid].transitions[X] = new_state.id
                else:
                    self.states[sid].transitions[X] = existing_id

        self._compute_follow()

        for state in self.states:
            s = state.id
            if s not in self.action:
                self.action[s] = {}
            if s not in self.goto_table:
                self.goto_table[s] = {}

            for symbol, next_state in state.transitions.items():
                if symbol == "epsilon":
                    continue
                if symbol in self.terminals:
                    self.action[s][symbol] = f"s{next_state}"
                elif symbol in self.non_terminals and symbol != "S'":
                    self.goto_table[s][symbol] = next_state

            for item in state.items:
                if item.dot_pos == len(item.prod):
                    if item.lhs == "S'":
                        self.action[s]["$"] = "acc"
                    else:
                        prod_key = f"{item.lhs}->" + " ".join(item.prod) + " "
                        if not item.prod:
                            prod_key = f"{item.lhs}->epsilon"
                        prod_num = self.prod_numbers.get(prod_key, -1)
                        if prod_num >= 0:
                            for t in self.follow.get(item.lhs, set()):
                                if t not in self.action[s]:
                                    self.action[s][t] = f"r{prod_num}"

    def _convert_tokens(self, tokens: list[Token]) -> list[str]:
        result = []
        for t in tokens:
            if t.type == TokenType.COMMENT:
                continue
            if t.type == TokenType.EOF:
                result.append("$")
                break
            result.append(t.to_grammar_symbol())
        if not result or result[-1] != "$":
            result.append("$")
        return result

    def _token_position(self, tokens: list[Token], ip: int) -> tuple[int, int]:
        idx = min(ip, max(0, len(tokens) - 1))
        if tokens:
            return tokens[idx].line, tokens[idx].col
        return 0, 0

    def _error_recovery(self, state_stack: list[int], sym_stack: list[str], a: str) -> bool:
        """Panic-mode recovery using error entries: pop until a shift on a is possible."""
        while len(state_stack) > 1:
            state_stack.pop()
            if sym_stack:
                sym_stack.pop()
            top = state_stack[-1]
            if top in self.action and a in self.action[top] and self.action[top][a].startswith("s"):
                return True
        return False

    def parse(self, tokens: list[Token]) -> dict:
        input_tokens = self._convert_tokens(tokens)
        state_stack = [0]
        sym_stack: list[str] = []
        ip = 0
        trace = []
        has_error = False
        panic_mode = False

        while True:
            state = state_stack[-1]
            a = input_tokens[ip] if ip < len(input_tokens) else "$"

            state_str = " ".join(str(s) for s in state_stack)
            sym_str = " ".join(sym_stack) if sym_stack else "$"
            input_str = " ".join(input_tokens[ip:]) if ip < len(input_tokens) else "$"

            step = {"state_stack": state_str, "sym_stack": sym_str, "input": input_str, "action": ""}

            if state not in self.action or a not in self.action.get(state, {}):
                line, col = self._token_position(tokens, ip)
                err_msg = f"LR: No action for state {state} with {a}"
                if not panic_mode:
                    self.errors.report(
                        ErrorType.SYNTAX,
                        err_msg,
                        line,
                        col,
                        recovery_action="error entry: pop stack until shift possible",
                    )
                    panic_mode = True
                has_error = True
                step["action"] = f"ERROR - {err_msg} (recovery)"
                trace.append(step)
                if not self._error_recovery(state_stack, sym_stack, a):
                    ip += 1
                panic_mode = False
                if a == "$" and ip >= len(input_tokens):
                    break
                continue

            act = self.action[state][a]

            if act == "acc":
                step["action"] = "ACCEPT"
                trace.append(step)
                return {
                    "success": not has_error,
                    "trace": trace,
                }
            elif act[0] == "s":
                next_state = int(act[1:])
                state_stack.append(next_state)
                sym_stack.append(a)
                ip += 1
                step["action"] = f"Shift to {next_state}"
                trace.append(step)
            elif act[0] == "r":
                prod_num = int(act[1:])
                lhs, rhs = self.prod_list[prod_num]

                for _ in range(len(rhs)):
                    if state_stack:
                        state_stack.pop()
                    if sym_stack:
                        sym_stack.pop()

                sym_stack.append(lhs)
                top_state = state_stack[-1]
                if top_state in self.goto_table and lhs in self.goto_table[top_state]:
                    state_stack.append(self.goto_table[top_state][lhs])
                else:
                    err_msg = f"LR: No goto entry for state {top_state} with {lhs}"
                    self.errors.report(ErrorType.SYNTAX, err_msg, 0, 0)
                    has_error = True
                    break

                rhs_str = "epsilon" if not rhs else " ".join(rhs)
                step["action"] = f"Reduce {lhs} -> {rhs_str}"
                trace.append(step)
            else:
                self.errors.report(ErrorType.SYNTAX, f"LR: Invalid action {act}", 0, 0)
                has_error = True
                break

        return {
            "success": not has_error,
            "trace": trace,
        }

    def get_states_info(self) -> list[dict]:
        states_info = []
        for state in self.states:
            items_str = [str(item) for item in state.items]
            trans_str = {k: str(v) for k, v in state.transitions.items()}
            states_info.append({
                "id": state.id,
                "items": items_str,
                "transitions": trans_str,
            })
        return states_info

    def get_action_table_data(self) -> dict:
        used_terminals: set[str] = set()
        for s_actions in self.action.values():
            for t in s_actions:
                used_terminals.add(t)

        used_terminals = sorted(used_terminals)
        rows = []
        for s in sorted(self.action.keys()):
            row = {"state": s}
            for t in used_terminals:
                row[t] = self.action[s].get(t, "")
            rows.append(row)

        return {"terminals": used_terminals, "rows": rows}

    def get_goto_table_data(self) -> dict:
        used_nt: set[str] = set()
        for s_gotos in self.goto_table.values():
            for nt in s_gotos:
                used_nt.add(nt)

        used_nt = sorted(used_nt)
        rows = []
        for s in sorted(self.goto_table.keys()):
            row = {"state": s}
            for nt in used_nt:
                row[nt] = self.goto_table[s].get(nt, "")
            rows.append(row)

        return {"non_terminals": used_nt, "rows": rows}
