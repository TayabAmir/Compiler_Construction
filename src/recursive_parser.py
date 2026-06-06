from __future__ import annotations

from .token import Token, TokenType
from .lexer import Lexer
from .symbol_table import ScopeManager, IdentifierKind, DataType
from .error_handler import ErrorHandler, ErrorType


class RecursiveParser:
    def __init__(self, lexer: Lexer, sym_table: ScopeManager, errors: ErrorHandler):
        self.lexer = lexer
        self.sym_table = sym_table
        self.errors = errors
        self.lookahead: Token | None = None
        self.has_error = False

    def next_token(self):
        self.lookahead = self.lexer.get_next_token()

    def match(self, expected: TokenType, expected_name: str):
        if self.lookahead.type == expected:
            self.next_token()
        else:
            self.has_error = True
            self.errors.report(
                ErrorType.SYNTAX,
                f"Expected {expected_name} but found '{self.lookahead.type_to_string()}'",
                self.lookahead.line, self.lookahead.col,
            )
            sync_set = {TokenType.EOF, TokenType.SYM_SEMICOL, TokenType.SYM_RBRACE, TokenType.KW_PROGRAM}
            while self.lookahead.type not in sync_set:
                self.next_token()

    def parse(self) -> bool:
        self.has_error = False
        self.next_token()
        self._program()
        if self.lookahead.type != TokenType.EOF:
            self.errors.report(ErrorType.SYNTAX, "Unexpected tokens after end of program",
                               self.lookahead.line, self.lookahead.col)
            self.has_error = True
        return not self.has_error and not self.errors.has_errors()

    def _program(self):
        if self.lookahead.type != TokenType.KW_PROGRAM:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, "Expected 'program' keyword at start",
                               self.lookahead.line, self.lookahead.col)
            return
        self.match(TokenType.KW_PROGRAM, "'program'")
        if self.lookahead.type == TokenType.IDENTIFIER:
            self.sym_table.insert(self.lookahead.lexeme, IdentifierKind.CLASS, DataType.USER_DEFINED, self.lookahead.line)
            self.match(TokenType.IDENTIFIER, "identifier (program name)")
        else:
            self.errors.report(ErrorType.SYNTAX, "Expected program name", self.lookahead.line, self.lookahead.col)
            self.has_error = True

        while self.lookahead.type in (TokenType.KW_FINAL, TokenType.KW_CLASS, TokenType.IDENTIFIER):
            if self.lookahead.type == TokenType.KW_FINAL:
                self._const_decl()
            elif self.lookahead.type == TokenType.KW_CLASS:
                self._class_decl()
            else:
                self._var_decl()

        self.match(TokenType.SYM_LBRACE, "'{'")
        while self.lookahead.type not in (TokenType.SYM_RBRACE, TokenType.EOF):
            self._method_decl()
        self.match(TokenType.SYM_RBRACE, "'}'")

    def _const_decl(self):
        self.match(TokenType.KW_FINAL, "'final'")
        self._type()
        name = self.lookahead.lexeme
        if self.lookahead.type == TokenType.IDENTIFIER:
            if self.sym_table.lookup_current(name) is not None:
                self.errors.report(ErrorType.SEMANTIC, f"Duplicate constant '{name}'", self.lookahead.line, self.lookahead.col)
            else:
                self.sym_table.insert(name, IdentifierKind.CONSTANT, DataType.INT, self.lookahead.line)
            self.match(TokenType.IDENTIFIER, "identifier (constant name)")
        self.match(TokenType.SYM_ASSIGN, "'='")
        if self.lookahead.type == TokenType.NUMBER:
            self.match(TokenType.NUMBER, "number")
        elif self.lookahead.type == TokenType.CHAR_CONST:
            self.match(TokenType.CHAR_CONST, "char constant")
        else:
            self.errors.report(ErrorType.SYNTAX, "Expected number or char constant", self.lookahead.line, self.lookahead.col)
        self.match(TokenType.SYM_SEMICOL, "';'")

    def _var_decl(self):
        self._type()
        name = self.lookahead.lexeme
        if self.lookahead.type == TokenType.IDENTIFIER:
            if self.sym_table.lookup_current(name) is not None:
                self.errors.report(ErrorType.SEMANTIC, f"Duplicate variable '{name}'", self.lookahead.line, self.lookahead.col)
            else:
                self.sym_table.insert(name, IdentifierKind.VARIABLE, DataType.INT, self.lookahead.line)
            self.match(TokenType.IDENTIFIER, "identifier (variable name)")
        while self.lookahead.type == TokenType.SYM_COMMA:
            self.match(TokenType.SYM_COMMA, "','")
            name = self.lookahead.lexeme
            if self.lookahead.type == TokenType.IDENTIFIER:
                if self.sym_table.lookup_current(name) is not None:
                    self.errors.report(ErrorType.SEMANTIC, f"Duplicate variable '{name}'", self.lookahead.line, self.lookahead.col)
                else:
                    self.sym_table.insert(name, IdentifierKind.VARIABLE, DataType.INT, self.lookahead.line)
                self.match(TokenType.IDENTIFIER, "identifier (variable name)")
        self.match(TokenType.SYM_SEMICOL, "';'")

    def _class_decl(self):
        self.match(TokenType.KW_CLASS, "'class'")
        name = self.lookahead.lexeme
        if self.lookahead.type == TokenType.IDENTIFIER:
            self.sym_table.insert(name, IdentifierKind.CLASS, DataType.USER_DEFINED, self.lookahead.line)
            self.match(TokenType.IDENTIFIER, "identifier (class name)")
        self.match(TokenType.SYM_LBRACE, "'{'")
        while self.lookahead.type == TokenType.IDENTIFIER:
            self._var_decl()
        self.match(TokenType.SYM_RBRACE, "'}'")

    def _method_decl(self):
        if self.lookahead.type == TokenType.KW_VOID:
            self.match(TokenType.KW_VOID, "'void'")
        else:
            self._type()

        name = self.lookahead.lexeme
        if self.lookahead.type == TokenType.IDENTIFIER:
            if self.sym_table.lookup_current(name) is not None:
                self.errors.report(ErrorType.SEMANTIC, f"Duplicate method '{name}'", self.lookahead.line, self.lookahead.col)
            else:
                self.sym_table.insert(name, IdentifierKind.FUNCTION, DataType.INT, self.lookahead.line)
            self.match(TokenType.IDENTIFIER, "identifier (method name)")

        self.match(TokenType.SYM_LPAREN, "'('")
        self.sym_table.begin_scope()

        if self.lookahead.type == TokenType.IDENTIFIER:
            self._type()
            pname = self.lookahead.lexeme
            if self.lookahead.type == TokenType.IDENTIFIER:
                self.sym_table.insert(pname, IdentifierKind.PARAMETER, DataType.INT, self.lookahead.line)
                self.match(TokenType.IDENTIFIER, "identifier (parameter name)")
            while self.lookahead.type == TokenType.SYM_COMMA:
                self.match(TokenType.SYM_COMMA, "','")
                self._type()
                pname = self.lookahead.lexeme
                if self.lookahead.type == TokenType.IDENTIFIER:
                    self.sym_table.insert(pname, IdentifierKind.PARAMETER, DataType.INT, self.lookahead.line)
                    self.match(TokenType.IDENTIFIER, "identifier (parameter name)")

        self.match(TokenType.SYM_RPAREN, "')'")

        while self.lookahead.type == TokenType.IDENTIFIER:
            self._var_decl()
        self._block()

        self.sym_table.end_scope()

    def _type(self):
        if self.lookahead.type == TokenType.IDENTIFIER:
            self.match(TokenType.IDENTIFIER, "type identifier")
            if self.lookahead.type == TokenType.SYM_LBRACK:
                self.match(TokenType.SYM_LBRACK, "'['")
                self.match(TokenType.SYM_RBRACK, "']'")
        else:
            self.errors.report(ErrorType.SYNTAX, "Expected type identifier", self.lookahead.line, self.lookahead.col)
            self.has_error = True

    def _block(self):
        self.match(TokenType.SYM_LBRACE, "'{'")
        while self.lookahead.type not in (TokenType.SYM_RBRACE, TokenType.EOF):
            self._statement()
        self.match(TokenType.SYM_RBRACE, "'}'")

    def _statement(self):
        if self.lookahead.type == TokenType.IDENTIFIER:
            self._designator()
            if self.lookahead.type == TokenType.SYM_ASSIGN:
                self.match(TokenType.SYM_ASSIGN, "'='")
                self._expr()
            elif self.lookahead.type == TokenType.SYM_LPAREN:
                self._act_pars()
            else:
                self.errors.report(ErrorType.SYNTAX, "Expected '=' or '(' after designator",
                                   self.lookahead.line, self.lookahead.col)
                self.has_error = True
            self.match(TokenType.SYM_SEMICOL, "';'")
        elif self.lookahead.type == TokenType.KW_IF:
            self.match(TokenType.KW_IF, "'if'")
            self.match(TokenType.SYM_LPAREN, "'('")
            self._condition()
            self.match(TokenType.SYM_RPAREN, "')'")
            self._statement()
            if self.lookahead.type == TokenType.KW_ELSE:
                self.match(TokenType.KW_ELSE, "'else'")
                self._statement()
        elif self.lookahead.type == TokenType.KW_WHILE:
            self.match(TokenType.KW_WHILE, "'while'")
            self.match(TokenType.SYM_LPAREN, "'('")
            self._condition()
            self.match(TokenType.SYM_RPAREN, "')'")
            self._statement()
        elif self.lookahead.type == TokenType.KW_RETURN:
            self.match(TokenType.KW_RETURN, "'return'")
            if self.lookahead.type != TokenType.SYM_SEMICOL:
                self._expr()
            self.match(TokenType.SYM_SEMICOL, "';'")
        elif self.lookahead.type == TokenType.KW_READ:
            self.match(TokenType.KW_READ, "'read'")
            self.match(TokenType.SYM_LPAREN, "'('")
            self._designator()
            self.match(TokenType.SYM_RPAREN, "')'")
            self.match(TokenType.SYM_SEMICOL, "';'")
        elif self.lookahead.type == TokenType.KW_PRINT:
            self.match(TokenType.KW_PRINT, "'print'")
            self.match(TokenType.SYM_LPAREN, "'('")
            self._expr()
            if self.lookahead.type == TokenType.SYM_COMMA:
                self.match(TokenType.SYM_COMMA, "','")
                self.match(TokenType.NUMBER, "number")
            self.match(TokenType.SYM_RPAREN, "')'")
            self.match(TokenType.SYM_SEMICOL, "';'")
        elif self.lookahead.type == TokenType.SYM_LBRACE:
            self._block()
        elif self.lookahead.type == TokenType.SYM_SEMICOL:
            self.match(TokenType.SYM_SEMICOL, "';'")
        else:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, f"Unexpected token in statement: {self.lookahead.lexeme}",
                               self.lookahead.line, self.lookahead.col)
            self.next_token()

    def _designator(self):
        if self.lookahead.type == TokenType.IDENTIFIER:
            name = self.lookahead.lexeme
            if self.sym_table.lookup(name) is None:
                self.errors.report(ErrorType.SEMANTIC, f"Undeclared identifier '{name}'",
                                   self.lookahead.line, self.lookahead.col)
            self.match(TokenType.IDENTIFIER, "identifier")
        while self.lookahead.type in (TokenType.SYM_DOT, TokenType.SYM_LBRACK):
            if self.lookahead.type == TokenType.SYM_DOT:
                self.match(TokenType.SYM_DOT, "'.'")
                if self.lookahead.type == TokenType.IDENTIFIER:
                    self.match(TokenType.IDENTIFIER, "identifier")
            else:
                self.match(TokenType.SYM_LBRACK, "'['")
                self._expr()
                self.match(TokenType.SYM_RBRACK, "']'")

    def _act_pars(self):
        self.match(TokenType.SYM_LPAREN, "'('")
        if self.lookahead.type != TokenType.SYM_RPAREN:
            self._expr()
            while self.lookahead.type == TokenType.SYM_COMMA:
                self.match(TokenType.SYM_COMMA, "','")
                self._expr()
        self.match(TokenType.SYM_RPAREN, "')'")

    def _condition(self):
        self._expr()
        self._relop()
        self._expr()

    def _relop(self):
        if self.lookahead.type in (TokenType.OP_EQ, TokenType.OP_NEQ, TokenType.OP_GT,
                                    TokenType.OP_GE, TokenType.OP_LT, TokenType.OP_LE):
            self.next_token()
        else:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, "Expected relational operator", self.lookahead.line, self.lookahead.col)

    def _expr(self):
        if self.lookahead.type == TokenType.OP_MINUS:
            self.match(TokenType.OP_MINUS, "'-'")
        self._term()
        while self.lookahead.type in (TokenType.OP_PLUS, TokenType.OP_MINUS):
            self.match(self.lookahead.type, self.lookahead.lexeme)
            self._term()

    def _term(self):
        self._factor()
        while self.lookahead.type in (TokenType.OP_MULT, TokenType.OP_DIV, TokenType.OP_MOD):
            self.match(self.lookahead.type, "'*' or '/' or '%'")
            self._factor()

    def _factor(self):
        if self.lookahead.type == TokenType.IDENTIFIER:
            self._designator()
            if self.lookahead.type == TokenType.SYM_LPAREN:
                self._act_pars()
        elif self.lookahead.type == TokenType.NUMBER:
            self.match(TokenType.NUMBER, "number")
        elif self.lookahead.type == TokenType.CHAR_CONST:
            self.match(TokenType.CHAR_CONST, "char constant")
        elif self.lookahead.type == TokenType.KW_NEW:
            self.match(TokenType.KW_NEW, "'new'")
            if self.lookahead.type == TokenType.IDENTIFIER:
                self.match(TokenType.IDENTIFIER, "identifier")
                if self.lookahead.type == TokenType.SYM_LBRACK:
                    self.match(TokenType.SYM_LBRACK, "'['")
                    self._expr()
                    self.match(TokenType.SYM_RBRACK, "']'")
        elif self.lookahead.type == TokenType.SYM_LPAREN:
            self.match(TokenType.SYM_LPAREN, "'('")
            self._expr()
            self.match(TokenType.SYM_RPAREN, "')'")
        else:
            self.has_error = True
            self.errors.report(ErrorType.SYNTAX, "Invalid expression factor", self.lookahead.line, self.lookahead.col)
            self.next_token()
