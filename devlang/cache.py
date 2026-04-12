# devlang/cache.py — bytecode cache (.devc files)
#
# Cache is stored alongside the source:  main.dev → main.devc
# Format: pickle of { 'hash': md5, 'version': str, 'ast': list }
#
# Cache is AUTOMATICALLY invalidated (rebuilt) when:
#   • Source file content changes  (md5 hash mismatch)
#   • DevLang interpreter version changes
#   • Cache file is missing or corrupt

from __future__ import annotations
import os
import pickle
import hashlib

from devlang import __version__
from .console import warn


def _hash(source: str) -> str:
    return hashlib.md5(source.encode()).hexdigest()


def _cache_path(filepath: str) -> str:
    return filepath + 'c'          # main.dev  →  main.devc


def load(filepath: str, source: str) -> list | None:
    """
    Try to load a valid cached AST.
    Returns the AST list on cache hit, or None on miss/invalid.
    """
    path = _cache_path(filepath)
    if not os.path.exists(path):
        return None

    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)

        if data.get('hash') != _hash(source):
            return None          # source changed → rebuild

        if data.get('version') != __version__:
            return None          # interpreter updated → rebuild

        return data['ast']       # ✅ cache hit

    except Exception:
        return None              # corrupt cache → rebuild silently


def save(filepath: str, source: str, ast: list):
    """
    Write AST to cache file.  Failure is non-fatal (just skipped).
    """
    path = _cache_path(filepath)
    try:
        with open(path, 'wb') as f:
            pickle.dump(
                {'hash': _hash(source), 'version': __version__, 'ast': ast},
                f,
                protocol=pickle.HIGHEST_PROTOCOL
            )
    except Exception as e:
        warn(f"Could not write cache file '{path}': {e}")


def load_or_parse(filepath: str) -> list:
    """
    Full pipeline:
      1. Read source
      2. Check cache → return if valid
      3. Parse fresh → save cache → return
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    cached = load(filepath, source)
    if cached is not None:
        return cached

    # Cache miss — parse from scratch
    from .parser import parse
    lines    = source.splitlines()
    line_nos = list(range(1, len(lines) + 1))
    ast      = parse(lines, line_nos)

    save(filepath, source, ast)
    return ast