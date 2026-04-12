# devlang/lexer.py — tokeniser and source pre-processing

from __future__ import annotations
import re

RE_TOKEN = re.compile(r'"[^"]*"|\'[^\']*\'|\S+')
RE_INT   = re.compile(r'^-?\d+$')
RE_FLOAT = re.compile(r'^-?\d+\.\d+$')


def tokenise(line: str) -> list[str]:
    return RE_TOKEN.findall(line)


def strip_inline_comment(line: str) -> str:
    """Remove everything after a # that is outside quotes."""
    in_q, q_char = False, ''
    for i, ch in enumerate(line):
        if in_q:
            if ch == q_char:
                in_q = False
        else:
            if ch in ('"', "'"):
                in_q, q_char = True, ch
            elif ch == '#':
                return line[:i]
    return line


def cast(val: str):
    """Try int → float → str."""
    if RE_INT.match(val):   return int(val)
    if RE_FLOAT.match(val): return float(val)
    return val