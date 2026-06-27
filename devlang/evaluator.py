# devlang/evaluator.py — expression evaluator

from __future__ import annotations
import operator
import re
from typing import Any

from .lexer import cast
from .console import error
from .nodes import StructInstance
from . import charts as _charts
from . import img as _img

_RAW_OPS: dict[str, Any] = {
    '+':  operator.add,  '-':  operator.sub,
    '*':  operator.mul,  '/':  operator.truediv,
    '%':  operator.mod,  '**': operator.pow,
    '>':  operator.gt,   '<':  operator.lt,
    '>=': operator.ge,   '<=': operator.le,
    '==': operator.eq,   '!=': operator.ne,
}

def _vectorized_op(op_func, a, b):
    # Fast path for flat lists
    if isinstance(a, list):
        if isinstance(b, list):
            if len(a) != len(b):
                raise ValueError(f"Shape mismatch: {len(a)} vs {len(b)}")
            if not a or not isinstance(a[0], list):
                return [op_func(x, y) for x, y in zip(a, b)]
            return [_vectorized_op(op_func, x, y) for x, y in zip(a, b)]
        if not a or not isinstance(a[0], list):
            return [op_func(x, b) for x in a]
        return [_vectorized_op(op_func, x, b) for x in a]
    if isinstance(b, list):
        if not b or not isinstance(b[0], list):
            return [op_func(a, y) for y in b]
        return [_vectorized_op(op_func, a, y) for y in b]
    return op_func(a, b)

_OPS: dict[str, Any] = {
    k: (lambda a, b, op=v: _vectorized_op(op, a, b)) for k, v in _RAW_OPS.items()
}

_PREC = [
    ['>=', '<=', '==', '!=', '>', '<'],
    ['+', '-'],
    ['*', '/', '%'],
    ['**'],
]


def _split_outside_quotes(expr: str, op: str, from_right: bool = False):
    in_q, q_char, idxs, depth, p_depth = False, '', [], 0, 0
    i = 0
    while i < len(expr):
        ch = expr[i]
        if in_q:
            if ch == q_char: in_q = False
        else:
            if ch in ('"', "'"):
                in_q, q_char = True, ch
            elif ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
            elif ch == '(':
                p_depth += 1
            elif ch == ')':
                p_depth -= 1
            elif depth == 0 and p_depth == 0 and expr[i:i + len(op)] == op:
                if len(op) == 1 and op == '*':
                    if (i + 1 < len(expr) and expr[i + 1] == '*') or (i > 0 and expr[i - 1] == '*'):
                        i += 1; continue
                idxs.append(i)
        i += 1
    if not idxs: return None
    idx   = idxs[-1] if from_right else idxs[0]
    left  = expr[:idx].strip()
    right = expr[idx + len(op):].strip()
    return [left, right] if left and right else None


def split_args(s: str) -> list[str]:
    args, depth, b_depth, cur, in_q, q_char = [], 0, 0, [], False, ''
    for ch in s:
        if in_q:
            cur.append(ch)
            if ch == q_char: in_q = False
        elif ch in ('"', "'"):
            in_q, q_char = True, ch; cur.append(ch)
        elif ch in ('(', '['):
            if ch == '(': depth += 1
            else: b_depth += 1
            cur.append(ch)
        elif ch in (')', ']'):
            if ch == ')': depth -= 1
            else: b_depth -= 1
            cur.append(ch)
        elif ch == ',' and depth == 0 and b_depth == 0:
            args.append(''.join(cur)); cur = []
        else:
            cur.append(ch)
    if cur: args.append(''.join(cur))
    return args

import time
import ctypes
import os
import sys
import math as _real_math
import random as _real_random
import builtins as _real_builtins
import threading as _threading

