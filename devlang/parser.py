# devlang/parser.py — source → AST

from __future__ import annotations
import re

from .nodes import (SayNode, LetNode, InputNode, IfNode, RepeatNode,
                    WhileNode, ForNode, FuncDefNode, ReturnNode, CallNode,
                    ImportNode, BreakNode, ContinueNode, ExprNode,
                    StructDefNode, EnumDefNode, SpawnNode,
                    AsyncFuncDefNode, AsyncAwaitNode)
from .lexer import tokenise, strip_inline_comment
from .evaluator import split_args
from .console import error, warn

RE_VARNAME = re.compile(r'^[a-zA-Z_]\w*$')
RE_BLOCK   = re.compile(r'^(if|repeat|while|for|def|struct|enum|spawn)\b')


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
                error(f"'input' expects: input <name> [options] -> \"prompt\"", lno)
                i += 1; continue
            var_part, _, prompt_part = rest.partition('->')
            var_part = var_part.strip()
            # Parse modifiers in order: mask, default, as — each stripped when found
            mask = var_part.endswith(' mask')
            if mask:
                var_part = var_part[:-5].rstrip()
            m_def = re.search(r'\s+default\s+(.+?)\s*$', var_part)
            default = m_def.group(1).strip() if m_def else None
            if default:
                var_part = var_part[:m_def.start()].rstrip()
            m_as = re.search(r'\s+as\s+(num)\s*$', var_part)
            as_type = m_as.group(1) if m_as else None
            if as_type:
                var_part = var_part[:m_as.start()].rstrip()
            var_name = var_part.strip()
            if not RE_VARNAME.match(var_name):
                error(f"Invalid variable name: '{var_name}'", lno); i += 1; continue
            if default:
                if (default.startswith('"') and default.endswith('"')) or \
                   (default.startswith("'") and default.endswith("'")):
                    default = default[1:-1]
            prompt = prompt_part.strip().strip('"').strip("'")
            ast.append(InputNode(var_name, prompt, lno, as_type=as_type, default=default, mask=mask))
            i += 1

        # ── if / elif ─────────────────────────────────────
        elif cmd == 'if':
            if '->' not in ln:
                error(f"'if' block missing '->': {ln}", lno); i += 1; continue
            cond_part, _, inline = ln.partition('->')
            cond_expr = cond_part[2:].strip()
            inline    = inline.strip()
            if inline:
                body_src  = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos  = [lno]
                elif_branches = []
                else_src, else_nos = [], []
                i += 1
            else:
                body_src, body_nos, elif_branches, else_src, else_nos, i = _extract_if_block(lines, line_nos, i + 1)
            # Build if-elif chain as nested IfNodes
            result_if = IfNode(cond_expr, parse(body_src, body_nos), [], lno)
            cur = result_if
            for ec, eb, en in elif_branches:
                n = IfNode(ec, parse(eb, en), [], lno)
                cur.else_body = [n]
                cur = n
            cur.else_body = parse(else_src, else_nos)
            ast.append(result_if)

        # ── else / elif (stray) ──────────────────────────
        elif cmd == 'else':
            warn("Unexpected 'else' without matching 'if'.", lno); i += 1

        elif cmd == 'elif':
            warn("Unexpected 'elif' without matching 'if'.", lno); i += 1

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

        # ── for ──────────────────────────────────────────
        elif cmd == 'for':
            # for <var> in <iterable> ->
            m = re.match(r'^for\s+([a-zA-Z_]\w*)\s+in\s+(.+?)\s*->', ln)
            if not m:
                error(f"'for' syntax: for var in list -> ... end   got: {ln}", lno)
                i += 1; continue
            var_name = m.group(1)
            iterable_expr = m.group(2)
            _, _, inline = ln.partition('->')
            inline = inline.strip()
            if inline:
                body_src = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos = [lno]; i += 1
            else:
                body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(ForNode(var_name, iterable_expr, parse(body_src, body_nos), lno))

        # ── async def ────────────────────────────────────
        elif cmd == 'async' and 'def' in ln:
            ln2 = ln.split(None, 1)[1] if ' ' in ln else ''
            m = re.match(r'^def\s+([a-zA-Z_]\w*)\s*\((.*?)\)\s*->', ln2)
            if not m:
                error(f"'async def' syntax: async def name(params) ->  …  end   got: {ln}", lno)
                i += 1; continue
            fname  = m.group(1)
            params = [p.strip() for p in m.group(2).split(',') if p.strip()]
            body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(AsyncFuncDefNode(fname, params, parse(body_src, body_nos), lno))

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

        # ── spawn ────────────────────────────────────────
        elif cmd == 'spawn':
            if '->' not in ln:
                error(f"'spawn' block missing '->': {ln}", lno); i += 1; continue
            _, _, inline = ln.partition('->')
            inline = inline.strip()
            if inline:
                body_src = [inline[:-3].strip()] if inline.endswith('end') else [inline]
                body_nos = [lno]; i += 1
            else:
                body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            ast.append(SpawnNode(parse(body_src, body_nos), lno))

        # ── return ───────────────────────────────────────
        elif cmd == 'return':
            ast.append(ReturnNode(ln[6:].strip(), lno))
            i += 1

        # ── break / continue ──────────────────────────────
        elif cmd == 'break':
            ast.append(BreakNode(lno))
            i += 1

        elif cmd == 'continue':
            ast.append(ContinueNode(lno))
            i += 1

        # ── import ───────────────────────────────────────
        elif cmd == 'import':
            ast.append(ImportNode(ln[6:].strip(), lno))
            i += 1

        # ── struct ────────────────────────────────────────
        elif cmd == 'struct':
            m = re.match(r'^struct\s+([a-zA-Z_]\w*)\s*->', ln)
            if not m:
                error(f"'struct' syntax: struct Name -> ... end   got: {ln}", lno)
                i += 1; continue
            sname = m.group(1)
            body_src, body_nos, i = _extract_block(lines, line_nos, i + 1)
            fields = []
            for bline in body_src:
                bt = tokenise(strip_inline_comment(bline).strip())
                if len(bt) >= 3 and bt[0] == 'let' and bt[2] == '=':
                    fname = bt[1]
                    fdefault = ' '.join(bt[3:])
                    if not RE_VARNAME.match(fname):
                        error(f"Invalid field name: '{fname}'", lno)
                        continue
                    fields.append((fname, fdefault))
            ast.append(StructDefNode(sname, fields, lno))

        # ── enum ──────────────────────────────────────────
        elif cmd == 'enum':
            m = re.match(r'^enum\s+([a-zA-Z_]\w*)\s*->\s*(.+?)\s*$', ln)
            if not m:
                error(f"'enum' syntax: enum Name -> A, B, C   got: {ln}", lno)
                i += 1; continue
            ename = m.group(1)
            values = [v.strip() for v in m.group(2).split(',') if v.strip()]
            if not values:
                error("enum must have at least one value", lno)
                i += 1; continue
            for v in values:
                if not RE_VARNAME.match(v):
                    error(f"Invalid enum value: '{v}'", lno)
            ast.append(EnumDefNode(ename, values, lno))
            i += 1

        # ── end (stray) ──────────────────────────────────
        elif cmd == 'end':
            warn("Unexpected 'end'.", lno); i += 1

        # ── bare function / method call ───────────────────
        elif '(' in ln:
            m_fn = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', ln)
            m_meth = re.match(r'^([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\((.*)\)$', ln)
            if m_fn:
                ast.append(CallNode(m_fn.group(1), m_fn.group(2).strip(), lno))
                i += 1
            elif m_meth:
                ast.append(ExprNode(ln, lno))
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
    body, b_nos = [], []
    elif_branches = []          # list of (cond, body_src, body_nos)
    else_body, e_nos = [], []
    state = 'body'              # 'body' | 'elif' | 'else'
    i = start
    while i < len(lines):
        ln = strip_inline_comment(lines[i]).strip()
        lno = line_nos[i]

        # elif must be checked before RE_BLOCK (which also matches 'elif')
        if depth == 1 and ln.startswith('elif '):
            m_elif = re.match(r'^elif\s+(.+?)\s*->\s*(.*)', ln)
            if not m_elif:
                error(f"'elif' syntax: elif <cond> ->  …  got: {ln}", lno)
                i += 1; continue
            elif_cond = m_elif.group(1).strip()
            elif_inline = m_elif.group(2).strip()
            if elif_inline:
                eb = [elif_inline[:-3].strip()] if elif_inline.endswith('end') else [elif_inline]
                en = [lno]
                i += 1
            else:
                # Extract elif body manually (stops at else/elif/end at depth 1)
                eb, en = [], []
                elif_depth = 1
                i += 1
                while i < len(lines):
                    ln2 = strip_inline_comment(lines[i]).strip()
                    if ln2 == 'end':
                        elif_depth -= 1
                        if elif_depth == 0:
                            i += 1; break
                    elif elif_depth == 1 and (ln2 == 'else' or ln2.startswith('elif ')):
                        break
                    elif RE_BLOCK.match(ln2) and '->' in ln2:
                        elif_depth += 1
                    eb.append(lines[i]); en.append(line_nos[i]); i += 1
            elif_branches.append((elif_cond, eb, en))
            continue

        if depth == 1 and ln == 'else':
            state = 'else'; i += 1; continue

        # Track nested block depth (skipping elif which doesn't nest)
        if not ln.startswith('elif ') and RE_BLOCK.match(ln) and '->' in ln:
            depth += 1

        if ln == 'end':
            depth -= 1
            if depth == 0:
                return body, b_nos, elif_branches, else_body, e_nos, i + 1

        if state == 'else':
            else_body.append(lines[i]); e_nos.append(line_nos[i])
        else:
            body.append(lines[i]); b_nos.append(line_nos[i])
        i += 1

    near = line_nos[start - 1] if start > 0 else '?'
    error(f"Missing 'end' for 'if' block near line {near}.")
    return body, b_nos, elif_branches, else_body, e_nos, i