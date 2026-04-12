# dev_interpreter.py  — DevLang v3.0
# New in v3: else, while, functions/def/return, inline comments,
#            and/or/not conditions, string methods (len/upper/lower/trim/replace/contains)

from __future__ import annotations
import sys
import os
import operator
import re
import pickle
import hashlib
import time
from typing import Any

# ── Lazy rich ──────────────────────────────────────────────────────────────
_con = None
def con():
    global _con
    if _con is None:
        from rich.console import Console
        _con = Console()
    return _con

def _panel(content, **kw):
    from rich.panel import Panel
    from rich import box as rbox
    return Panel(content, box=rbox.ROUNDED, **kw)

# ── Pre-compiled regexes ───────────────────────────────────────────────────
RE_TOKEN   = re.compile(r'"[^"]*"|\'[^\']*\'|\S+')
RE_VARNAME = re.compile(r'^[a-zA-Z_]\w*$')
RE_INT     = re.compile(r'^-?\d+$')
RE_FLOAT   = re.compile(r'^-?\d+\.\d+$')

# ── Sentinel for return values ─────────────────────────────────────────────
class _ReturnSignal(Exception):
    def __init__(self, value): self.value = value

# ────────────────────────────────────────────────────────────────────────────
#  AST Nodes
# ────────────────────────────────────────────────────────────────────────────
class SayNode:
    __slots__ = ('expr','line')
    def __init__(self, e, l): self.expr=e; self.line=l

class LetNode:
    __slots__ = ('name','expr','line')
    def __init__(self, n, e, l): self.name=n; self.expr=e; self.line=l

class InputNode:
    __slots__ = ('name','prompt','line')
    def __init__(self, n, p, l): self.name=n; self.prompt=p; self.line=l

class IfNode:
    __slots__ = ('cond','body','else_body','line')
    def __init__(self, c, b, eb, l): self.cond=c; self.body=b; self.else_body=eb; self.line=l

class RepeatNode:
    __slots__ = ('count_expr','body','line')
    def __init__(self, c, b, l): self.count_expr=c; self.body=b; self.line=l

class WhileNode:
    __slots__ = ('cond','body','line')
    def __init__(self, c, b, l): self.cond=c; self.body=b; self.line=l

class FuncDefNode:
    __slots__ = ('name','params','body','line')
    def __init__(self, n, p, b, l): self.name=n; self.params=p; self.body=b; self.line=l

class ReturnNode:
    __slots__ = ('expr','line')
    def __init__(self, e, l): self.expr=e; self.line=l

class CallNode:
    __slots__ = ('name','args','line')
    def __init__(self, n, a, l): self.name=n; self.args=a; self.line=l

# ────────────────────────────────────────────────────────────────────────────
#  Error / Warn
# ────────────────────────────────────────────────────────────────────────────
def error(msg, line_no=None):
    loc = f"[bold red]Line {line_no}:[/bold red] " if line_no else ""
    con().print(_panel(f"{loc}[red]{msg}[/red]",
                       title="[bold red]⚠  DevLang Error[/bold red]",
                       border_style="red", expand=False))

def warn(msg, line_no=None):
    loc = f"[yellow]Line {line_no}:[/yellow] " if line_no else ""
    con().print(f"  [bold yellow]⚡ Warning:[/bold yellow] {loc}{msg}")

# ────────────────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────────────────
def tokenise(line: str) -> list[str]:
    return RE_TOKEN.findall(line)

def strip_inline_comment(line: str) -> str:
    """Remove inline # comments that are outside quotes."""
    in_q, q_char = False, ''
    for i, ch in enumerate(line):
        if in_q:
            if ch == q_char: in_q = False
        else:
            if ch in ('"', "'"): in_q, q_char = True, ch
            elif ch == '#': return line[:i]
    return line

def _cast(val: str) -> Any:
    if RE_INT.match(val):   return int(val)
    if RE_FLOAT.match(val): return float(val)
    return val

# ────────────────────────────────────────────────────────────────────────────
#  Expression evaluator
# ────────────────────────────────────────────────────────────────────────────
_OPS = {
    '+': operator.add, '-': operator.sub,
    '*': operator.mul, '/': operator.truediv,
    '%': operator.mod, '**': operator.pow,
    '>': operator.gt,  '<': operator.lt,
    '>=': operator.ge, '<=': operator.le,
    '==': operator.eq, '!=': operator.ne,
}
_PREC = [
    ['>=','<=','==','!=','>','<'],
    ['+','-'],
    ['**','*','/','%'],
]