# Attempt to load C extension for math/matrix optimization
_c_math = None
try:
    _ext = ".dll" if sys.platform == "win32" else ".so"
    _lib_path = os.path.join(os.path.dirname(__file__), f"devmath{_ext}")
    if os.path.exists(_lib_path):
        _c_math = ctypes.CDLL(_lib_path)
        _c_math.matrix_mul.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_int]
except Exception:
    pass

def _matmul(A, B):
    if not isinstance(A, list) or not isinstance(B, list): return 0
    if not A or not isinstance(A[0], list): return 0
    if not B or not isinstance(B[0], list): return 0
    
    m, n = len(A), len(A[0])
    p = len(B[0])
    if len(B) != n: error("Matrix inner dimensions must match", 0); return []
    
    if _c_math is not None:
        # C-accelerated Matrix Multiplication
        flat_A = (ctypes.c_double * (m * n))(*[val for row in A for val in row])
        flat_B = (ctypes.c_double * (n * p))(*[val for row in B for val in row])
        flat_out = (ctypes.c_double * (m * p))()
        _c_math.matrix_mul(flat_A, flat_B, flat_out, m, n, p)
        
        out = []
        for i in range(m):
            out.append([flat_out[i * p + j] for j in range(p)])
        return out
    else:
        # Pure Python Matrix Multiplication (Optimized list comp)
        return [[sum(a * b for a, b in zip(A_row, B_col)) for B_col in zip(*B)] for A_row in A]

def _safe_file_read(p):
    try:
        with open(p, 'r') as f:
            return f.read()
    except Exception as e:
        return f"[Error reading '{p}': {e}]"

def _safe_file_write(p, c):
    try:
        with open(p, 'w') as f:
            f.write(str(c))
        return True
    except Exception as e:
        return f"[Error writing '{p}': {e}]"

# ── Matrix class ────────────────────────────────────────────────────

class Matrix:
    def __init__(self, data):
        self._data = [list(row) for row in data]
        self.rows = len(self._data)
        self.cols = len(self._data[0]) if self._data else 0

    @property
    def shape(self):
        return (self.rows, self.cols)

    @property
    def T(self):
        return Matrix(list(zip(*self._data)))

    def dot(self, other):
        if not isinstance(other, Matrix):
            other = Matrix(other)
        if self.cols != other.rows:
            error(f"Matrix dot: inner dims must match ({self.cols} vs {other.rows})", 0)
            return Matrix([])
        result = [[sum(a * b for a, b in zip(self_row, other_col))
                   for other_col in zip(*other._data)]
                  for self_row in self._data]
        return Matrix(result)

    def apply(self, fn):
        from .executor import call_function
        result = [[0.0] * self.cols for _ in range(self.rows)]
        for i in range(self.rows):
            for j in range(self.cols):
                result[i][j] = call_function(str(fn), [self._data[i][j]], {}, 0)
        return Matrix(result)

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Matrix([[v + other for v in row] for row in self._data])
        if isinstance(other, Matrix):
            return Matrix([[self._data[i][j] + other._data[i][j]
                           for j in range(self.cols)] for i in range(self.rows)])
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return Matrix([[v - other for v in row] for row in self._data])
        if isinstance(other, Matrix):
            return Matrix([[self._data[i][j] - other._data[i][j]
                           for j in range(self.cols)] for i in range(self.rows)])
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Matrix([[v * other for v in row] for row in self._data])
        if isinstance(other, Matrix):
            return Matrix([[self._data[i][j] * other._data[i][j]
                           for j in range(self.cols)] for i in range(self.rows)])
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Matrix([[v / other for v in row] for row in self._data])
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return Matrix([[other - v for v in row] for row in self._data])
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __repr__(self):
        widths = [max(len(f"{self._data[i][j]:g}") for i in range(self.rows))
                  for j in range(self.cols)]
        lines = []
        for row in self._data:
            lines.append("  [" + ", ".join(f"{v:>{widths[j]}g}" for j, v in enumerate(row)) + "]")
        return "Matrix(" + str(self.rows) + "x" + str(self.cols) + ")\n" + "\n".join(lines)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, idx):
        return self._data[idx]

    def __len__(self):
        return self.rows


