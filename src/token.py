from __future__ import annotations

from enum import Enum, auto


class TokenType(Enum):
    EOF = 0
    KW_PROGRAM = auto()
    KW_CLASS = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_READ = auto()
    KW_PRINT = auto()
    KW_RETURN = auto()
    KW_VOID = auto()
    KW_FINAL = auto()
    KW_NEW = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    CHAR_CONST = auto()
    OP_EQ = auto()
    OP_NEQ = auto()
    OP_GE = auto()
    OP_LE = auto()
    OP_GT = auto()
    OP_LT = auto()
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_MULT = auto()
    OP_DIV = auto()
    OP_MOD = auto()
    SYM_LPAREN = auto()
    SYM_RPAREN = auto()
    SYM_LBRACK = auto()
    SYM_RBRACK = auto()
    SYM_LBRACE = auto()
    SYM_RBRACE = auto()
    SYM_ASSIGN = auto()
    SYM_SEMICOL = auto()
    SYM_COMMA = auto()
    SYM_DOT = auto()
    COMMENT = auto()
    UNKNOWN = auto()


TOKEN_NAMES = {
    TokenType.EOF: "EOF",
    TokenType.KW_PROGRAM: "Keyword(program)",
    TokenType.KW_CLASS: "Keyword(class)",
    TokenType.KW_IF: "Keyword(if)",
    TokenType.KW_ELSE: "Keyword(else)",
    TokenType.KW_WHILE: "Keyword(while)",
    TokenType.KW_READ: "Keyword(read)",
    TokenType.KW_PRINT: "Keyword(print)",
    TokenType.KW_RETURN: "Keyword(return)",
    TokenType.KW_VOID: "Keyword(void)",
    TokenType.KW_FINAL: "Keyword(final)",
    TokenType.KW_NEW: "Keyword(new)",
    TokenType.IDENTIFIER: "Identifier",
    TokenType.NUMBER: "Number",
    TokenType.CHAR_CONST: "CharConst",
    TokenType.OP_EQ: "Operator(==)",
    TokenType.OP_NEQ: "Operator(!=)",
    TokenType.OP_GE: "Operator(>=)",
    TokenType.OP_LE: "Operator(<=)",
    TokenType.OP_GT: "Operator(>)",
    TokenType.OP_LT: "Operator(<)",
    TokenType.OP_PLUS: "Operator(+)",
    TokenType.OP_MINUS: "Operator(-)",
    TokenType.OP_MULT: "Operator(*)",
    TokenType.OP_DIV: "Operator(/)",
    TokenType.OP_MOD: "Operator(%)",
    TokenType.SYM_LPAREN: "Operator(()",
    TokenType.SYM_RPAREN: "Operator())",
    TokenType.SYM_LBRACK: "Operator([)",
    TokenType.SYM_RBRACK: "Operator(])",
    TokenType.SYM_LBRACE: "Operator({)",
    TokenType.SYM_RBRACE: "Operator(})",
    TokenType.SYM_ASSIGN: "Operator(=)",
    TokenType.SYM_SEMICOL: "Operator(;)",
    TokenType.SYM_COMMA: "Operator(,)",
    TokenType.SYM_DOT: "Operator(.)",
    TokenType.COMMENT: "Comment",
    TokenType.UNKNOWN: "Unknown",
}