def _split_outside_quotes(expr: str, op: str, from_right: bool = False):
    in_q, q_char, idxs = False, '', []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if in_q:
            if ch == q_char: in_q = False
        else:
            if ch in ('"', "'"): in_q, q_char = True, ch
            elif expr[i:i+len(op)] == op: idxs.append(i)
        i += 1
    if not idxs: return None
    idx   = idxs[-1] if from_right else idxs[0]
    left  = expr[:idx].strip()
    right = expr[idx+len(op):].strip()
    return [left, right] if left and right else None


def evaluate(expr: str, variables: dict, line_no: int, functions: dict = None) -> Any:
    if functions is None: functions = {}
    expr = expr.strip()
    if not expr: return ""

    # ── not <expr>
    if expr.startswith('not '):
        return not evaluate(expr[4:].strip(), variables, line_no, functions)

    # ── <lhs> and <rhs>
    parts = _split_outside_quotes(expr, ' and ', from_right=False)
    if parts:
        return bool(evaluate(parts[0], variables, line_no, functions)) and \
               bool(evaluate(parts[1], variables, line_no, functions))

    # ── <lhs> or <rhs>
    parts = _split_outside_quotes(expr, ' or ', from_right=False)
    if parts:
        return bool(evaluate(parts[0], variables, line_no, functions)) or \
               bool(evaluate(parts[1], variables, line_no, functions))

    # ── comparison & arithmetic
    for ops in _PREC:
        for op in ops:
            parts = _split_outside_quotes(expr, op, from_right=(op not in _PREC[0]))
            if parts:
                lhs = evaluate(parts[0], variables, line_no, functions)
                rhs = evaluate(parts[1], variables, line_no, functions)
                fn  = _OPS[op]
                try:
                    if op == '/' and rhs == 0:
                        error("Division by zero.", line_no); return 0
                    return fn(lhs, rhs)
                except TypeError:
                    if op == '+':  return str(lhs) + str(rhs)
                    if op == '==': return str(lhs) == str(rhs)
                    if op in ('>','<','>=','<=','!='): return False
                    error(f"Cannot apply '{op}' to {lhs!r} and {rhs!r}", line_no)
                    return 0

    # ── string method:  expr.method(args)
    m = re.match(r'^(.+?)\.(len|upper|lower|trim|replace|contains)\((.*)\)$', expr)
    if m:
        target = evaluate(m.group(1).strip(), variables, line_no, functions)
        method = m.group(2)
        raw_args = m.group(3).strip()
        s = str(target)
        if method == 'len':     return len(s)
        if method == 'upper':   return s.upper()
        if method == 'lower':   return s.lower()
        if method == 'trim':    return s.strip()
        if method == 'contains':
            arg = evaluate(raw_args, variables, line_no, functions)
            return str(arg) in s
        if method == 'replace':
            arg_parts = _split_outside_quotes(raw_args, ',')
            if not arg_parts:
                error(f"replace() needs 2 args: replace(old, new)", line_no); return s
            a = str(evaluate(arg_parts[0].strip(), variables, line_no, functions))
            b = str(evaluate(arg_parts[1].strip(), variables, line_no, functions))
            return s.replace(a, b)

    # ── function call:  name(arg1, arg2, ...)
    m2 = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', expr)
    if m2:
        fname    = m2.group(1)
        raw_args = m2.group(2).strip()
        arg_vals = []
        if raw_args:
            for a in _split_args(raw_args):
                arg_vals.append(evaluate(a.strip(), variables, line_no, functions))
        if fname in functions:
            return _call_function(fname, arg_vals, functions, line_no)
        error(f"Undefined function: '{fname}'", line_no)
        return ""

    # ── single token
    tok = expr
    if (tok.startswith('"') and tok.endswith('"')) or \
       (tok.startswith("'") and tok.endswith("'")):
        return tok[1:-1]
    if tok == 'true':  return True
    if tok == 'false': return False
    if tok in variables: return variables[tok]
    return _cast(tok)