def _matrix(data) -> Matrix:
    if isinstance(data, Matrix):
        return data
    return Matrix(data)


def _zeros_matrix(rows: int, cols: int) -> Matrix:
    return Matrix([[0.0] * int(cols) for _ in range(int(rows))])


def _identity(n: int) -> Matrix:
    n = int(n)
    return Matrix([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])

def _thread_join(handle) -> str:
    import threading
    if isinstance(handle, threading.Thread):
        handle.join()
    return ""


    n = int(n)
    return Matrix([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])


# ── Coroutine (async) ─────────────────────────────────────────────

class Coro:
    def __init__(self, name, args, body, params, functions, line):
        self.name = name; self.args = args; self.body = body
        self.params = params; self.functions = functions; self.line = line
        self.result = None
        self._thread = None

    def start(self):
        import threading
        def _run():
            from .executor import run_block, ReturnSignal
            local_vars = dict(zip(self.params, self.args))
            try:
                run_block(self.body, local_vars, self.functions)
            except ReturnSignal as r:
                self.result = r.value
            except Exception as e:
                from .console import error
                error(f"Async '{self.name}': {e}", self.line)
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def join(self):
        if self._thread:
            self._thread.join()
        return self.result

# ── JSON helpers ───────────────────────────────────────────────────

def _json_loads(s: str):
    import json as _json
    return _json.loads(str(s))

def _json_dumps(v) -> str:
    import json as _json
    return _json.dumps(v, indent=2)

def _json_read(path: str) -> str:
    try:
        with open(str(path), 'r') as f:
            return _json_loads(f.read())
    except Exception as e:
        return f"[Error reading JSON '{path}': {e}]"

# ── CSV helpers ────────────────────────────────────────────────────

def _csv_parse(s: str) -> list:
    import csv as _csv
    import io as _io
    return list(_csv.reader(_io.StringIO(str(s))))

def _csv_read(path: str) -> list:
    import csv as _csv
    try:
        with open(str(path), 'r', newline='') as f:
            return list(_csv.reader(f))
    except Exception as e:
        return f"[Error reading CSV '{path}': {e}]"

def _csv_write(path: str, rows: list) -> bool:
    import csv as _csv
    try:
        with open(str(path), 'w', newline='') as f:
            w = _csv.writer(f)
            for row in rows:
                w.writerow([str(c) for c in (row if isinstance(row, list) else [row])])
        return True
    except Exception as e:
        return f"[Error writing CSV '{path}': {e}]"

# ── Interactive terminal UI helpers ───────────────────────────────

def _interactive_menu(prompt: str, options: list) -> str:
    from rich.prompt import Prompt
    return Prompt.ask(str(prompt), choices=[str(o) for o in options])

def _interactive_confirm(prompt: str) -> bool:
    from rich.prompt import Confirm
    return Confirm.ask(str(prompt))

def _interactive_password(prompt: str) -> str:
    from rich.prompt import Prompt
    return Prompt.ask(str(prompt), password=True)

def _display_table(headers: list, rows: list) -> str:
    from rich.table import Table
    from devlang.console import con
    t = Table(*[str(h) for h in headers])
    for row in rows:
        t.add_row(*[str(c) for c in (row if isinstance(row, list) else [row])])
    con().print(t)
    return ""

def _display_panel(content: str, title: str = "") -> str:
    from rich.panel import Panel
    from devlang.console import con
    con().print(Panel(str(content), title=str(title) if title else None, border_style="cyan"))
    return str(content)

def _display_tree(data: list, title: str = "") -> str:
    from rich.tree import Tree
    from devlang.console import con
    t = Tree(str(title) if title else "Tree")
    for item in data:
        t.add(str(item))
    con().print(t)
    return ""

