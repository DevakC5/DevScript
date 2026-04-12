# devlang/evaluator.py — expression evaluator

from __future__ import annotations
import operator
import re
from typing import Any

from .lexer import cast
from .console import error

_RAW_OPS: dict[str, Any] = {
    '+':  operator.add,  '-':  operator.sub,
    '*':  operator.mul,  '/':  operator.truediv,
    '%':  operator.mod,  '**': operator.pow,
    '>':  operator.gt,   '<':  operator.lt,
    '>=': operator.ge,   '<=': operator.le,
    '==': operator.eq,   '!=': operator.ne,
}

def _vectorized_op(op_func, a, b):
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ValueError(f"Shape mismatch: {len(a)} vs {len(b)}")
        return [_vectorized_op(op_func, x, y) for x, y in zip(a, b)]
    if isinstance(a, list):
        return [_vectorized_op(op_func, x, b) for x in a]
    if isinstance(b, list):
        return [_vectorized_op(op_func, a, y) for y in b]
    return op_func(a, b)

_OPS: dict[str, Any] = {
    k: (lambda a, b, op=v: _vectorized_op(op, a, b)) for k, v in _RAW_OPS.items()
}

_PREC = [
    ['>=', '<=', '==', '!=', '>', '<'],
    ['+', '-'],
    ['**', '*', '/', '%'],
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
                idxs.append(i)
        i += 1
    if not idxs: return None
    idx   = idxs[-1] if from_right else idxs[0]
    left  = expr[:idx].strip()
    right = expr[idx + len(op):].strip()
    return [left, right] if left and right else None


def split_args(s: str) -> list[str]:
    """Split comma-separated function args or list elements, respecting quotes, parens, and brackets."""
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


def _mock_cv_imread(path):
    return {"type": "image", "path": path, "status": "loaded"}

def _mock_cv_imwrite(path, img):
    return f"Saved image to {path}"

def _mock_cv_blur(img, k):
    if isinstance(img, dict):
        return {"type": "image", "path": img.get("path"), "status": f"blurred({k})"}
    return img

def _mock_cv_gray(img):
    if isinstance(img, dict):
        return {"type": "image", "path": img.get("path"), "status": "grayscale"}
    return img

def _mock_plot_bar(labels, values):
    print("\n[Bar Chart]")
    if isinstance(labels, list) and isinstance(values, list):
        for lbl, val in zip(labels, values):
            print(f"{str(lbl):10} | {'█' * int(val)} {val}")
    return "Plot rendered"

def _mock_plot_line(labels, values):
    print("\n[Line Chart]")
    if isinstance(labels, list) and isinstance(values, list):
        for lbl, val in zip(labels, values):
            print(f"{str(lbl):10} | {'-' * int(val)}* {val}")
    return "Plot rendered"

BUILTINS: dict[str, Any] = {
    'zeros':  lambda n: [0] * int(n),
    'ones':   lambda n: [1] * int(n),
    'arange': lambda n: list(range(int(n))),
    'sum':    lambda l: sum(l) if isinstance(l, list) else l,
    'mean':   lambda l: sum(l) / len(l) if isinstance(l, list) and l else 0,
    'min':    lambda l: min(l) if isinstance(l, list) and l else l,
    'max':    lambda l: max(l) if isinstance(l, list) and l else l,
    'cv_imread': _mock_cv_imread,
    'cv_imwrite': _mock_cv_imwrite,
    'cv_blur': _mock_cv_blur,
    'cv_gray': _mock_cv_gray,
    'plot_bar': _mock_plot_bar,
    'plot_line': _mock_plot_line,
}


def evaluate(expr: str, variables: dict, line_no: int, functions: dict) -> Any:
    expr = expr.strip()
    if not expr: return ""

    # parentheses: (expr)
    if expr.startswith('(') and expr.endswith(')'):
        # Check if these parentheses are matching each other
        depth = 0
        balanced = True
        for i in range(len(expr) - 1):
            ch = expr[i]
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
            if i > 0 and depth == 0:
                balanced = False
                break
        if balanced:
            return evaluate(expr[1:-1].strip(), variables, line_no, functions)

    # list literal: [1, 2, 3]
    if expr.startswith('[') and expr.endswith(']'):
        content = expr[1:-1].strip()
        if not content: return []
        return [evaluate(a.strip(), variables, line_no, functions) for a in split_args(content)]

    # not
    if expr.startswith('not '):
        return not evaluate(expr[4:].strip(), variables, line_no, functions)

    # and / or
    for kw in (' and ', ' or '):
        parts = _split_outside_quotes(expr, kw)
        if parts:
            lhs = bool(evaluate(parts[0], variables, line_no, functions))
            rhs = bool(evaluate(parts[1], variables, line_no, functions))
            return (lhs and rhs) if kw == ' and ' else (lhs or rhs)

    # comparison + arithmetic
    for ops in _PREC:
        for op in ops:
            parts = _split_outside_quotes(expr, op, from_right=(op not in _PREC[0]))
            if parts:
                lhs = evaluate(parts[0], variables, line_no, functions)
                rhs = evaluate(parts[1], variables, line_no, functions)
                try:
                    if op == '/' and rhs == 0:
                        error("Division by zero.", line_no); return 0
                    return _OPS[op](lhs, rhs)
                except (TypeError, ValueError) as e:
                    if op == '+':  return val_to_str(lhs) + val_to_str(rhs)
                    if op == '==': return str(lhs) == str(rhs)
                    if op in ('>', '<', '>=', '<=', '!='): return False
                    error(f"Error applying '{op}': {e}", line_no)
                    return 0

    # indexing: a[0]
    m_idx = re.match(r'^(.+?)\[(.+?)\]$', expr)
    if m_idx:
        target = evaluate(m_idx.group(1).strip(), variables, line_no, functions)
        idx = evaluate(m_idx.group(2).strip(), variables, line_no, functions)
        try:
            return target[int(idx)]
        except Exception as e:
            error(f"Indexing error: {e}", line_no)
            return 0

    # method call:  expr.method(args)
    m = re.match(r'^(.+?)\.(len|upper|lower|trim|replace|contains|sum|mean|min|max)\((.*)\)$', expr)
    if m:
        target = evaluate(m.group(1).strip(), variables, line_no, functions)
        method = m.group(2)
        raw    = m.group(3).strip()
        
        if isinstance(target, list):
            if method == 'len':  return len(target)
            if method == 'sum':  return sum(target)
            if method == 'mean': return sum(target) / len(target) if target else 0
            if method == 'min':  return min(target) if target else 0
            if method == 'max':  return max(target) if target else 0
            error(f"List has no method '{method}'", line_no)
            return 0
        
        s = str(target)
        if method == 'len':      return len(s)
        if method == 'upper':    return s.upper()
        if method == 'lower':    return s.lower()
        if method == 'trim':     return s.strip()
        if method == 'contains':
            return str(evaluate(raw, variables, line_no, functions)) in s
        if method == 'replace':
            p = _split_outside_quotes(raw, ',')
            if not p: error("replace() needs 2 args: replace(old, new)", line_no); return s
            a = str(evaluate(p[0].strip(), variables, line_no, functions))
            b = str(evaluate(p[1].strip(), variables, line_no, functions))
            return s.replace(a, b)

    # function call:  name(args)
    m2 = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', expr)
    if m2:
        fname = m2.group(1)
        rargs = m2.group(2).strip()
        vals  = [evaluate(a.strip(), variables, line_no, functions)
                 for a in split_args(rargs)] if rargs else []
        
        if fname in BUILTINS:
            try:
                return BUILTINS[fname](*vals)
            except Exception as e:
                error(f"Error in built-in '{fname}': {e}", line_no)
                return 0

        if fname in functions:
            from .executor import call_function
            return call_function(fname, vals, functions, line_no)
        error(f"Undefined function: '{fname}'", line_no)
        return ""

    # single token
    tok = expr
    if (tok.startswith('"') and tok.endswith('"')) or \
       (tok.startswith("'") and tok.endswith("'")):
        return tok[1:-1]
    if tok == 'true':  return True
    if tok == 'false': return False
    if tok in variables: return variables[tok]
    return cast(tok)


def val_to_str(val: Any) -> str:
    if isinstance(val, bool):  return "true" if val else "false"
    if isinstance(val, float) and val == int(val): return str(int(val))
    if isinstance(val, list):
        return "[" + ", ".join(val_to_str(x) for x in val) + "]"
    return str(val)