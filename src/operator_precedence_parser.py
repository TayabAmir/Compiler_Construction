from __future__ import annotations

from .token import Token, TokenType
from .lexer import Lexer
from .symbol_table import ScopeManager
from .error_handler import ErrorHandler, ErrorType
from .recursive_parser import RecursiveParser
from .ast import ASTNode, ASTNodeType, make_node


# MicroJava arithmetic expression precedence (higher number = tighter binding)
PRECEDENCE = {
    "U_MINUS": (4, "right"),
    TokenType.OP_MULT: (3, "left"),
    TokenType.OP_DIV: (3, "left"),
    TokenType.OP_MOD: (3, "left"),
    TokenType.OP_PLUS: (2, "left"),
    TokenType.OP_MINUS: (2, "left"),
}

EXPR_END = {
    TokenType.SYM_SEMICOL,
    TokenType.SYM_COMMA,
    TokenType.SYM_RPAREN,
    TokenType.SYM_RBRACE,
    TokenType.OP_EQ,
    TokenType.OP_NEQ,
    TokenType.OP_GT,
    TokenType.OP_GE,
    TokenType.OP_LT,
    TokenType.OP_LE,
    TokenType.EOF,
}

OPERATOR_TOKENS = {
    TokenType.OP_PLUS,
    TokenType.OP_MINUS,
    TokenType.OP_MULT,
    TokenType.OP_DIV,
    TokenType.OP_MOD,
}


