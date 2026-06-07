from __future__ import annotations

from enum import Enum


class ErrorType(Enum):
    LEXICAL = "Lexical Error"
    SYNTAX = "Syntax Error"
    SEMANTIC = "Semantic Error"


class CompilerError:
    def __init__(self, type_, message, line, col, recovery_action=""):
        self.type = type_
        self.message = message
        self.line = line
        self.col = col
        self.recovery_action = recovery_action

    def to_string(self):
        msg = f"[{self.type.value}] Line {self.line}, Col {self.col}: {self.message}"
        if self.recovery_action:
            msg += f" | Recovery: {self.recovery_action}"
        return msg

    def to_dict(self):
        return {
            "type": self.type.value,
            "message": self.message,
            "line": self.line,
            "col": self.col,
            "recovery_action": self.recovery_action,
        }


class ErrorHandler:

    def __init__(self):
        self.errors = []
        self.panic_mode = False

    def report(
            self,
            type_,
            message,
            line,
            col,
            recovery_action=""
    ):
        err = CompilerError(
            type_,
            message,
            line,
            col,
            recovery_action
        )
        self.errors.append(err)
        return err

    def enter_panic_mode(self):
        self.panic_mode = True

    def exit_panic_mode(self):
        self.panic_mode = False

    def is_panic_mode(self):
        return self.panic_mode

    def has_errors(self):
        return len(self.errors) > 0

    def error_count(self):
        return len(self.errors)

    def get_errors(self):
        return self.errors

    def clear(self):
        self.errors.clear()
        self.panic_mode = False

    def get_summary(self):

        lexical = sum(
            1 for e in self.errors
            if e.type == ErrorType.LEXICAL
        )

        syntax = sum(
            1 for e in self.errors
            if e.type == ErrorType.SYNTAX
        )

        semantic = sum(
            1 for e in self.errors
            if e.type == ErrorType.SEMANTIC
        )

        return {
            "total": len(self.errors),
            "lexical": lexical,
            "syntax": syntax,
            "semantic": semantic,
        }