def _split_args(s: str) -> list[str]:
    """Split comma-separated args respecting quotes and parens."""
    args, depth, cur, in_q, q_char = [], 0, [], False, ''
    for ch in s:
        if in_q:
            cur.append(ch)
            if ch == q_char: in_q = False
        elif ch in ('"', "'"):
            in_q, q_char = True, ch; cur.append(ch)
        elif ch == '(': depth += 1; cur.append(ch)
        elif ch == ')': depth -= 1; cur.append(ch)
        elif ch == ',' and depth == 0:
            args.append(''.join(cur)); cur = []
        else:
            cur.append(ch)
    if cur: args.append(''.join(cur))
    return args


def _call_function(name: str, arg_vals: list, functions: dict, line_no: int) -> Any:
    func = functions[name]
    if len(arg_vals) != len(func['params']):
        error(f"Function '{name}' expects {len(func['params'])} arg(s), got {len(arg_vals)}.", line_no)
        return ""
    local_vars = dict(zip(func['params'], arg_vals))
    try:
        run_block(func['body'], local_vars, functions)
    except _ReturnSignal as r:
        return r.value
    return ""


def val_to_str(val: Any) -> str:
    if isinstance(val, bool): return "true" if val else "false"
    if isinstance(val, float) and val == int(val): return str(int(val))
    return str(val)

# ────────────────────────────────────────────────────────────────────────────
#  Parser
# ────────────────────────────────────────────────────────────────────────────
def parse(lines: list[str], line_nos: list[int]) -> list:
    ast, i = [], 0
    while i < len(lines):
        raw = strip_inline_comment(lines[i])
        ln  = raw.strip()
        lno = line_nos[i]

        if not ln:
            i += 1; continue

        tokens = tokenise(ln)
        cmd    = tokens[0]

        # ── say
        if cmd == 'say':
            ast.append(SayNode(ln[3:].strip(), lno))
            i += 1

        # ── let
        elif cmd == 'let':
            rest = ln[3:].strip()
            if '=' not in rest:
                error(f"'let' expects: let <name> = <value>  →  got: {ln}", lno)
                i += 1; continue
            name, _, expr = rest.partition('=')
            name = name.strip()
            if not RE_VARNAME.match(name):
                error(f"Invalid variable name: '{name}'", lno); i += 1; continue
            ast.append(LetNode(name, expr.strip(), lno))
            i += 1

        # ── input
        elif cmd == 'input':
            rest = ln[5:].strip()
            if '->' not in rest:
                error(f"'input' expects: input <name> -> \"prompt\"  →  got: {ln}", lno)
                i += 1; continue
            var_name, _, prompt_part = rest.partition('->')
            var_name = var_name.strip()
            if not RE_VARNAME.match(var_name):
                error(f"Invalid variable name: '{var_name}'", lno); i += 1; continue
            prompt = prompt_part.strip().strip('"').strip("'")
            ast.append(InputNode(var_name, prompt, lno))
            i += 1

        # ── if  (with optional else)
        elif cmd == 'if':
            if '->' not in ln:
                error(f"'if' block missing '->': {ln}", lno); i += 1; continue
            cond_part, _, inline = ln.partition('->')
            cond_expr = cond_part[2:].strip()
            inline    = inline.strip()
            if inline:
                body_src = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos = [lno]
                else_src, else_nos = [], []
                i += 1
            else:
                body_src, body_nos, else_src, else_nos, i = _extract_if_block(lines, line_nos, i + 1)
            ast.append(IfNode(cond_expr, parse(body_src, body_nos), parse(else_src, else_nos), lno))

        # ── else  (stray — handled inside _extract_if_block)
        elif cmd == 'else':
            warn(f"Unexpected 'else' without matching 'if'.", lno); i += 1

        # ── repeat
        elif cmd == 'repeat':
            if '->' not in ln:
                error(f"'repeat' block missing '->': {ln}", lno); i += 1; continue
            count_part, _, inline = ln.partition('->')
            count_expr = count_part[6:].strip()
            inline     = inline.strip()
            if inline:
                body_src = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos = [lno]; i += 1
            else:
                body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(RepeatNode(count_expr, parse(body_src, body_nos), lno))

        # ── while
        elif cmd == 'while':
            if '->' not in ln:
                error(f"'while' block missing '->': {ln}", lno); i += 1; continue
            cond_part, _, inline = ln.partition('->')
            cond_expr = cond_part[5:].strip()
            inline    = inline.strip()
            if inline:
                body_src = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos = [lno]; i += 1
            else:
                body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(WhileNode(cond_expr, parse(body_src, body_nos), lno))

        # ── def
        elif cmd == 'def':
            # def greet(name) ->
            m = re.match(r'^def\s+([a-zA-Z_]\w*)\s*\((.*?)\)\s*->', ln)
            if not m:
                error(f"'def' syntax: def name(params) ->  …  end   got: {ln}", lno)
                i += 1; continue
            fname  = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(FuncDefNode(fname, params, parse(body_src, body_nos), lno))

        # ── return
        elif cmd == 'return':
            expr = ln[6:].strip()
            ast.append(ReturnNode(expr, lno))
            i += 1

        # ── end (stray)
        elif cmd == 'end':
            warn(f"Unexpected 'end'.", lno); i += 1

        # ── bare function call:  greet("world")
        elif RE_VARNAME.match(cmd) and '(' in ln:
            m2 = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', ln)
            if m2:
                fname    = m2.group(1)
                raw_args = m2.group(2).strip()
                ast.append(CallNode(fname, raw_args, lno))
                i += 1
            else:
                error(f"Unknown command: '{cmd}'", lno); i += 1

        else:
            error(f"Unknown command: '{cmd}'", lno); i += 1

    return ast


