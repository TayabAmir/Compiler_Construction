from __future__ import annotations

from enum import Enum


class ErrorType(Enum):
    LEXICAL = "Lexical Error"
    SYNTAX = "Syntax Error"
    SEMANTIC = "Semantic Error"


class CompilerError:
    def __init__(self, type_: ErrorType, message: str, line: int, col: int):
        self.type = type_
        self.message = message
        self.line = line
        self.col = col

    def to_string(self) -> str:
        return f"[{self.type.value}] Line {self.line}, Col {self.col}: {self.message}"

    def to_dict(self):
        return {
            "type": self.type.value,
            "message": self.message,
            "line": self.line,
            "col": self.col,
        }


class ErrorHandler:
    def __init__(self):
        self.errors: list[CompilerError] = []
        self.panic_mode = False

    def report(self, type_: ErrorType, message: str, line: int, col: int):
        err = CompilerError(type_, message, line, col)
        self.errors.append(err)
        return err

    def set_panic_mode(self, mode: bool):
        self.panic_mode = mode

    def is_panic_mode(self) -> bool:
        return self.panic_mode

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def error_count(self) -> int:
        return len(self.errors)

    def get_errors(self) -> list[CompilerError]:
        return self.errors

    def get_summary(self) -> dict:
        lexical = sum(1 for e in self.errors if e.type == ErrorType.LEXICAL)
        syntax = sum(1 for e in self.errors if e.type == ErrorType.SYNTAX)
        semantic = sum(1 for e in self.errors if e.type == ErrorType.SEMANTIC)
        return {
            "total": len(self.errors),
            "lexical": lexical,
            "syntax": syntax,
            "semantic": semantic,
        }

    def clear(self):
        self.errors.clear()
        self.panic_mode = False
