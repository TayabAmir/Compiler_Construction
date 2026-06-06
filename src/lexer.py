from __future__ import annotations

from .token import Token, TokenType
from .error_handler import ErrorHandler, ErrorType


KEYWORDS = {
    "program": TokenType.KW_PROGRAM,
    "class": TokenType.KW_CLASS,
    "if": TokenType.KW_IF,
    "else": TokenType.KW_ELSE,
    "while": TokenType.KW_WHILE,
    "read": TokenType.KW_READ,
    "print": TokenType.KW_PRINT,
    "return": TokenType.KW_RETURN,
    "void": TokenType.KW_VOID,
    "final": TokenType.KW_FINAL,
    "new": TokenType.KW_NEW,
}


class Lexer:
    def __init__(self, source: str, errors: ErrorHandler):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 0
        self.errors = errors

    def peek(self) -> str:
        if self.pos >= len(self.source):
            return ""
        return self.source[self.pos]

    def advance(self) -> str:
        if self.pos >= len(self.source):
            return ""
        c = self.source[self.pos]
        self.pos += 1
        if c == "\n":
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        return c

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            c = self.peek()
            # treat literal whitespace characters as whitespace
            if c in " \t\n\r":
                self.advance()
                continue
            # treat backslash-escaped whitespace sequences (e.g. "\\r", "\\n", "\\t") as whitespace
            if c == "\\" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] in "rnt":
                self.advance()
                self.advance()
                continue
            if c == "/" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "/":
                self.advance()
                self.advance()
                while self.pos < len(self.source) and self.peek() != "\n":
                    self.advance()
                continue
            break

    def get_next_token(self) -> Token:
        self.skip_whitespace_and_comments()

        if self.pos >= len(self.source):
            return Token(TokenType.EOF, "EOF", self.line, self.col)

        c = self.peek()
        start_line, start_col = self.line, self.col

        # backslash-escaped whitespace sequences are handled by the skipper above

        if c.isalpha() or c == "_":
            lexeme = ""
            while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == "_"):
                lexeme += self.advance()
            if lexeme in KEYWORDS:
                return Token(KEYWORDS[lexeme], lexeme, start_line, start_col)
            return Token(TokenType.IDENTIFIER, lexeme, start_line, start_col)

        if c.isdigit():
            lexeme = ""
            while self.pos < len(self.source) and self.peek().isdigit():
                lexeme += self.advance()
            return Token(TokenType.NUMBER, lexeme, start_line, start_col)

        if c == "'":
            lexeme = self.advance()
            if self.pos < len(self.source):
                if self.peek() == "\\":
                    lexeme += self.advance()
                    if self.pos < len(self.source):
                        lexeme += self.advance()
                else:
                    lexeme += self.advance()
            if self.pos < len(self.source) and self.peek() == "'":
                lexeme += self.advance()
            else:
                self.errors.report(ErrorType.LEXICAL, "Unterminated character constant", start_line, start_col)
            return Token(TokenType.CHAR_CONST, lexeme, start_line, start_col)

        if c == "=":
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.OP_EQ, "==", start_line, start_col)
            return Token(TokenType.SYM_ASSIGN, "=", start_line, start_col)

        if c == "!":
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.OP_NEQ, "!=", start_line, start_col)
            self.errors.report(ErrorType.LEXICAL, "Unexpected character '!'", start_line, start_col)
            return Token(TokenType.UNKNOWN, "!", start_line, start_col)

        if c == ">":
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.OP_GE, ">=", start_line, start_col)
            return Token(TokenType.OP_GT, ">", start_line, start_col)

        if c == "<":
            self.advance()
            if self.peek() == "=":
                self.advance()
                return Token(TokenType.OP_LE, "<=", start_line, start_col)
            return Token(TokenType.OP_LT, "<", start_line, start_col)

        self.advance()
        single_chars = {
            "+": TokenType.OP_PLUS,
            "-": TokenType.OP_MINUS,
            "*": TokenType.OP_MULT,
            "/": TokenType.OP_DIV,
            "%": TokenType.OP_MOD,
            "(": TokenType.SYM_LPAREN,
            ")": TokenType.SYM_RPAREN,
            "[": TokenType.SYM_LBRACK,
            "]": TokenType.SYM_RBRACK,
            "{": TokenType.SYM_LBRACE,
            "}": TokenType.SYM_RBRACE,
            ";": TokenType.SYM_SEMICOL,
            ",": TokenType.SYM_COMMA,
            ".": TokenType.SYM_DOT,
        }
        if c in single_chars:
            return Token(single_chars[c], c, start_line, start_col)

        self.errors.report(ErrorType.LEXICAL, f"Unknown character: '{c}'", start_line, start_col)
        return Token(TokenType.UNKNOWN, c, start_line, start_col)

    def tokenize_all(self) -> list[Token]:
        tokens = []
        t = self.get_next_token()
        while t.type != TokenType.EOF:
            tokens.append(t)
            t = self.get_next_token()
        tokens.append(t)
        return tokens