_ProgressContext = None
_ProgressTasks: dict[int, tuple] = {}
_ProgressCounter = 0

def _progress_start(desc: str, total: int) -> int:
    global _ProgressContext, _ProgressCounter
    if _ProgressContext is None:
        from rich.progress import Progress
        _ProgressContext = Progress()
        _ProgressContext.start()
    _ProgressCounter += 1
    tid = _ProgressCounter
    task_id = _ProgressContext.add_task(str(desc), total=int(total))
    _ProgressTasks[tid] = (_ProgressContext, task_id)
    return tid

def _progress_tick(tid: int):
    ctx, task_id = _ProgressTasks.get(tid, (None, None))
    if ctx and task_id is not None:
        ctx.update(task_id, advance=1)

def _progress_stop(tid: int) -> bool:
    global _ProgressContext
    ctx, task_id = _ProgressTasks.get(tid, (None, None))
    if ctx and task_id is not None:
        ctx.update(task_id, completed=ctx.tasks[task_id].total)
        ctx.stop()
        del _ProgressTasks[tid]
        if not _ProgressTasks:
            _ProgressContext = None
        return True
    return False

# ── Event system (timers, intervals, key_wait) ────────────────────

_ActiveTimers: dict = {}
_TimerLock = _threading.Lock()
_TimerDone = _threading.Event()
_TimerCounter = 0
_current_functions: dict = {}

def _wait(ms: float):
    time.sleep(float(ms) / 1000.0)

def _set_timeout(fn_name: str, delay_ms: float) -> int:
    global _TimerCounter
    fn = str(fn_name)
    delay = float(delay_ms) / 1000.0
    def _job(tid: int):
        from .executor import call_function
        try:
            call_function(fn, [], _current_functions, 0)
        except Exception:
            pass
        with _TimerLock:
            _ActiveTimers.pop(tid, None)
            if not _ActiveTimers:
                _TimerDone.set()
    with _TimerLock:
        _TimerCounter += 1
        tid = _TimerCounter
        t = _threading.Timer(delay, _job, args=[tid])
        _ActiveTimers[tid] = t
        _TimerDone.clear()
        t.start()
        return tid

def _set_interval(fn_name: str, interval_ms: float) -> int:
    global _TimerCounter
    fn = str(fn_name)
    interval = float(interval_ms) / 1000.0
    def _recurring(tid: int):
        from .executor import call_function
        with _TimerLock:
            if tid not in _ActiveTimers:
                return
        try:
            call_function(fn, [], _current_functions, 0)
        except Exception:
            pass
        with _TimerLock:
            if tid in _ActiveTimers:
                t = _threading.Timer(interval, _recurring, args=[tid])
                _ActiveTimers[tid] = t
                t.start()
    with _TimerLock:
        _TimerCounter += 1
        tid = _TimerCounter
        t = _threading.Timer(interval, _recurring, args=[tid])
        _ActiveTimers[tid] = t
        _TimerDone.clear()
        t.start()
        return tid

def _clear_timer(tid: int) -> bool:
    with _TimerLock:
        t = _ActiveTimers.pop(int(tid), None)
        if t:
            t.cancel()
            if not _ActiveTimers:
                _TimerDone.set()
            return True
        return False

def _wait_all():
    _TimerDone.wait()

def _key_wait(prompt: str = "") -> str:
    prompt = str(prompt)
    if prompt:
        from .console import con
        con().print(f"  [cyan]{prompt}[/cyan]", end="")
    import sys as _sys
    if _sys.platform == 'win32':
        import msvcrt
        ch = msvcrt.getch()
        return ch.decode('utf-8', errors='replace')
    else:
        import tty as _tty
        import termios as _termios
        fd = _sys.stdin.fileno()
        old = _termios.tcgetattr(fd)
        try:
            _tty.setraw(fd)
            return _sys.stdin.read(1)
        finally:
            _termios.tcsetattr(fd, _termios.TCSADRAIN, old)

