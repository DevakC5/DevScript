# devlang/nodes.py — AST node definitions

class SayNode:
    __slots__ = ('expr', 'line')
    def __init__(self, e, l): self.expr = e;  self.line = l

class LetNode:
    __slots__ = ('name', 'expr', 'line')
    def __init__(self, n, e, l): self.name = n; self.expr = e; self.line = l

class InputNode:
    __slots__ = ('name', 'prompt', 'line', 'as_type', 'default', 'mask')
    def __init__(self, n, p, l, as_type=None, default=None, mask=False):
        self.name = n; self.prompt = p; self.line = l
        self.as_type = as_type; self.default = default; self.mask = mask

class IfNode:
    __slots__ = ('cond', 'body', 'else_body', 'line')
    def __init__(self, c, b, eb, l): self.cond = c; self.body = b; self.else_body = eb; self.line = l

class RepeatNode:
    __slots__ = ('count_expr', 'body', 'line')
    def __init__(self, c, b, l): self.count_expr = c; self.body = b; self.line = l

class WhileNode:
    __slots__ = ('cond', 'body', 'line')
    def __init__(self, c, b, l): self.cond = c; self.body = b; self.line = l

class ForNode:
    __slots__ = ('var_name', 'iterable_expr', 'body', 'line')
    def __init__(self, v, i, b, l): self.var_name = v; self.iterable_expr = i; self.body = b; self.line = l

class FuncDefNode:
    __slots__ = ('name', 'params', 'body', 'line')
    def __init__(self, n, p, b, l): self.name = n; self.params = p; self.body = b; self.line = l

class ReturnNode:
    __slots__ = ('expr', 'line')
    def __init__(self, e, l): self.expr = e; self.line = l

class CallNode:
    __slots__ = ('name', 'args', 'line')
    def __init__(self, n, a, l): self.name = n; self.args = a; self.line = l

class ImportNode:
    __slots__ = ('filepath_expr', 'line')
    def __init__(self, f, l): self.filepath_expr = f; self.line = l

class ExprNode:
    """Evaluate an expression for side-effects, discard result."""
    __slots__ = ('expr', 'line')
    def __init__(self, e, l): self.expr = e; self.line = l

class BreakNode:
    __slots__ = ('line',)
    def __init__(self, l): self.line = l

class ContinueNode:
    __slots__ = ('line',)
    def __init__(self, l): self.line = l

class StructDefNode:
    __slots__ = ('name', 'fields', 'line')
    def __init__(self, n, f, l):
        self.name = n; self.fields = f; self.line = l
        # fields: list of (field_name, default_expr_string)

class EnumDefNode:
    __slots__ = ('name', 'values', 'line')
    def __init__(self, n, v, l):
        self.name = n; self.values = v; self.line = l
        # values: list of strings


class SpawnNode:
    __slots__ = ('body', 'line')
    def __init__(self, b, l):
        self.body = b; self.line = l

class AsyncFuncDefNode:
    __slots__ = ('name', 'params', 'body', 'line')
    def __init__(self, n, p, b, l):
        self.name = n; self.params = p; self.body = b; self.line = l

class AsyncAwaitNode:
    __slots__ = ('expr', 'line')
    def __init__(self, e, l):
        self.expr = e; self.line = l

class StructInstance:
    __slots__ = ('_fields',)
    def __init__(self, fields: dict):
        object.__setattr__(self, '_fields', fields)

    def __getattr__(self, name):
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(f"No field '{name}'")

    def __setattr__(self, name, value):
        self._fields[name] = value

    def __repr__(self):
        parts = ", ".join(f"{k}={v!r}" for k, v in self._fields.items())
        return "{" + parts + "}"


class ReturnSignal(Exception):
    """Used to unwind the call stack when 'return' is hit."""
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    """Unwind loop on 'break'."""

class ContinueSignal(Exception):
    """Skip to next loop iteration on 'continue'."""