def grammar_symbol_to_display(symbol: str) -> str:
    mapping = {
        "KW_PROGRAM": "program",
        "KW_CLASS": "class",
        "KW_IF": "if",
        "KW_ELSE": "else",
        "KW_WHILE": "while",
        "KW_READ": "read",
        "KW_PRINT": "print",
        "KW_RETURN": "return",
        "KW_VOID": "void",
        "KW_FINAL": "final",
        "KW_NEW": "new",
        "OP_EQ": "==",
        "OP_NEQ": "!=",
        "OP_GE": ">=",
        "OP_LE": "<=",
        "OP_GT": ">",
        "OP_LT": "<",
        "OP_PLUS": "+",
        "OP_MINUS": "-",
        "OP_MULT": "*",
        "OP_DIV": "/",
        "OP_MOD": "%",
        "SYM_LPAREN": "(",
        "SYM_RPAREN": ")",
        "SYM_LBRACK": "[",
        "SYM_RBRACK": "]",
        "SYM_LBRACE": "{",
        "SYM_RBRACE": "}",
        "SYM_ASSIGN": "=",
        "SYM_SEMICOL": ";",
        "SYM_COMMA": ",",
        "SYM_DOT": ".",
    }
    return mapping.get(symbol, symbol)


def grammar_symbols_to_display(symbols: list[str]) -> str:
    if not symbols:
        return "[]"
    if symbols == ["epsilon"]:
        return "[eps]"
    parts = ["eps" if symbol == "epsilon" else grammar_symbol_to_display(symbol) for symbol in symbols]
    return "[" + " ".join(parts) + "]"


def grammar_symbol_set_to_display(symbols: set[str]) -> str:
    return "{ " + ", ".join(sorted(grammar_symbol_to_display(symbol) for symbol in symbols)) + " }"

class Token:
    def __init__(self, type_: TokenType, lexeme: str = "", line: int = 0, col: int = 0):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.col = col

    def type_to_string(self) -> str:
        return TOKEN_NAMES.get(self.type, "Invalid")

    def to_string(self) -> str:
        s = f"[Line {self.line}, Col {self.col}] {self.type_to_string()}"
        if self.type in (TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.CHAR_CONST, TokenType.UNKNOWN):
            s += f" ({self.lexeme})"
        return s

    def to_grammar_symbol(self) -> str:
        mapping = {
            TokenType.EOF: "$",
            TokenType.IDENTIFIER: "id",
            TokenType.NUMBER: "NUMBER",
            TokenType.CHAR_CONST: "CHAR_CONST",
            TokenType.KW_PROGRAM: "KW_PROGRAM",
            TokenType.KW_CLASS: "KW_CLASS",
            TokenType.KW_IF: "KW_IF",
            TokenType.KW_ELSE: "KW_ELSE",
            TokenType.KW_WHILE: "KW_WHILE",
            TokenType.KW_READ: "KW_READ",
            TokenType.KW_PRINT: "KW_PRINT",
            TokenType.KW_RETURN: "KW_RETURN",
            TokenType.KW_VOID: "KW_VOID",
            TokenType.KW_FINAL: "KW_FINAL",
            TokenType.KW_NEW: "KW_NEW",
            TokenType.OP_EQ: "OP_EQ",
            TokenType.OP_NEQ: "OP_NEQ",
            TokenType.OP_GE: "OP_GE",
            TokenType.OP_LE: "OP_LE",
            TokenType.OP_GT: "OP_GT",
            TokenType.OP_LT: "OP_LT",
            TokenType.OP_PLUS: "OP_PLUS",
            TokenType.OP_MINUS: "OP_MINUS",
            TokenType.OP_MULT: "OP_MULT",
            TokenType.OP_DIV: "OP_DIV",
            TokenType.OP_MOD: "OP_MOD",
            TokenType.SYM_LPAREN: "SYM_LPAREN",
            TokenType.SYM_RPAREN: "SYM_RPAREN",
            TokenType.SYM_LBRACK: "SYM_LBRACK",
            TokenType.SYM_RBRACK: "SYM_RBRACK",
            TokenType.SYM_LBRACE: "SYM_LBRACE",
            TokenType.SYM_RBRACE: "SYM_RBRACE",
            TokenType.SYM_ASSIGN: "SYM_ASSIGN",
            TokenType.SYM_SEMICOL: "SYM_SEMICOL",
            TokenType.SYM_COMMA: "SYM_COMMA",
            TokenType.SYM_DOT: "SYM_DOT",
        }
        return mapping.get(self.type, "UNKNOWN")