# ── Live display (Rich Live) ──────────────────────────────────────

_LiveDisplay = None

def _live_start(title: str = ""):
    global _LiveDisplay
    if _LiveDisplay is not None:
        return
    from rich.live import Live
    from rich.panel import Panel
    _LiveDisplay = Live(
        Panel("", title=str(title) if title else None),
        refresh_per_second=4,
    )
    _LiveDisplay.start()

def _live_set(content: str):
    global _LiveDisplay
    if _LiveDisplay is None:
        return
    from rich.panel import Panel
    _LiveDisplay.update(Panel(str(content)))

def _live_stop():
    global _LiveDisplay
    if _LiveDisplay is None:
        return
    _LiveDisplay.stop()
    _LiveDisplay = None

BUILTINS: dict[str, Any] = {
    'time':   lambda: time.time(),
    '_sleep': lambda s: time.sleep(float(s)),
    'file_read':  _safe_file_read,
    'file_write': _safe_file_write,
    'range':  lambda *args: list(range(*[int(a) for a in args])),
    'zeros':  lambda n: [0] * int(n),
    'ones':   lambda n: [1] * int(n),
    'arange': lambda n: list(range(int(n))),
    'sum':    lambda l: sum(l) if isinstance(l, list) else l,
    'mean':   lambda l: sum(l) / len(l) if isinstance(l, list) and l else 0,
    'min':    lambda l: min(l) if isinstance(l, list) and l else l,
    'max':    lambda l: max(l) if isinstance(l, list) and l else l,
    'matmul': _matmul,
    'sqrt':   lambda x: _real_math.sqrt(float(x)),
    'sin':    lambda x: _real_math.sin(float(x)),
    'cos':    lambda x: _real_math.cos(float(x)),
    'tan':    lambda x: _real_math.tan(float(x)),
    'floor':  lambda x: _real_math.floor(float(x)),
    'ceil':   lambda x: _real_math.ceil(float(x)),
    'round':  lambda x: _real_builtins.round(x),
    'rand':   lambda: _real_random.random(),
    'randint': lambda a, b: _real_random.randint(int(a), int(b)),
    'abs':    lambda x: abs(x),
    'menu':           _interactive_menu,
    'confirm':        _interactive_confirm,
    'password':       _interactive_password,
    'say_table':      _display_table,
    'say_panel':      _display_panel,
    'say_tree':       _display_tree,
    'progress_start': _progress_start,
    'progress_tick':  _progress_tick,
    'progress_stop':  _progress_stop,
    'wait':         _wait,
    'set_timeout':  _set_timeout,
    'set_interval': _set_interval,
    'clear_timer':  _clear_timer,
    'wait_all':     _wait_all,
    'key_wait':     _key_wait,
    'live_start':   _live_start,
    'live_set':     _live_set,
    'live_stop':    _live_stop,
    'matrix':       _matrix,
    'zeros_matrix': _zeros_matrix,
    'identity':     _identity,
    'thread_join':  _thread_join,
    'json_loads':  _json_loads,
    'json_dumps':  _json_dumps,
    'json_read':   _json_read,
    'csv_parse':   _csv_parse,
    'csv_read':    _csv_read,
    'csv_write':   _csv_write,
    'cv_imread':  _img.imread,
    'cv_imwrite': _img.imwrite,
    'cv_blur':    _img.blur,
    'cv_gray':    _img.grayscale,
    'cv_resize':  _img.resize,
    'cv_rotate':  _img.rotate,
    'cv_threshold': _img.threshold,
    'cv_canny':   _img.canny,
    'plot_bar':      _charts.plot_bar,
    'plot_line':     _charts.plot_line,
    'plot_scatter':  _charts.plot_scatter,
    'plot_hist':     _charts.plot_hist,
    'plot_cartesian': _charts.plot_cartesian,
    'plot_3d':       _charts.plot_3d_scatter,
    'plot_save':     _charts.plot_save,
}

