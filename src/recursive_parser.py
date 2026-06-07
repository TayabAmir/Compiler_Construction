from __future__ import annotations

from .token import Token, TokenType
from .lexer import Lexer
from .symbol_table import (
    ScopeManager,
    IdentifierKind,
    DataType,
    type_string_to_data_type,
    kind_for_declaration,
)
from .error_handler import ErrorHandler, ErrorType
from .ast import ASTNode, ASTNodeType, make_node


PHRASE_SYNC = {
    "statement": {
        TokenType.SYM_SEMICOL, TokenType.SYM_RBRACE, TokenType.KW_ELSE, TokenType.EOF,
    },
    "block": {TokenType.SYM_RBRACE, TokenType.EOF},
    "declaration": {TokenType.SYM_SEMICOL, TokenType.EOF},
    "method": {
        TokenType.SYM_LBRACE, TokenType.KW_VOID, TokenType.IDENTIFIER,
        TokenType.SYM_RBRACE, TokenType.EOF,
    },
    "expression": {
        TokenType.SYM_RPAREN, TokenType.SYM_SEMICOL, TokenType.SYM_COMMA,
        TokenType.SYM_RBRACE, TokenType.EOF,
    },
}


class RecursiveParser:
    def __init__(self, lexer: Lexer, sym_table: ScopeManager, errors: ErrorHandler):
        self.lexer = lexer
        self.sym_table = sym_table
        self.errors = errors
        self.lookahead: Token | None = None
        self.has_error = False
        self.main_found = False
        self.main_param_count = 0

    def next_token(self):
        self.lookahead = self.lexer.get_next_token()

    def _recover_phrase(self, phrase: str, *, consume_semicolon: bool = False):
        sync = PHRASE_SYNC.get(phrase, PHRASE_SYNC["statement"])
        while self.lookahead.type not in sync:
            self.next_token()
        if consume_semicolon and self.lookahead.type == TokenType.SYM_SEMICOL:
            self.next_token()

    def _panic_sync(self):
        sync_set = {TokenType.EOF, TokenType.SYM_SEMICOL, TokenType.SYM_RBRACE, TokenType.KW_PROGRAM}
        while self.lookahead.type not in sync_set:
            self.next_token()

    def match(self, expected: TokenType, expected_name: str, phrase: str | None = None):
        if self.lookahead.type == expected:
            self.next_token()
        else:
            self.has_error = True
            recovery = (
                f"phrase-level recovery: skip to end of {phrase}"
                if phrase
                else "panic-mode: sync on ;, }, program, EOF"
            )
            self.errors.report(
                ErrorType.SYNTAX,
                f"Expected {expected_name} but found '{self.lookahead.type_to_string()}'",
                self.lookahead.line,
                self.lookahead.col,
                recovery_action=recovery,
            )
            if phrase:
                self._recover_phrase(phrase, consume_semicolon=(phrase == "statement"))
            else:
                self._panic_sync()

    def parse(self) -> tuple[bool, ASTNode | None]:
        self.has_error = False
        self.main_found = False
        self.main_param_count = 0
        self.next_token()
        ast = self._program()
        if not self.main_found:
            self.errors.report(
                ErrorType.SEMANTIC,
                "Program must contain a void main() method with no parameters",
                1,
                1,
            )
            self.has_error = True
        elif self.main_param_count > 0:
            self.errors.report(
                ErrorType.SEMANTIC,
                "main() must not have parameters",
                1,
                1,
            )
            self.has_error = True
        if self.lookahead.type != TokenType.EOF:
            self.errors.report(ErrorType.SYNTAX, "Unexpected tokens after end of program",
                               self.lookahead.line, self.lookahead.col)
            self.has_error = True
        success = not self.has_error and not self.errors.has_errors()
        return success, ast

    def _program(self) -> ASTNode | None:
        node = make_node(ASTNodeType.PROGRAM)
        if self.lookahead.type != TokenType.KW_PROGRAM:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, "Expected 'program' keyword at start",
                               self.lookahead.line, self.lookahead.col)
            return node
        self.match(TokenType.KW_PROGRAM, "'program'")
        if self.lookahead.type == TokenType.IDENTIFIER:
            node.name = self.lookahead.lexeme
            self.sym_table.insert(self.lookahead.lexeme, IdentifierKind.CLASS, DataType.USER_DEFINED, self.lookahead.line)
            self.match(TokenType.IDENTIFIER, "identifier (program name)")
        else:
            self.errors.report(ErrorType.SYNTAX, "Expected program name", self.lookahead.line, self.lookahead.col)
            self.has_error = True

        while self.lookahead.type in (TokenType.KW_FINAL, TokenType.KW_CLASS, TokenType.IDENTIFIER):
            if self.lookahead.type == TokenType.KW_FINAL:
                child = self._const_decl()
                if child:
                    node.add_child(child)
            elif self.lookahead.type == TokenType.KW_CLASS:
                child = self._class_decl()
                if child:
                    node.add_child(child)
            else:
                child = self._var_decl()
                if child:
                    node.add_child(child)

        self.match(TokenType.SYM_LBRACE, "'{'")
        while self.lookahead.type not in (TokenType.SYM_RBRACE, TokenType.EOF):
            child = self._method_decl()
            if child:
                node.add_child(child)
        self.match(TokenType.SYM_RBRACE, "'}'")
        return node

    def _const_decl(self) -> ASTNode | None:
        self.match(TokenType.KW_FINAL, "'final'")
        dtype = self._type()
        name = self.lookahead.lexeme
        line = self.lookahead.line
        col = self.lookahead.col
        if self.lookahead.type == TokenType.IDENTIFIER:
            if self.sym_table.lookup_current(name) is not None:
                self.errors.report(ErrorType.SEMANTIC, f"Duplicate constant '{name}'", self.lookahead.line, self.lookahead.col)
            else:
                self.sym_table.insert(
                    name,
                    kind_for_declaration(dtype, is_constant=True),
                    type_string_to_data_type(dtype),
                    self.lookahead.line,
                )
            self.match(TokenType.IDENTIFIER, "identifier (constant name)")
        self.match(TokenType.SYM_ASSIGN, "'='")
        value = None
        if self.lookahead.type == TokenType.NUMBER:
            value = self.lookahead.lexeme
            self.match(TokenType.NUMBER, "number")
        elif self.lookahead.type == TokenType.CHAR_CONST:
            value = self.lookahead.lexeme
            self.match(TokenType.CHAR_CONST, "char constant")
        else:
            self.errors.report(ErrorType.SYNTAX, "Expected number or char constant", self.lookahead.line, self.lookahead.col)
        self.match(TokenType.SYM_SEMICOL, "';'", phrase="declaration")
        return make_node(ASTNodeType.CONST_DECL, name=name, value=value, data_type=dtype, line=line, col=col)

    def _var_decl(self) -> ASTNode | None:
        dtype = self._type()
        line = self.lookahead.line
        col = self.lookahead.col
        names = []
        name = self.lookahead.lexeme
        if self.lookahead.type == TokenType.IDENTIFIER:
            if self.sym_table.lookup_current(name) is not None:
                self.errors.report(ErrorType.SEMANTIC, f"Duplicate variable '{name}'", self.lookahead.line, self.lookahead.col)
            else:
                self.sym_table.insert(
                    name,
                    kind_for_declaration(dtype),
                    type_string_to_data_type(dtype),
                    self.lookahead.line,
                )
            names.append(name)
            self.match(TokenType.IDENTIFIER, "identifier (variable name)")
        while self.lookahead.type == TokenType.SYM_COMMA:
            self.match(TokenType.SYM_COMMA, "','")
            name = self.lookahead.lexeme
            if self.lookahead.type == TokenType.IDENTIFIER:
                if self.sym_table.lookup_current(name) is not None:
                    self.errors.report(ErrorType.SEMANTIC, f"Duplicate variable '{name}'", self.lookahead.line, self.lookahead.col)
                else:
                    self.sym_table.insert(
                        name,
                        kind_for_declaration(dtype),
                        type_string_to_data_type(dtype),
                        self.lookahead.line,
                    )
                names.append(name)
                self.match(TokenType.IDENTIFIER, "identifier (variable name)")
        self.match(TokenType.SYM_SEMICOL, "';'", phrase="declaration")
        return make_node(ASTNodeType.VAR_DECL, names=names, data_type=dtype, line=line, col=col)

    def _class_decl(self) -> ASTNode | None:
        self.match(TokenType.KW_CLASS, "'class'")
        name = self.lookahead.lexeme
        line = self.lookahead.line
        col = self.lookahead.col
        if self.lookahead.type == TokenType.IDENTIFIER:
            self.sym_table.insert(name, IdentifierKind.CLASS, DataType.USER_DEFINED, line)
            self.match(TokenType.IDENTIFIER, "identifier (class name)")
        node = make_node(ASTNodeType.CLASS_DECL, name=name, line=line, col=col)
        self.match(TokenType.SYM_LBRACE, "'{'")
        self.sym_table.begin_scope()
        while self.lookahead.type == TokenType.IDENTIFIER:
            child = self._var_decl()
            if child:
                node.add_child(child)
        self.match(TokenType.SYM_RBRACE, "'}'", phrase="block")
        self.sym_table.end_scope()
        return node

    def _method_decl(self) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col
        if self.lookahead.type == TokenType.KW_VOID:
            return_type = "void"
            self.match(TokenType.KW_VOID, "'void'")
        else:
            return_type = self._type()
            if return_type is None:
                return_type = "int"

        name = self.lookahead.lexeme
        if self.lookahead.type == TokenType.IDENTIFIER:
            if self.sym_table.lookup_current(name) is not None:
                self.errors.report(ErrorType.SEMANTIC, f"Duplicate method '{name}'", self.lookahead.line, self.lookahead.col)
            else:
                self.sym_table.insert(
                    name,
                    IdentifierKind.FUNCTION,
                    type_string_to_data_type(return_type),
                    self.lookahead.line,
                )
            self.match(TokenType.IDENTIFIER, "identifier (method name)")

        node = make_node(ASTNodeType.METHOD_DECL, name=name, return_type=return_type, line=line, col=col)

        self.match(TokenType.SYM_LPAREN, "'('")
        self.sym_table.begin_scope()
        param_count = 0

        if self.lookahead.type == TokenType.IDENTIFIER:
            ptype = self._type()
            pname = self.lookahead.lexeme
            if self.lookahead.type == TokenType.IDENTIFIER:
                self.sym_table.insert(
                    pname,
                    IdentifierKind.PARAMETER,
                    type_string_to_data_type(ptype),
                    self.lookahead.line,
                )
                node.add_child(make_node(ASTNodeType.PARAMETER, name=pname, data_type=ptype, line=self.lookahead.line, col=self.lookahead.col))
                self.match(TokenType.IDENTIFIER, "identifier (parameter name)")
                param_count += 1
            while self.lookahead.type == TokenType.SYM_COMMA:
                self.match(TokenType.SYM_COMMA, "','")
                ptype = self._type()
                pname = self.lookahead.lexeme
                if self.lookahead.type == TokenType.IDENTIFIER:
                    self.sym_table.insert(
                        pname,
                        IdentifierKind.PARAMETER,
                        type_string_to_data_type(ptype),
                        self.lookahead.line,
                    )
                    node.add_child(make_node(ASTNodeType.PARAMETER, name=pname, data_type=ptype, line=self.lookahead.line, col=self.lookahead.col))
                    self.match(TokenType.IDENTIFIER, "identifier (parameter name)")
                    param_count += 1

        if name == "main":
            self.main_found = True
            self.main_param_count = param_count
            if return_type != "void":
                self.errors.report(
                    ErrorType.SEMANTIC,
                    "main() must be declared as void",
                    line,
                    col,
                )

        self.match(TokenType.SYM_RPAREN, "')'")

        while self.lookahead.type == TokenType.IDENTIFIER:
            child = self._var_decl()
            if child:
                node.add_child(child)

        block_node = self._block()
        if block_node:
            node.add_child(block_node)

        self.sym_table.end_scope()
        return node

    def _type(self) -> str | None:
        if self.lookahead.type == TokenType.IDENTIFIER:
            name = self.lookahead.lexeme
            self.match(TokenType.IDENTIFIER, "type identifier")
            if self.lookahead.type == TokenType.SYM_LBRACK:
                self.match(TokenType.SYM_LBRACK, "'['")
                self.match(TokenType.SYM_RBRACK, "']'")
                return name + "[]"
            return name
        else:
            self.errors.report(ErrorType.SYNTAX, "Expected type identifier", self.lookahead.line, self.lookahead.col)
            self.has_error = True
            return None

    def _block(self) -> ASTNode | None:
        node = make_node(ASTNodeType.BLOCK)
        self.match(TokenType.SYM_LBRACE, "'{'")
        while self.lookahead.type not in (TokenType.SYM_RBRACE, TokenType.EOF):
            child = self._statement()
            if child:
                node.add_child(child)
        self.match(TokenType.SYM_RBRACE, "'}'", phrase="block")
        return node

    def _statement(self) -> ASTNode | None:
        if self.lookahead.type == TokenType.IDENTIFIER:
            desig = self._designator()
            if self.lookahead.type == TokenType.SYM_ASSIGN:
                self.match(TokenType.SYM_ASSIGN, "'='")
                expr = self._expr()
                self.match(TokenType.SYM_SEMICOL, "';'", phrase="statement")
                return make_node(ASTNodeType.ASSIGN_STMT, line=desig.line if desig else 0, col=desig.col if desig else 0,
                                 children=[desig, expr] if desig and expr else [n for n in (desig, expr) if n])
            elif self.lookahead.type == TokenType.SYM_LPAREN:
                self._act_pars()
                self.match(TokenType.SYM_SEMICOL, "';'", phrase="statement")
                return make_node(ASTNodeType.CALL_STMT, children=[desig] if desig else [])
            else:
                self.has_error = True
                self.errors.report(
                    ErrorType.SYNTAX,
                    "Expected '=' or '(' after designator",
                    self.lookahead.line,
                    self.lookahead.col,
                    recovery_action="phrase-level recovery: skip to end of statement",
                )
                self._recover_phrase("statement", consume_semicolon=True)
                return make_node(ASTNodeType.EMPTY_STMT)
        elif self.lookahead.type == TokenType.KW_IF:
            line = self.lookahead.line
            col = self.lookahead.col
            self.match(TokenType.KW_IF, "'if'")
            self.match(TokenType.SYM_LPAREN, "'('")
            cond = self._condition()
            self.match(TokenType.SYM_RPAREN, "')'")
            then_stmt = self._statement()
            else_stmt = None
            if self.lookahead.type == TokenType.KW_ELSE:
                self.match(TokenType.KW_ELSE, "'else'")
                else_stmt = self._statement()
            children = [n for n in (cond, then_stmt, else_stmt) if n]
            return make_node(ASTNodeType.IF_STMT, line=line, col=col, children=children)
        elif self.lookahead.type == TokenType.KW_WHILE:
            line = self.lookahead.line
            col = self.lookahead.col
            self.match(TokenType.KW_WHILE, "'while'")
            self.match(TokenType.SYM_LPAREN, "'('")
            cond = self._condition()
            self.match(TokenType.SYM_RPAREN, "')'")
            body = self._statement()
            children = [n for n in (cond, body) if n]
            return make_node(ASTNodeType.WHILE_STMT, line=line, col=col, children=children)
        elif self.lookahead.type == TokenType.KW_RETURN:
            line = self.lookahead.line
            col = self.lookahead.col
            self.match(TokenType.KW_RETURN, "'return'")
            expr = None
            if self.lookahead.type != TokenType.SYM_SEMICOL:
                expr = self._expr()
            self.match(TokenType.SYM_SEMICOL, "';'")
            children = [expr] if expr else []
            return make_node(ASTNodeType.RETURN_STMT, line=line, col=col, children=children)
        elif self.lookahead.type == TokenType.KW_READ:
            line = self.lookahead.line
            col = self.lookahead.col
            self.match(TokenType.KW_READ, "'read'")
            self.match(TokenType.SYM_LPAREN, "'('")
            desig = self._designator()
            self.match(TokenType.SYM_RPAREN, "')'")
            self.match(TokenType.SYM_SEMICOL, "';'")
            return make_node(ASTNodeType.READ_STMT, line=line, col=col, children=[desig] if desig else [])
        elif self.lookahead.type == TokenType.KW_PRINT:
            line = self.lookahead.line
            col = self.lookahead.col
            self.match(TokenType.KW_PRINT, "'print'")
            self.match(TokenType.SYM_LPAREN, "'('")
            expr = self._expr()
            width = None
            if self.lookahead.type == TokenType.SYM_COMMA:
                self.match(TokenType.SYM_COMMA, "','")
                width = self.lookahead.lexeme
                self.match(TokenType.NUMBER, "number")
            self.match(TokenType.SYM_RPAREN, "')'")
            self.match(TokenType.SYM_SEMICOL, "';'")
            children = [expr] if expr else []
            return make_node(ASTNodeType.PRINT_STMT, line=line, col=col, width=width, children=children)
        elif self.lookahead.type == TokenType.SYM_LBRACE:
            return self._block()
        elif self.lookahead.type == TokenType.SYM_SEMICOL:
            self.match(TokenType.SYM_SEMICOL, "';'")
            return make_node(ASTNodeType.EMPTY_STMT)
        else:
            self.has_error = True
            self.errors.report(
                ErrorType.SYNTAX,
                f"Unexpected token in statement: '{self.lookahead.lexeme}'",
                self.lookahead.line,
                self.lookahead.col,
                recovery_action="phrase-level recovery: skip to end of statement",
            )
            self._recover_phrase("statement", consume_semicolon=True)
            return make_node(ASTNodeType.EMPTY_STMT)

    def _designator(self) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col
        name = None
        if self.lookahead.type == TokenType.IDENTIFIER:
            name = self.lookahead.lexeme
            if self.sym_table.lookup(name) is None:
                self.errors.report(ErrorType.SEMANTIC, f"Undeclared identifier '{name}'",
                                   self.lookahead.line, self.lookahead.col)
            self.match(TokenType.IDENTIFIER, "identifier")
        node = make_node(ASTNodeType.DESIGNATOR, name=name, line=line, col=col)
        while self.lookahead.type in (TokenType.SYM_DOT, TokenType.SYM_LBRACK):
            if self.lookahead.type == TokenType.SYM_DOT:
                self.match(TokenType.SYM_DOT, "'.'")
                if self.lookahead.type == TokenType.IDENTIFIER:
                    member = self.lookahead.lexeme
                    self.match(TokenType.IDENTIFIER, "identifier")
                    node.add_child(make_node(ASTNodeType.IDENTIFIER, name=member))
            else:
                self.match(TokenType.SYM_LBRACK, "'['")
                expr = self._expr()
                self.match(TokenType.SYM_RBRACK, "']'")
                if expr:
                    node.add_child(expr)
        return node

    def _act_pars(self):
        self.match(TokenType.SYM_LPAREN, "'('")
        if self.lookahead.type != TokenType.SYM_RPAREN:
            self._expr()
            while self.lookahead.type == TokenType.SYM_COMMA:
                self.match(TokenType.SYM_COMMA, "','")
                self._expr()
        self.match(TokenType.SYM_RPAREN, "')'")

    def _condition(self) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col
        left = self._expr()
        op = self._relop()
        right = self._expr()
        return make_node(ASTNodeType.CONDITION, op=op, line=line, col=col,
                         children=[n for n in (left, right) if n])

    def _relop(self) -> str | None:
        if self.lookahead.type == TokenType.OP_EQ:
            op = "=="
            self.next_token()
        elif self.lookahead.type == TokenType.OP_NEQ:
            op = "!="
            self.next_token()
        elif self.lookahead.type == TokenType.OP_GT:
            op = ">"
            self.next_token()
        elif self.lookahead.type == TokenType.OP_GE:
            op = ">="
            self.next_token()
        elif self.lookahead.type == TokenType.OP_LT:
            op = "<"
            self.next_token()
        elif self.lookahead.type == TokenType.OP_LE:
            op = "<="
            self.next_token()
        else:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, "Expected relational operator", self.lookahead.line, self.lookahead.col)
            op = None
        return op

    def _expr(self) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col
        if self.lookahead.type == TokenType.OP_MINUS:
            self.match(TokenType.OP_MINUS, "'-'")
            term = self._term()
            unary = make_node(ASTNodeType.UNARY_OP, op="-", line=line, col=col)
            if term:
                unary.add_child(term)
            left = unary
        else:
            left = self._term()

        while self.lookahead.type in (TokenType.OP_PLUS, TokenType.OP_MINUS):
            op = self.lookahead.lexeme
            self.match(self.lookahead.type, self.lookahead.lexeme)
            right = self._term()
            binop = make_node(ASTNodeType.BINARY_OP, op=op, line=line, col=col)
            if left:
                binop.add_child(left)
            if right:
                binop.add_child(right)
            left = binop
        return left

    def _term(self) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col
        left = self._factor()
        while self.lookahead.type in (TokenType.OP_MULT, TokenType.OP_DIV, TokenType.OP_MOD):
            op = self.lookahead.lexeme
            self.match(self.lookahead.type, "'*' or '/' or '%'")
            right = self._factor()
            binop = make_node(ASTNodeType.BINARY_OP, op=op, line=line, col=col)
            if left:
                binop.add_child(left)
            if right:
                binop.add_child(right)
            left = binop
        return left

    def _factor(self) -> ASTNode | None:
        line = self.lookahead.line
        col = self.lookahead.col
        if self.lookahead.type == TokenType.IDENTIFIER:
            desig = self._designator()
            if self.lookahead.type == TokenType.SYM_LPAREN:
                self._act_pars()
                return make_node(ASTNodeType.CALL_STMT, children=[desig] if desig else [])
            return desig
        elif self.lookahead.type == TokenType.NUMBER:
            value = self.lookahead.lexeme
            self.match(TokenType.NUMBER, "number")
            return make_node(ASTNodeType.NUMBER_LITERAL, value=value, line=line, col=col)
        elif self.lookahead.type == TokenType.CHAR_CONST:
            value = self.lookahead.lexeme
            self.match(TokenType.CHAR_CONST, "char constant")
            return make_node(ASTNodeType.CHAR_LITERAL, value=value, line=line, col=col)
        elif self.lookahead.type == TokenType.KW_NEW:
            self.match(TokenType.KW_NEW, "'new'")
            if self.lookahead.type == TokenType.IDENTIFIER:
                name = self.lookahead.lexeme
                self.match(TokenType.IDENTIFIER, "identifier")
                size_expr = None
                if self.lookahead.type == TokenType.SYM_LBRACK:
                    self.match(TokenType.SYM_LBRACK, "'['")
                    size_expr = self._expr()
                    self.match(TokenType.SYM_RBRACK, "']'")
                children = [size_expr] if size_expr else []
                return make_node(ASTNodeType.NEW_EXPR, name=name, line=line, col=col, children=children)
        elif self.lookahead.type == TokenType.SYM_LPAREN:
            self.match(TokenType.SYM_LPAREN, "'('")
            expr = self._expr()
            self.match(TokenType.SYM_RPAREN, "')'")
            return expr
        else:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, "Invalid expression factor", self.lookahead.line, self.lookahead.col)
            self.next_token()
            return None
