from typing import Any, List
from devscript.core.ast_nodes import (
    ASTNode, Expr, Stmt, NumberExpr, StringExpr, VariableExpr,
    BinaryOpExpr, UnaryOpExpr, CallExpr, SayStmt,
    AssignStmt, IfStmt, WhileStmt, Block, ArrayLiteralExpr
)
from devscript.core.environment import Environment
from devscript.utils.errors import RuntimeError
from devscript.stdlib.arraylib import DevArray

class Interpreter:
    def __init__(self, globals_env: Environment):
        self.env = globals_env

    def interpret(self, block: Block):
        for stmt in block.statements:
            self.execute(stmt)

    def execute(self, node: ASTNode):
        if isinstance(node, Block):
            for stmt in node.statements:
                self.execute(stmt)
        elif isinstance(node, SayStmt):
            value = self.evaluate(node.expr)
            print(value)
        elif isinstance(node, AssignStmt):
            value = self.evaluate(node.value)
            self.env.define(node.name, value)
        elif isinstance(node, IfStmt):
            condition = self.evaluate(node.condition)
            if condition:
                for stmt in node.then_branch:
                    self.execute(stmt)
            elif node.else_branch:
                for stmt in node.else_branch:
                    self.execute(stmt)
        elif isinstance(node, WhileStmt):
            while self.evaluate(node.condition):
                # To support 'break' or similar in the future, we might need a different loop
                for stmt in node.body:
                    self.execute(stmt)
        else:
            raise RuntimeError(f"Unknown statement type: {type(node).__name__}")

    def evaluate(self, node: Expr) -> Any:
        if isinstance(node, NumberExpr):
            return node.value
        elif isinstance(node, StringExpr):
            return node.value
        elif isinstance(node, VariableExpr):
            val = self.env.get(node.name)
            if val is None:
                raise RuntimeError(f"Undefined variable: {node.name}")
            return val
        elif isinstance(node, ArrayLiteralExpr):
            elements = [self.evaluate(e) for e in node.elements]
            return DevArray(elements)
        elif isinstance(node, BinaryOpExpr):
            return self._eval_binary(node)
        elif isinstance(node, UnaryOpExpr):
            return self._eval_unary(node)
        elif isinstance(node, CallExpr):
            return self._eval_call(node)
        else:
            raise RuntimeError(f"Unknown expression type: {type(node).__name__}")

    def _eval_binary(self, node: BinaryOpExpr) -> Any:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.op

        try:
            if op == '+': return left + right
            if op == '-': return left - right
            if op == '*': return left * right
            if op == '/': 
                if right == 0: raise RuntimeError("Division by zero")
                return left / right
            if op == '%': return left % right
            if op == '^': return left ** right
            if op == '==': return left == right
            if op == '!=': return left != right
            if op == '>': return left > right
            if op == '<': return left < right
            if op == '>=': return left >= right
            if op == '<=': return left <= right
        except TypeError as e:
            raise RuntimeError(f"Type error: {e}")
        
        raise RuntimeError(f"Unknown operator: {op}")

    def _eval_unary(self, node: UnaryOpExpr) -> Any:
        operand = self.evaluate(node.operand)
        op = node.op
        if op == '+': return +operand
        if op == '-': return -operand
        raise RuntimeError(f"Unknown unary operator: {op}")

    def _eval_call(self, node: CallExpr) -> Any:
        func = self.env.get(node.func_name)
        if func is None or not callable(func):
            raise RuntimeError(f"Undefined function: {node.func_name}")
        
        args = [self.evaluate(arg) for arg in node.args]
        try:
            return func(*args)
        except Exception as e:
            raise RuntimeError(f"Error calling function {node.func_name}: {e}")