def _extract_block(lines, line_nos, start):
    depth, block, b_nos = 1, [], []
    i = start
    while i < len(lines):
        ln = strip_inline_comment(lines[i]).strip()
        if re.match(r'^(if|repeat|while|def)\b', ln) and ('->' in ln):
            depth += 1
        if ln == 'end':
            depth -= 1
            if depth == 0: return block, b_nos, i + 1
        block.append(lines[i]); b_nos.append(line_nos[i]); i += 1
    error(f"Missing 'end' — block opened near line {line_nos[start-1] if start > 0 else '?'} was never closed.")
    return block, b_nos, i


def _extract_if_block(lines, line_nos, start):
    """Extract if-body and optional else-body, return (body, b_nos, else_body, e_nos, next_i)."""
    depth, body, b_nos, else_body, e_nos = 1, [], [], [], []
    in_else = False
    i = start
    while i < len(lines):
        ln = strip_inline_comment(lines[i]).strip()
        if re.match(r'^(if|repeat|while|def)\b', ln) and ('->' in ln):
            depth += 1
        if depth == 1 and ln == 'else':
            in_else = True; i += 1; continue
        if ln == 'end':
            depth -= 1
            if depth == 0: return body, b_nos, else_body, e_nos, i + 1
        if in_else:
            else_body.append(lines[i]); e_nos.append(line_nos[i])
        else:
            body.append(lines[i]); b_nos.append(line_nos[i])
        i += 1
    error(f"Missing 'end' for 'if' block near line {line_nos[start-1] if start > 0 else '?'}.")
    return body, b_nos, else_body, e_nos, i

# ────────────────────────────────────────────────────────────────────────────
#  Executor
# ────────────────────────────────────────────────────────────────────────────
def run_block(ast: list, variables: dict, functions: dict = None):
    if functions is None: functions = {}
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
            variables[node.name] = _cast(raw)

        elif isinstance(node, IfNode):
            if evaluate(node.cond, variables, node.line, functions):
                run_block(node.body, variables, functions)
            elif node.else_body:
                run_block(node.else_body, variables, functions)

        elif isinstance(node, RepeatNode):
            count_val = evaluate(node.count_expr, variables, node.line, functions)
            try:    count = int(count_val)
            except: error(f"'repeat' count must be a number, got: {count_val!r}", node.line); continue
            if count < 0: warn(f"'repeat' count is negative; skipping.", node.line); continue
            for _ in range(count):
                run_block(node.body, variables, functions)

        elif isinstance(node, WhileNode):
            limit = 100_000  # safety cap
            iters = 0
            while evaluate(node.cond, variables, node.line, functions):
                run_block(node.body, variables, functions)
                iters += 1
                if iters >= limit:
                    error(f"'while' loop exceeded {limit} iterations — possible infinite loop.", node.line)
                    break

        elif isinstance(node, FuncDefNode):
            functions[node.name] = {'params': node.params, 'body': node.body}

        elif isinstance(node, ReturnNode):
            val = evaluate(node.expr, variables, node.line, functions)
            raise _ReturnSignal(val)

        elif isinstance(node, CallNode):
            raw_args = node.args
            arg_vals = []
            if raw_args:
                for a in _split_args(raw_args):
                    arg_vals.append(evaluate(a.strip(), variables, node.line, functions))
            if node.name in functions:
                _call_function(node.name, arg_vals, functions, node.line)
            else:
                error(f"Undefined function: '{node.name}'", node.line)

