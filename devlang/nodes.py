# devlang/nodes.py — AST node definitions

class SayNode:
    __slots__ = ('expr', 'line')
    def __init__(self, e, l): self.expr = e;  self.line = l

class LetNode:
    __slots__ = ('name', 'expr', 'line')
    def __init__(self, n, e, l): self.name = n; self.expr = e; self.line = l

class InputNode:
    __slots__ = ('name', 'prompt', 'line')
    def __init__(self, n, p, l): self.name = n; self.prompt = p; self.line = l

class IfNode:
    __slots__ = ('cond', 'body', 'else_body', 'line')
    def __init__(self, c, b, eb, l): self.cond = c; self.body = b; self.else_body = eb; self.line = l

class RepeatNode:
    __slots__ = ('count_expr', 'body', 'line')
    def __init__(self, c, b, l): self.count_expr = c; self.body = b; self.line = l

class WhileNode:
    __slots__ = ('cond', 'body', 'line')
    def __init__(self, c, b, l): self.cond = c; self.body = b; self.line = l

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

class ReturnSignal(Exception):
    """Used to unwind the call stack when 'return' is hit."""
    def __init__(self, value):
        self.value = value