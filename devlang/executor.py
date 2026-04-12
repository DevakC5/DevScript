# devlang/executor.py — AST walker / runtime

from __future__ import annotations
from typing import Any

from .nodes import (SayNode, LetNode, InputNode, IfNode, RepeatNode,
                    WhileNode, FuncDefNode, ReturnNode, CallNode, ImportNode, ReturnSignal)
from .evaluator import evaluate, val_to_str, split_args
from .lexer import cast
from .console import con, error, warn

_WHILE_LIMIT = 100_000   # safety cap for while loops


def run_block(ast: list, variables: dict, functions: dict):
    for node in ast:

        if isinstance(node, SayNode):
            val = evaluate(node.expr, variables, node.line, functions)
            con().print(f"  [bold green]>[/bold green] {val_to_str(val)}")

        elif isinstance(node, LetNode):
            variables[node.name] = evaluate(node.expr, variables, node.line, functions)

        elif isinstance(node, InputNode):
            try:
                raw = con().input(f"  [bold cyan]?[/bold cyan] [cyan]{node.prompt}[/cyan] ")
            except (EOFError, KeyboardInterrupt):
                raw = ""
            variables[node.name] = cast(raw)

        elif isinstance(node, IfNode):
            if evaluate(node.cond, variables, node.line, functions):
                run_block(node.body, variables, functions)
            elif node.else_body:
                run_block(node.else_body, variables, functions)

        elif isinstance(node, RepeatNode):
            count_val = evaluate(node.count_expr, variables, node.line, functions)
            try:
                count = int(count_val)
            except (ValueError, TypeError):
                error(f"'repeat' count must be a number, got: {count_val!r}", node.line)
                continue
            if count < 0:
                warn("'repeat' count is negative; skipping.", node.line)
                continue
            for _ in range(count):
                run_block(node.body, variables, functions)

        elif isinstance(node, WhileNode):
            iters = 0
            while evaluate(node.cond, variables, node.line, functions):
                run_block(node.body, variables, functions)
                iters += 1
                if iters >= _WHILE_LIMIT:
                    error(f"'while' exceeded {_WHILE_LIMIT} iterations — possible infinite loop.", node.line)
                    break

        elif isinstance(node, FuncDefNode):
            functions[node.name] = {'params': node.params, 'body': node.body}

        elif isinstance(node, ReturnNode):
            val = evaluate(node.expr, variables, node.line, functions)
            raise ReturnSignal(val)

        elif isinstance(node, ImportNode):
            filepath = evaluate(node.filepath_expr, variables, node.line, functions)
            try:
                from .cache import load_or_parse
                import os
                # Try relative to current dir, then scripts dir (for simple resolution)
                if not os.path.exists(filepath):
                    alt_path = os.path.join("scripts", filepath)
                    if os.path.exists(alt_path):
                        filepath = alt_path
                lib_ast = load_or_parse(filepath)
                run_block(lib_ast, variables, functions)
            except Exception as e:
                error(f"Failed to import '{filepath}': {e}", node.line)

        elif isinstance(node, CallNode):
            arg_vals = [evaluate(a.strip(), variables, node.line, functions)
                        for a in split_args(node.args)] if node.args else []
            if node.name in functions:
                call_function(node.name, arg_vals, functions, node.line)
            else:
                error(f"Undefined function: '{node.name}'", node.line)


def call_function(name: str, arg_vals: list, functions: dict, line_no: int) -> Any:
    func = functions[name]
    if len(arg_vals) != len(func['params']):
        error(
            f"Function '{name}' expects {len(func['params'])} arg(s), "
            f"got {len(arg_vals)}.",
            line_no
        )
        return ""
    local_vars = dict(zip(func['params'], arg_vals))
    try:
        run_block(func['body'], local_vars, functions)
    except ReturnSignal as r:
        return r.value
    return ""