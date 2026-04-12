# devlang/parser.py — source → AST

from __future__ import annotations
import re

from .nodes import (SayNode, LetNode, InputNode, IfNode, RepeatNode,
                    WhileNode, FuncDefNode, ReturnNode, CallNode, ImportNode)
from .lexer import tokenise, strip_inline_comment
from .evaluator import split_args
from .console import error, warn

RE_VARNAME = re.compile(r'^[a-zA-Z_]\w*$')
RE_BLOCK   = re.compile(r'^(if|repeat|while|def)\b')


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

        # ── say ──────────────────────────────────────────
        if cmd == 'say':
            ast.append(SayNode(ln[3:].strip(), lno))
            i += 1

        # ── let ──────────────────────────────────────────
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

        # ── input ────────────────────────────────────────
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

        # ── if ───────────────────────────────────────────
        elif cmd == 'if':
            if '->' not in ln:
                error(f"'if' block missing '->': {ln}", lno); i += 1; continue
            cond_part, _, inline = ln.partition('->')
            cond_expr = cond_part[2:].strip()
            inline    = inline.strip()
            if inline:
                body_src  = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos  = [lno]
                else_src, else_nos = [], []
                i += 1
            else:
                body_src, body_nos, else_src, else_nos, i = _extract_if_block(lines, line_nos, i + 1)
            ast.append(IfNode(
                cond_expr,
                parse(body_src, body_nos),
                parse(else_src, else_nos),
                lno
            ))

        # ── else (stray) ─────────────────────────────────
        elif cmd == 'else':
            warn("Unexpected 'else' without matching 'if'.", lno); i += 1

        # ── repeat ───────────────────────────────────────
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

        # ── while ────────────────────────────────────────
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

        # ── def ──────────────────────────────────────────
        elif cmd == 'def':
            m = re.match(r'^def\s+([a-zA-Z_]\w*)\s*\((.*?)\)\s*->', ln)
            if not m:
                error(f"'def' syntax: def name(params) ->  …  end   got: {ln}", lno)
                i += 1; continue
            fname  = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(FuncDefNode(fname, params, parse(body_src, body_nos), lno))

        # ── return ───────────────────────────────────────
        elif cmd == 'return':
            ast.append(ReturnNode(ln[6:].strip(), lno))
            i += 1

        # ── import ───────────────────────────────────────
        elif cmd == 'import':
            ast.append(ImportNode(ln[6:].strip(), lno))
            i += 1

        # ── end (stray) ──────────────────────────────────
        elif cmd == 'end':
            warn("Unexpected 'end'.", lno); i += 1

        # ── bare function call ────────────────────────────
        elif RE_VARNAME.match(cmd) and '(' in ln:
            m2 = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', ln)
            if m2:
                ast.append(CallNode(m2.group(1), m2.group(2).strip(), lno))
                i += 1
            else:
                error(f"Unknown command: '{cmd}'", lno); i += 1

        else:
            error(f"Unknown command: '{cmd}'", lno); i += 1

    return ast


# ── Block extraction helpers ─────────────────────────────────────────────────

def _extract_block(lines, line_nos, start):
    depth, block, b_nos = 1, [], []
    i = start
    while i < len(lines):
        ln = strip_inline_comment(lines[i]).strip()
        if RE_BLOCK.match(ln) and '->' in ln: depth += 1
        if ln == 'end':
            depth -= 1
            if depth == 0: return block, b_nos, i + 1
        block.append(lines[i]); b_nos.append(line_nos[i]); i += 1
    near = line_nos[start - 1] if start > 0 else '?'
    error(f"Missing 'end' — block opened near line {near} was never closed.")
    return block, b_nos, i


def _extract_if_block(lines, line_nos, start):
    depth = 1
    body, b_nos, else_body, e_nos = [], [], [], []
    in_else = False
    i = start
    while i < len(lines):
        ln = strip_inline_comment(lines[i]).strip()
        if RE_BLOCK.match(ln) and '->' in ln: depth += 1
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
    near = line_nos[start - 1] if start > 0 else '?'
    error(f"Missing 'end' for 'if' block near line {near}.")
    return body, b_nos, else_body, e_nos, i