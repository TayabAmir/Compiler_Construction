from __future__ import annotations

from enum import Enum


class IdentifierKind(Enum):
    VARIABLE = 0
    CONSTANT = 1
    FUNCTION = 2
    ARRAY = 3
    CLASS = 4
    PARAMETER = 5


class DataType(Enum):
    INT = 0
    CHAR = 1
    REAL = 2
    BOOL = 3
    VOID = 4
    USER_DEFINED = 5


KIND_NAMES = {
    IdentifierKind.VARIABLE: "variable",
    IdentifierKind.CONSTANT: "constant",
    IdentifierKind.FUNCTION: "function",
    IdentifierKind.ARRAY: "array",
    IdentifierKind.CLASS: "class",
    IdentifierKind.PARAMETER: "parameter",
}

TYPE_NAMES = {
    DataType.INT: "int",
    DataType.CHAR: "char",
    DataType.REAL: "real",
    DataType.BOOL: "bool",
    DataType.VOID: "void",
    DataType.USER_DEFINED: "user-defined",
}


TABLE_SIZE = 211


class Entry:
    def __init__(self, name: str, kind: IdentifierKind, dtype: DataType, scope_level: int, line: int):
        self.name = name
        self.kind = kind
        self.type = dtype
        self.scope_level = scope_level
        self.line = line
        self.offset = 0
        self.next: Entry | None = None


class SymTable:
    def __init__(self, parent: "SymTable | None" = None):
        self.slots: list[Entry | None] = [None] * TABLE_SIZE
        self.parent = parent
        self.scope_level = 0 if parent is None else parent.scope_level + 1
        self.entry_count = 0

    def _hash(self, name: str) -> int:
        h = 5381
        for c in name:
            h = ((h << 5) + h) + ord(c)
        return h % TABLE_SIZE

    def insert(self, name: str, kind: IdentifierKind, dtype: DataType, line: int) -> Entry | None:
        if self.lookup_current(name) is not None:
            return None
        h = self._hash(name)
        e = Entry(name, kind, dtype, self.scope_level, line)
        e.next = self.slots[h]
        self.slots[h] = e
        self.entry_count += 1
        return e

    def lookup_current(self, name: str) -> Entry | None:
        h = self._hash(name)
        e = self.slots[h]
        while e is not None:
            if e.name == name:
                return e
            e = e.next
        return None

    def lookup(self, name: str) -> Entry | None:
        current: SymTable | None = self
        while current is not None:
            e = current.lookup_current(name)
            if e is not None:
                return e
            current = current.parent
        return None

    def delete_entry(self, name: str) -> bool:
        h = self._hash(name)
        current = self.slots[h]
        prev = None
        while current is not None:
            if current.name == name:
                if prev is None:
                    self.slots[h] = current.next
                else:
                    prev.next = current.next
                self.entry_count -= 1
                return True
            prev = current
            current = current.next
        return False

    def get_entries(self) -> list[Entry]:
        entries = []
        for i in range(TABLE_SIZE):
            e = self.slots[i]
            while e is not None:
                entries.append(e)
                e = e.next
        return entries


class ScopeManager:
    def __init__(self):
        self.current_scope: SymTable | None = None
        self.total_entries = 0
        self.all_scopes: list[SymTable] = []
        self.begin_scope()

    def begin_scope(self):
        new_scope = SymTable(self.current_scope)
        self.current_scope = new_scope
        self.all_scopes.append(new_scope)

    def end_scope(self):
        if self.current_scope is None:
            return
        self.current_scope = self.current_scope.parent

    def insert(self, name: str, kind: IdentifierKind, dtype: DataType, line: int) -> Entry | None:
        if self.current_scope is None:
            return None
        result = self.current_scope.insert(name, kind, dtype, line)
        if result is not None:
            self.total_entries += 1
        return result

    def lookup(self, name: str) -> Entry | None:
        if self.current_scope is None:
            return None
        return self.current_scope.lookup(name)

    def lookup_current(self, name: str) -> Entry | None:
        if self.current_scope is None:
            return None
        return self.current_scope.lookup_current(name)

    def get_current_scope_level(self) -> int:
        if self.current_scope is None:
            return -1
        return self.current_scope.scope_level

    def get_all_scopes_data(self) -> list[dict]:
        scopes_data = []
        for scope in self.all_scopes:
            entries = scope.get_entries()
            entries_data = []
            for idx, e in enumerate(entries, 1):
                entries_data.append({
                    "id": idx,
                    "name": e.name,
                    "kind": KIND_NAMES.get(e.kind, "unknown"),
                    "type": TYPE_NAMES.get(e.type, "unknown"),
                    "scope": e.scope_level,
                    "line": e.line,
                })
            scopes_data.append({
                "scope_level": scope.scope_level,
                "entries": entries_data,
                "entry_count": scope.entry_count,
            })
        return scopes_data

    def reset(self):
        while self.current_scope is not None:
            self.current_scope = self.current_scope.parent
        self.total_entries = 0
        self.all_scopes.clear()
        self.begin_scope()
