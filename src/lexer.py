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

BUFFER_HALF = 2048
EOF_SENTINEL = "\0"


class DoubleBuffer:
    def __init__(self, source: str):
        self.source = source
        self.source_len = len(source)
        self.buffer = [EOF_SENTINEL] * (2 * BUFFER_HALF + 2)
        self.current = 0
        self.read_pos = 0
        self.line = 1
        self.col = 0
        self._load_buffer(0)
        if self.read_pos < self.source_len:
            self._load_buffer(BUFFER_HALF)

    def _load_buffer(self, start: int):
        i = start
        end = start + BUFFER_HALF
        while i < end and self.read_pos < self.source_len:
            self.buffer[i] = self.source[self.read_pos]
            i += 1
            self.read_pos += 1
        self.buffer[i] = EOF_SENTINEL

    def _reload_if_needed(self):
        if self.buffer[self.current] != EOF_SENTINEL:
            return
        if self.read_pos >= self.source_len:
            return
        if self.current < BUFFER_HALF:
            self._load_buffer(BUFFER_HALF)
            self.current = BUFFER_HALF
        else:
            self._load_buffer(0)
            self.current = 0

    def peek(self) -> str:
        self._reload_if_needed()
        return self.buffer[self.current]

    def advance(self) -> str:
        self._reload_if_needed()
        c = self.buffer[self.current]
        if c == EOF_SENTINEL:
            return ""
        self.current += 1
        if c == "\n":
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        return c

    def at_end(self) -> bool:
        self._reload_if_needed()
        return self.buffer[self.current] == EOF_SENTINEL


class Lexer:
    def __init__(self, source: str, errors: ErrorHandler):
        self.buffer = DoubleBuffer(source)
        self.errors = errors

    @property
    def line(self) -> int:
        return self.buffer.line

    @property
    def col(self) -> int:
        return self.buffer.col

    def peek(self) -> str:
        return self.buffer.peek()

    def advance(self) -> str:
        return self.buffer.advance()

    def skip_whitespace_and_comments(self):
        while not self.buffer.at_end():
            c = self.peek()
            if c in " \t\n\r":
                self.advance()
                continue
            if c == "\\" and self.buffer.current + 1 < len(self.buffer.source) and self.buffer.source[self.buffer.current + 1] in "rnt":
                self.advance()
                self.advance()
                continue
            if c == "/" and self._next_char() == "/":
                self.advance()
                self.advance()
                while not self.buffer.at_end() and self.peek() != "\n":
                    self.advance()
                continue
            break

    def _next_char(self) -> str:
        if self.buffer.at_end():
            return ""
        saved = self.buffer.current
        saved_line = self.buffer.line
        saved_col = self.buffer.col
        self.buffer.advance()
        nxt = self.buffer.peek()
        self.buffer.current = saved
        self.buffer.line = saved_line
        self.buffer.col = saved_col
        return nxt

    def get_next_token(self) -> Token:
        self.skip_whitespace_and_comments()

        if self.buffer.at_end():
            return Token(TokenType.EOF, "EOF", self.line, self.col)

        c = self.peek()
        start_line, start_col = self.line, self.col

        if c.isalpha():
            lexeme = ""
            while not self.buffer.at_end() and self.peek().isalnum():
                lexeme += self.advance()
            if lexeme in KEYWORDS:
                return Token(KEYWORDS[lexeme], lexeme, start_line, start_col)
            return Token(TokenType.IDENTIFIER, lexeme, start_line, start_col)

        if c.isdigit():
            lexeme = ""
            while not self.buffer.at_end() and self.peek().isdigit():
                lexeme += self.advance()
            return Token(TokenType.NUMBER, lexeme, start_line, start_col)

        if c == "'":
            lexeme = self.advance()
            if not self.buffer.at_end():
                if self.peek() == "\\":
                    lexeme += self.advance()
                    if not self.buffer.at_end():
                        lexeme += self.advance()
                else:
                    lexeme += self.advance()
            if not self.buffer.at_end() and self.peek() == "'":
                lexeme += self.advance()
            else:
                self.errors.report(
                    ErrorType.LEXICAL,
                    "Unterminated character constant",
                    start_line,
                    start_col,
                )
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