class OperatorPrecedenceParser(RecursiveParser):
    """
    Hybrid parser: recursive descent for program structure,
    operator-precedence (two-stack) parsing for expressions.
    """

    def __init__(self, lexer: Lexer, sym_table: ScopeManager, errors: ErrorHandler):
        super().__init__(lexer, sym_table, errors)
        self.expr_traces: list[dict] = []
        self._trace_counter = 0

    def _op_key(self, op: TokenType | str) -> str:
        if op == "U_MINUS":
            return "- (unary)"
        if isinstance(op, TokenType):
            return op.name.replace("OP_", "")
        return str(op)

    def _precedence(self, op: TokenType | str) -> int:
        return PRECEDENCE.get(op, (0, "left"))[0]

    def _associativity(self, op: TokenType | str) -> str:
        return PRECEDENCE.get(op, (0, "left"))[1]

    def _should_reduce(self, stack_op: TokenType | str, incoming: TokenType | str | None) -> bool:
        if incoming is None or incoming == "$":
            return stack_op != "$"
        if stack_op == "$":
            return False
        left_prec = self._precedence(stack_op)
        right_prec = self._precedence(incoming)
        if left_prec > right_prec:
            return True
        if left_prec == right_prec:
            return self._associativity(stack_op) == "left"
        return False

    def _at_expr_boundary(self) -> bool:
        return self.lookahead.type in EXPR_END

    def _peek_expr_operator(self) -> TokenType | str | None:
        # Unary minus is handled inside _read_operand; here '-' is always binary.
        if self.lookahead.type in OPERATOR_TOKENS:
            return self.lookahead.type
        return None

    def _trace_step(
        self,
        op_stack: list,
        operand_stack: list,
        action: str,
        context: str = "",
    ):
        self._trace_counter += 1
        self.expr_traces.append({
            "step": self._trace_counter,
            "context": context,
            "operator_stack": " ".join(self._op_key(o) for o in op_stack),
            "operand_stack": self._format_operand_stack(operand_stack),
            "lookahead": self.lookahead.lexeme if self.lookahead else "",
            "action": action,
        })

    @staticmethod
    def _format_operand_stack(stack: list[ASTNode]) -> str:
        labels = []
        for node in stack:
            if node.node_type == ASTNodeType.NUMBER_LITERAL:
                labels.append(node.value)
            elif node.node_type == ASTNodeType.CHAR_LITERAL:
                labels.append(node.value)
            elif node.node_type == ASTNodeType.DESIGNATOR:
                labels.append(node.name or "desig")
            elif node.node_type in (ASTNodeType.BINARY_OP, ASTNodeType.UNARY_OP):
                labels.append(f"({node.op})")
            elif node.node_type == ASTNodeType.NEW_EXPR:
                labels.append(f"new {node.name}")
            else:
                labels.append(node.node_type.value)
        return " ".join(labels) if labels else "(empty)"

    def _read_operand(self, context: str) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col

        if self.lookahead.type == TokenType.OP_MINUS:
            self.match(TokenType.OP_MINUS, "'-'")
            inner = self._read_operand(context)
            node = make_node(ASTNodeType.UNARY_OP, op="-", line=line, col=col)
            if inner:
                node.add_child(inner)
            return node

        if self.lookahead.type == TokenType.NUMBER:
            value = self.lookahead.lexeme
            self.match(TokenType.NUMBER, "number")
            return make_node(ASTNodeType.NUMBER_LITERAL, value=value, line=line, col=col)

        if self.lookahead.type == TokenType.CHAR_CONST:
            value = self.lookahead.lexeme
            self.match(TokenType.CHAR_CONST, "char constant")
            return make_node(ASTNodeType.CHAR_LITERAL, value=value, line=line, col=col)

        if self.lookahead.type == TokenType.IDENTIFIER:
            desig = self._designator()
            if self.lookahead.type == TokenType.SYM_LPAREN:
                self._act_pars()
                return make_node(ASTNodeType.CALL_STMT, children=[desig] if desig else [])
            return desig

        if self.lookahead.type == TokenType.KW_NEW:
            self.match(TokenType.KW_NEW, "'new'")
            name = self.lookahead.lexeme
            self.match(TokenType.IDENTIFIER, "identifier")
            size_expr = None
            if self.lookahead.type == TokenType.SYM_LBRACK:
                self.match(TokenType.SYM_LBRACK, "'['")
                size_expr = self._parse_expr_opp(f"new {name}[...]")
                self.match(TokenType.SYM_RBRACK, "']'")
            children = [size_expr] if size_expr else []
            return make_node(ASTNodeType.NEW_EXPR, name=name, line=line, col=col, children=children)

        if self.lookahead.type == TokenType.SYM_LPAREN:
            self.match(TokenType.SYM_LPAREN, "'('")
            expr = self._parse_expr_opp(f"{context} (paren)")
            self.match(TokenType.SYM_RPAREN, "')'")
            return expr

        self.has_error = True
        self.errors.report(
            ErrorType.SYNTAX,
            f"OPP: expected operand, found '{self.lookahead.type_to_string()}'",
            self.lookahead.line,
            self.lookahead.col,
        )
        return None

    def _reduce_top(self, op_stack: list, operand_stack: list, context: str):
        op = op_stack.pop()
        if op == "U_MINUS":
            if not operand_stack:
                return
            operand = operand_stack.pop()
            node = make_node(ASTNodeType.UNARY_OP, op="-", line=operand.line, col=operand.col)
            node.add_child(operand)
            operand_stack.append(node)
            self._trace_step(op_stack, operand_stack, "REDUCE unary -", context)
            return

        if len(operand_stack) < 2:
            return
        right = operand_stack.pop()
        left = operand_stack.pop()
        op_lexeme = {
            TokenType.OP_PLUS: "+",
            TokenType.OP_MINUS: "-",
            TokenType.OP_MULT: "*",
            TokenType.OP_DIV: "/",
            TokenType.OP_MOD: "%",
        }.get(op, "?")
        node = make_node(ASTNodeType.BINARY_OP, op=op_lexeme, line=left.line, col=left.col)
        node.add_child(left)
        node.add_child(right)
        operand_stack.append(node)
        self._trace_step(op_stack, operand_stack, f"REDUCE {op_lexeme}", context)

    def _parse_expr_opp(self, context: str = "expr") -> ASTNode | None:
        op_stack: list[TokenType | str] = ["$"]
        operand_stack: list[ASTNode] = []

        operand = self._read_operand(context)
        if operand:
            operand_stack.append(operand)
        self._trace_step(op_stack, operand_stack, "SHIFT operand", context)

        while True:
            if self._at_expr_boundary():
                while op_stack[-1] != "$":
                    self._reduce_top(op_stack, operand_stack, context)
                break

            incoming = self._peek_expr_operator()
            if incoming is None:
                self.has_error = True
                self.errors.report(
                    ErrorType.SYNTAX,
                    f"OPP: expected operator or end of expression, found '{self.lookahead.type_to_string()}'",
                    self.lookahead.line,
                    self.lookahead.col,
                )
                break

            while self._should_reduce(op_stack[-1], incoming):
                self._reduce_top(op_stack, operand_stack, context)

            op_stack.append(incoming)
            if incoming == "U_MINUS":
                self.match(TokenType.OP_MINUS, "'-'")
            else:
                self.match(incoming, self.lookahead.lexeme)
            self._trace_step(op_stack, operand_stack, f"SHIFT {self._op_key(incoming)}", context)

            operand = self._read_operand(context)
            if operand:
                operand_stack.append(operand)
                self._trace_step(op_stack, operand_stack, "SHIFT operand", context)

        return operand_stack[-1] if operand_stack else None

    def _expr(self) -> ASTNode | None:
        return self._parse_expr_opp("statement expr")

    def parse(self) -> tuple[bool, ASTNode | None]:
        self.expr_traces.clear()
        self._trace_counter = 0
        return super().parse()

    @staticmethod
    def get_precedence_table() -> list[dict]:
        rows = []
        for op, (prec, assoc) in sorted(PRECEDENCE.items(), key=lambda x: -x[1][0]):
            key = op if isinstance(op, str) else op.name.replace("OP_", "")
            rows.append({
                "operator": key if key != "U_MINUS" else "- (unary)",
                "precedence": prec,
                "associativity": assoc,
            })
        return rows

    def get_expression_traces(self) -> list[dict]:
        return self.expr_traces