# ────────────────────────────────────────────────────────────────────────────
#  Bytecode cache
# ────────────────────────────────────────────────────────────────────────────
def _source_hash(src): return hashlib.md5(src.encode()).hexdigest()
def _cache_path(fp):   return fp + 'c'

def load_ast_cached(filepath: str) -> list:
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    h     = _source_hash(source)
    cache = _cache_path(filepath)
    if os.path.exists(cache):
        try:
            with open(cache, 'rb') as f:
                stored_hash, ast = pickle.load(f)
            if stored_hash == h: return ast
        except Exception: pass
    lines    = source.splitlines()
    line_nos = list(range(1, len(lines) + 1))
    ast      = parse(lines, line_nos)
    try:
        with open(cache, 'wb') as f:
            pickle.dump((h, ast), f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception: pass
    return ast

# ────────────────────────────────────────────────────────────────────────────
#  CLI
# ────────────────────────────────────────────────────────────────────────────
def show_banner():
    from rich.text import Text
    txt = Text()
    txt.append("  DevLang Interpreter ", style="bold cyan")
    txt.append("v3.0", style="bold yellow")
    txt.append("  ⚡ full-featured", style="dim green")
    txt.append("\n  Clean · Readable · Beginner-Friendly", style="dim white")
    con().print(_panel(txt, border_style="cyan", expand=False))
    con().print()

def show_usage():
    con().print(_panel(
        "[bold cyan]Commands:[/bold cyan]\n"
        "  [yellow]dev run [white]<file.dev>[/white][/yellow]   Run a DevLang program\n"
        "  [yellow]dev version[/yellow]          Show interpreter version\n"
        "  [yellow]dev help[/yellow]             Show this message\n\n"
        "[bold cyan]Example:[/bold cyan]\n"
        "  [white]dev run main.dev[/white]\n\n"
        "[dim]v3.0: else · while · def/return · and/or/not · string methods · inline comments[/dim]",
        title="[bold yellow]DevLang CLI[/bold yellow]",
        border_style="cyan", expand=False
    ))

def main():
    show_banner()
    args = sys.argv[1:]
    if not args: show_usage(); sys.exit(0)

    if args[0] == 'run':
        if len(args) < 2: error("Missing file.  Usage:  dev run <file.dev>"); sys.exit(1)
        filepath = args[1]
    elif args[0] == 'version':
        con().print("  [bold cyan]DevLang[/bold cyan] [yellow]v3.0.0[/yellow]"); sys.exit(0)
    elif args[0] == 'help':
        show_usage(); sys.exit(0)
    else:
        filepath = args[0]

    if not filepath.endswith('.dev'):
        warn(f"File '{filepath}' does not have a .dev extension.")
    if not os.path.exists(filepath):
        error(f"File not found: '{filepath}'"); sys.exit(1)

    con().print(f"  [dim]Running:[/dim] [bold white]{filepath}[/bold white]\n")
    t0  = time.perf_counter()
    ast = load_ast_cached(filepath)
    t1  = time.perf_counter()
    variables, functions = {}, {}
    try:
        run_block(ast, variables, functions)
    except KeyboardInterrupt:
        con().print("\n  [bold yellow]Interrupted.[/bold yellow]"); sys.exit(0)
    t2 = time.perf_counter()
    con().print(
        f"\n  [dim]─── finished in {(t2-t0)*1000:.1f}ms "
        f"(parse {(t1-t0)*1000:.1f}ms · exec {(t2-t1)*1000:.1f}ms) ───[/dim]"
    )

if __name__ == '__main__':
    main()