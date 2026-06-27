# devlang/executor.py — AST walker / runtime

from __future__ import annotations
import sys
from typing import Any

from .nodes import (SayNode, LetNode, InputNode, IfNode, RepeatNode,
                    WhileNode, ForNode, FuncDefNode, ReturnNode, CallNode,
                    ImportNode, BreakNode, ContinueNode, ExprNode,
                    StructDefNode, EnumDefNode, StructInstance, SpawnNode,
                    AsyncFuncDefNode, AsyncAwaitNode,
                    ReturnSignal, BreakSignal, ContinueSignal)
from .evaluator import evaluate, val_to_str, split_args, Coro
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
            prompt_str = f"  [bold cyan]?[/bold cyan] [cyan]{node.prompt}[/cyan] "
            try:
                if node.mask:
                    raw = con().input(prompt_str, password=True)
                else:
                    raw = con().input(prompt_str)
            except (EOFError, KeyboardInterrupt):
                raw = node.default if node.default is not None else ""
            if not raw and node.default is not None:
                raw = node.default
            if node.as_type == 'num':
                try:
                    variables[node.name] = int(raw) if '.' not in raw else float(raw)
                except (ValueError, TypeError):
                    variables[node.name] = cast(raw)
            else:
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
                try:
                    run_block(node.body, variables, functions)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif isinstance(node, WhileNode):
            iters = 0
            while evaluate(node.cond, variables, node.line, functions):
                try:
                    run_block(node.body, variables, functions)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
                iters += 1
                if iters >= _WHILE_LIMIT:
                    error(f"'while' exceeded {_WHILE_LIMIT} iterations — possible infinite loop.", node.line)
                    break

        elif isinstance(node, ForNode):
            iterable = evaluate(node.iterable_expr, variables, node.line, functions)
            if isinstance(iterable, (int, float)):
                iterable = list(range(int(iterable)))
            if not isinstance(iterable, (list, str)):
                error(f"'for' loop expects a list, string, or number, got: {type(iterable).__name__}", node.line)
                continue
            for item in iterable:
                variables[node.var_name] = item
                try:
                    run_block(node.body, variables, functions)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif isinstance(node, FuncDefNode):
            functions[node.name] = {'params': node.params, 'body': node.body}

        elif isinstance(node, StructDefNode):
            functions[node.name] = {'_struct_fields': node.fields, 'line': node.line}

        elif isinstance(node, EnumDefNode):
            for val in node.values:
                variables[val] = node.name + '.' + val
            functions[node.name] = {'_enum_values': node.values, 'line': node.line}

        elif isinstance(node, SpawnNode):
            import threading as _thr
            def _spawn_target(f=functions, v=variables.copy(), b=node.body):
                try:
                    run_block(b, v, f)
                except Exception:
                    pass
            t = _thr.Thread(target=_spawn_target, daemon=True)
            t.start()
            variables['_last_spawn'] = t

        elif isinstance(node, AsyncFuncDefNode):
            functions[node.name] = {'_async': True, 'params': node.params, 'body': node.body}

        elif isinstance(node, AsyncAwaitNode):
            val = evaluate(node.expr, variables, node.line, functions)
            if isinstance(val, Coro):
                val.start()
                result = val.join()
                if result is not None:
                    pass  # result stored in coroutine
            elif isinstance(val, dict) and '_coro' in val:
                val['_coro'].start()
                val['_coro'].join()

        elif isinstance(node, ReturnNode):
            val = evaluate(node.expr, variables, node.line, functions)
            raise ReturnSignal(val)

        elif isinstance(node, BreakNode):
            raise BreakSignal()

        elif isinstance(node, ContinueNode):
            raise ContinueSignal()

        elif isinstance(node, ImportNode):
            filepath = evaluate(node.filepath_expr, variables, node.line, functions)
            try:
                from .cache import load_or_parse
                import os
                # Ensure .dev extension
                search = filepath if filepath.endswith('.dev') else filepath + '.dev'
                found_path = search
                if not os.path.exists(found_path):
                    script_dir = os.path.dirname(os.path.abspath(sys.argv[2])) if len(sys.argv) > 2 else "."
                    for folder in [script_dir, "libs", "scripts"]:
                        alt_path = os.path.join(folder, search)
                        if os.path.exists(alt_path):
                            found_path = alt_path
                            break
                if not os.path.exists(found_path):
                    raise FileNotFoundError(f"Could not find '{filepath}'")
                # Circular import detection
                import_stack = getattr(run_block, '_import_stack', set())
                abs_path = os.path.abspath(found_path)
                if abs_path in import_stack:
                    error(f"Circular import detected: '{filepath}'", node.line)
                    continue
                import_stack.add(abs_path)
                run_block._import_stack = import_stack
                try:
                    lib_ast = load_or_parse(found_path)
                    run_block(lib_ast, variables, functions)
                finally:
                    run_block._import_stack.discard(abs_path)
            except Exception as e:
                error(f"Failed to import '{filepath}': {e}", node.line)

        elif isinstance(node, ExprNode):
            evaluate(node.expr, variables, node.line, functions)

        elif isinstance(node, CallNode):
            arg_vals = [evaluate(a.strip(), variables, node.line, functions)
                        for a in split_args(node.args)] if node.args else []
            if node.name in functions:
                func = functions[node.name]
                if '_enum_values' in func:
                    error(f"'enum' type '{node.name}' cannot be called as a function", node.line)
                else:
                    call_function(node.name, arg_vals, functions, node.line)
            else:
                from .evaluator import BUILTINS
                if node.name in BUILTINS:
                    try:
                        BUILTINS[node.name](*arg_vals)
                    except Exception as e:
                        error(f"Error in built-in '{node.name}': {e}", node.line)
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