def val_to_str(val: Any) -> str:
    if isinstance(val, bool):  return "true" if val else "false"
    if isinstance(val, float) and val == int(val): return str(int(val))
    if isinstance(val, StructInstance):
        return repr(val)
    if isinstance(val, Matrix):
        return repr(val)
    if isinstance(val, list):
        return "[" + ", ".join(val_to_str(x) for x in val) + "]"
    return str(val)

# === AST COMPILATION CACHE ===
_EXPR_CACHE = {}

def _compile_expr(expr: str):
    # parentheses
    if expr.startswith('(') and expr.endswith(')'):
        depth = 0; balanced = True
        for i in range(len(expr) - 1):
            ch = expr[i]
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
            if i > 0 and depth == 0: balanced = False; break
        if balanced:
            inner = _compile_expr(expr[1:-1].strip())
            return lambda v, l, f: inner(v, l, f)

    # not
    if expr.startswith('not '):
        inner = _compile_expr(expr[4:].strip())
        return lambda v, l, f, i=inner: not i(v, l, f)

    # and / or
    for kw in (' and ', ' or '):
        parts = _split_outside_quotes(expr, kw)
        if parts:
            lhs = _compile_expr(parts[0])
            rhs = _compile_expr(parts[1])
            if kw == ' and ':
                return lambda v, l, f, left=lhs, right=rhs: bool(left(v, l, f)) and bool(right(v, l, f))
            else:
                return lambda v, l, f, left=lhs, right=rhs: bool(left(v, l, f)) or bool(right(v, l, f))

    # comparison + arithmetic
    for ops in _PREC:
        for op in ops:
            parts = _split_outside_quotes(expr, op, from_right=(op not in _PREC[0]))
            if parts:
                lhs = _compile_expr(parts[0])
                rhs = _compile_expr(parts[1])
                op_func = _OPS[op]
                
                def _eval_op(v, l, f, left=lhs, right=rhs, o=op, ofunc=op_func):
                    L = left(v, l, f)
                    R = right(v, l, f)
                    try:
                        if o == '/' and R == 0:
                            error("Division by zero.", l); return 0
                        return ofunc(L, R)
                    except (TypeError, ValueError) as e:
                        if o == '+':  return val_to_str(L) + val_to_str(R)
                        if o == '==': return str(L) == str(R)
                        if o in ('>', '<', '>=', '<=', '!='): return False
                        error(f"Error applying '{o}': {e}", l)
                        return 0
                return _eval_op

    # indexing (including slice)
    # Guard: skip if target is just '[' (nested list literal, not indexing)
    m_idx = re.match(r'^(.+?)\[(.+?)\]$', expr)
    if m_idx and m_idx.group(1).strip() != '[':
        target = _compile_expr(m_idx.group(1).strip())
        idx_raw = m_idx.group(2).strip()
        if ':' in idx_raw:
            parts = [p.strip() for p in idx_raw.split(':')]
            parts = parts[:3]
            start = _compile_expr(parts[0]) if parts[0] else None
            stop  = _compile_expr(parts[1]) if len(parts) > 1 and parts[1] else None
            step  = _compile_expr(parts[2]) if len(parts) > 2 and parts[2] else None
            def _eval_slice(v, l, f, t=target, st=start, sp=stop, stp=step):
                try:
                    s = int(st(v, l, f)) if st else None
                    e = int(sp(v, l, f)) if sp else None
                    p = int(stp(v, l, f)) if stp else None
                    return t(v, l, f)[s:e:p]
                except Exception as exc:
                    error(f"Slice error: {exc}", l)
                    return 0
            return _eval_slice
        else:
            idx = _compile_expr(idx_raw)
            def _eval_idx(v, l, f, t=target, i=idx):
                try:
                    val = t(v, l, f)
                    key = i(v, l, f)
                    if isinstance(val, dict):
                        return val[key]
                    return val[int(key)]
                except Exception as e:
                    error(f"Indexing error: {e}", l)
                    return 0
            return _eval_idx

    # method call
    m = re.match(r'^(.+?)\.(append|pop|sort|len|upper|lower|trim|replace|contains|sum|mean|min|max)\((.*)\)$', expr)
    if m:
        target = _compile_expr(m.group(1).strip())
        method = m.group(2)
        raw_args = m.group(3).strip()

        if method in ('len', 'sum', 'mean', 'min', 'max', 'upper', 'lower', 'trim'):
            def _eval_no_arg_method(v, l, f, t=target, meth=method):
                T = t(v, l, f)
                if isinstance(T, list):
                    if meth == 'len':  return len(T)
                    if meth == 'sum':  return sum(T)
                    if meth == 'mean': return sum(T) / len(T) if T else 0
                    if meth == 'min':  return min(T) if T else 0
                    if meth == 'max':  return max(T) if T else 0
                    error(f"List has no method '{meth}'", l)
                    return 0
                S = str(T)
                if meth == 'len':      return len(S)
                if meth == 'upper':    return S.upper()
                if meth == 'lower':    return S.lower()
                if meth == 'trim':     return S.strip()
                return 0
            return _eval_no_arg_method

        if method == 'contains':
            arg_expr = _compile_expr(raw_args)
            return lambda v, l, f, t=target, a=arg_expr: str(a(v, l, f)) in str(t(v, l, f))

        if method == 'replace':
            p = _split_outside_quotes(raw_args, ',')
            if not p:
                def _eval_bad_replace(v, l, f, t=target):
                    error("replace() needs 2 args: replace(old, new)", l)
                    return str(t(v, l, f))
                return _eval_bad_replace
            a_expr = _compile_expr(p[0].strip())
            b_expr = _compile_expr(p[1].strip())
            def _eval_replace(v, l, f, t=target, a=a_expr, b=b_expr):
                return str(t(v, l, f)).replace(str(a(v, l, f)), str(b(v, l, f)))
            return _eval_replace

        if method == 'append':
            arg_expr = _compile_expr(raw_args)
            def _eval_append(v, l, f, t=target, a=arg_expr):
                lst = t(v, l, f)
                if not isinstance(lst, list):
                    error("append() requires a list", l)
                    return 0
                lst.append(a(v, l, f))
                return lst
            return _eval_append

        if method == 'pop':
            def _eval_pop(v, l, f, t=target):
                lst = t(v, l, f)
                if not isinstance(lst, list):
                    error("pop() requires a list", l)
                    return 0
                if not lst:
                    error("pop() from empty list", l)
                    return 0
                return lst.pop()
            return _eval_pop

        if method == 'sort':
            def _eval_sort(v, l, f, t=target):
                lst = t(v, l, f)
                if not isinstance(lst, list):
                    error("sort() requires a list", l)
                    return 0
                try:
                    lst.sort()
                except Exception as e:
                    error(f"sort() error: {e}", l)
                return lst
            return _eval_sort

    # function call (also handles struct construction)
    m2 = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', expr)
    if m2:
        fname = m2.group(1)
        rargs = m2.group(2).strip()
        arg_exprs = [_compile_expr(a.strip()) for a in split_args(rargs)] if rargs else []
        
        def _eval_func(v, l, f, fn=fname, aes=arg_exprs):
            global _current_functions
            _current_functions = f
            vals = [ae(v, l, f) for ae in aes]
            if fn in BUILTINS:
                try:
                    return BUILTINS[fn](*vals)
                except Exception as e:
                    error(f"Error in built-in '{fn}': {e}", l)
                    return 0
            if fn in f:
                func = f[fn]
                if '_struct_fields' in func:
                    fields = func['_struct_fields']
                    result = {}
                    for idx, (fname, fdefault) in enumerate(fields):
                        if idx < len(vals):
                            result[fname] = vals[idx]
                        elif fdefault:
                            result[fname] = evaluate(fdefault, v, l, f)
                        else:
                            result[fname] = ""
                    return StructInstance(result)
                if '_enum_values' in func:
                    error(f"'enum' type '{fn}' cannot be called as a function", l)
                    return ""
                if func.get('_async'):
                    return Coro(fn, vals, func['body'], func['params'], f, l)
                from .executor import call_function
                return call_function(fn, vals, f, l)
            error(f"Undefined function: '{fn}'", l)
            return ""
        return _eval_func

    # await expression
    if expr.startswith('await '):
        inner = _compile_expr(expr[6:].strip())
        def _eval_await(v, l, f, i=inner):
            val = i(v, l, f)
            if isinstance(val, Coro):
                val.start()
                return val.join()
            return val
        return _eval_await

    # dot access (field / property)
    m_dot = re.match(r'^(.+)\.([a-zA-Z_]\w*)$', expr)
    if m_dot:
        target = _compile_expr(m_dot.group(1).strip())
        field = m_dot.group(2)
        def _eval_dot(v, l, f, t=target, attr=field):
            T = t(v, l, f)
            try:
                return getattr(T, attr)
            except AttributeError:
                error(f"'{type(T).__name__}' has no attribute '{attr}'", l)
                return 0
        return _eval_dot

    # list literal (after operators so [1,2]+[3,4] hits + first)
    if expr.startswith('[') and expr.endswith(']'):
        content = expr[1:-1].strip()
        if not content: return lambda v, l, f: []
        args_exprs = split_args(content)
        compiled_args = [_compile_expr(a.strip()) for a in args_exprs]
        return lambda v, l, f, ca=compiled_args: [c(v, l, f) for c in ca]

    # dict literal  {key: val, ...}
    if expr.startswith('{') and expr.endswith('}'):
        content = expr[1:-1].strip()
        if not content: return lambda v, l, f: {}
        args_exprs = split_args(content)
        keys, vals = [], []
        for pair in args_exprs:
            kv = _split_outside_quotes(pair, ':')
            if not kv:
                error(f"Dict entry requires 'key: value', got: '{pair}'", 0)
                return lambda v, l, f: {}
            keys.append(_compile_expr(kv[0].strip()))
            vals.append(_compile_expr(kv[1].strip()))
        def _eval_dict(v, l, f, ks=keys, vs=vals):
            return {k(v, l, f): val(v, l, f) for k, val in zip(ks, vs)}
        return _eval_dict

    # single token
    tok = expr
    if (tok.startswith('"') and tok.endswith('"')) or \
       (tok.startswith("'") and tok.endswith("'")):
        s_val = tok[1:-1]
        return lambda v, l, f, s=s_val: s
    if tok == 'true':  return lambda v, l, f: True
    if tok == 'false': return lambda v, l, f: False
    
    # unary -
    if tok.startswith('-') and len(tok) > 1 and not tok[1].isdigit():
        inner = _compile_expr(tok[1:].strip())
        return lambda v, l, f, i=inner: -i(v, l, f)
    
    c_val = cast(tok)
    def _eval_tok(v, l, f, t=tok, cv=c_val):
        if t in v: return v[t]
        return cv
    return _eval_tok

def clear_cache():
    _EXPR_CACHE.clear()

def evaluate(expr: str, variables: dict, line_no: int, functions: dict) -> Any:
    expr = expr.strip()
    if not expr: return ""
    # print(f"DEBUG: evaluating '{expr}', BUILTINS: {list(BUILTINS.keys())}")
    if expr not in _EXPR_CACHE:
        _EXPR_CACHE[expr] = _compile_expr(expr)
        
    return _EXPR_CACHE[expr](variables, line_no, functions)
