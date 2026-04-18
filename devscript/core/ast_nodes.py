from dataclasses import dataclass
from typing import List, Any, Union

@dataclass
class ASTNode:
    pass

@dataclass
class Expr(ASTNode):
    pass

@dataclass
class Stmt(ASTNode):
    pass

# Expressions
@dataclass
class NumberExpr(Expr):
    value: float

@dataclass
class StringExpr(Expr):
    value: str

@dataclass
class VariableExpr(Expr):
    name: str

@dataclass
class BinaryOpExpr(Expr):
    left: Expr
    op: str
    right: Expr

@dataclass
class UnaryOpExpr(Expr):
    op: str
    operand: Expr

@dataclass
class CallExpr(Expr):
    func_name: str
    args: List[Expr]

@dataclass
class ArrayLiteralExpr(Expr):
    elements: List[Expr]


# Statements
@dataclass
class SayStmt(Stmt):
    expr: Expr

@dataclass
class AssignStmt(Stmt):
    name: str
    value: Expr

@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: List[Stmt]
    else_branch: List[Stmt] = None

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: List[Stmt]

@dataclass
class Block(ASTNode):
    statements: List[Stmt]
