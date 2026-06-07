from __future__ import annotations

from enum import Enum, auto


class ASTNodeType(Enum):
    PROGRAM = "Program"
    CONST_DECL = "ConstDecl"
    VAR_DECL = "VarDecl"
    CLASS_DECL = "ClassDecl"
    METHOD_DECL = "MethodDecl"
    PARAMETER = "Parameter"
    BLOCK = "Block"
    ASSIGN_STMT = "AssignStmt"
    CALL_STMT = "CallStmt"
    IF_STMT = "IfStmt"
    WHILE_STMT = "WhileStmt"
    RETURN_STMT = "ReturnStmt"
    READ_STMT = "ReadStmt"
    PRINT_STMT = "PrintStmt"
    EMPTY_STMT = "EmptyStmt"
    DESIGNATOR = "Designator"
    BINARY_OP = "BinaryOp"
    UNARY_OP = "UnaryOp"
    NUMBER_LITERAL = "Number"
    CHAR_LITERAL = "CharConst"
    IDENTIFIER = "Identifier"
    NEW_EXPR = "NewExpr"
    CONDITION = "Condition"
    TYPE_NODE = "Type"


class ASTNode:
    def __init__(self, node_type: ASTNodeType, **kwargs):
        self.node_type = node_type
        self.children = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add_child(self, child: ASTNode | None):
        if child is not None:
            self.children.append(child)

    def to_dict(self) -> dict:
        result = {"type": self.node_type.value}
        for attr in ("name", "value", "op", "line", "col", "return_type", "width"):
            if hasattr(self, attr):
                v = getattr(self, attr)
                if v is not None:
                    result[attr] = v
        if hasattr(self, "data_type") and self.data_type:
            result["data_type"] = self.data_type
        if hasattr(self, "names") and self.names:
            result["names"] = self.names
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result

    def __repr__(self):
        return f"ASTNode({self.node_type.value})"


def make_node(node_type: ASTNodeType, **kwargs) -> ASTNode:
    return ASTNode(node_type, **kwargs)
