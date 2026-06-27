# devlang/lsp.py — Language Server Protocol (stdio JSON-RPC)

import sys
import json
import os
from .parser import parse
from .lexer import strip_inline_comment
from .console import error

_DOCUMENTS: dict[str, dict] = {}
_CAPABILITIES: dict = {}
_SERVER_INFO = {"name": "devlang-lsp", "version": "1.0.0"}

_KEYWORDS = [
    'say', 'let', 'if', 'else', 'elif', 'end', 'while', 'for', 'in',
    'repeat', 'def', 'async', 'return', 'break', 'continue', 'import',
    'input', 'struct', 'enum', 'spawn', 'true', 'false', 'not', 'and', 'or',
    'as', 'default', 'mask', 'await',
]

_BUILTIN_NAMES = [
    'time', 'sleep', 'file_read', 'file_write', 'range', 'zeros', 'ones',
    'arange', 'sum', 'mean', 'min', 'max', 'matmul', 'sqrt', 'sin', 'cos',
    'tan', 'floor', 'ceil', 'round', 'abs', 'rand', 'randint',
    'matrix', 'zeros_matrix', 'identity',
    'menu', 'confirm', 'password', 'say_table', 'say_panel', 'say_tree',
    'progress_start', 'progress_tick', 'progress_stop',
    'wait', 'set_timeout', 'set_interval', 'clear_timer', 'wait_all', 'key_wait',
    'live_start', 'live_set', 'live_stop',
    'thread_join', 'json_loads', 'json_dumps', 'json_read',
    'csv_parse', 'csv_read', 'csv_write',
]


def _read_message() -> dict | None:
    header = sys.stdin.readline()
    if not header:
        return None
    header = header.strip()
    if not header.startswith('Content-Length:'):
        return _read_message()
    length = int(header.split(':')[1].strip())
    while header.strip():
        header = sys.stdin.readline()
    body = sys.stdin.read(length)
    if not body:
        return None
    return json.loads(body)


def _send_response(msg: dict, req_id: int | None):
    resp = {"jsonrpc": "2.0"}
    if req_id is not None:
        resp["id"] = req_id
    resp.update(msg)
    body = json.dumps(resp, ensure_ascii=False)
    data = f"Content-Length: {len(body)}\r\n\r\n{body}"
    sys.stdout.write(data)
    sys.stdout.flush()


def _send_notification(method: str, params: dict):
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params}, ensure_ascii=False)
    data = f"Content-Length: {len(body)}\r\n\r\n{body}"
    sys.stdout.write(data)
    sys.stdout.flush()


def _check_syntax(uri: str) -> list[dict]:
    doc = _DOCUMENTS.get(uri)
    if not doc:
        return []
    text = doc.get('text', '')
    lines = text.splitlines()
    line_nos = list(range(1, len(lines) + 1))
    errors = []
    try:
        ast = parse(lines, line_nos)
    except Exception as e:
        errors.append({
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
            "severity": 1,
            "message": str(e),
            "source": "devlang"
        })
        return errors
    return errors


def _get_completions(line_text: str) -> list[dict]:
    items = []
    for kw in _KEYWORDS:
        items.append({"label": kw, "kind": 14, "detail": "keyword"})
    for bn in _BUILTIN_NAMES:
        items.append({"label": bn, "kind": 3, "detail": "builtin function"})
    return items


def _get_hover(line: str, col: int, text: str) -> dict | None:
    word = ''
    lines = text.splitlines()
    if line < len(lines):
        ln = lines[line]
        if col < len(ln):
            start = col
            while start > 0 and (ln[start - 1].isalnum() or ln[start - 1] == '_'):
                start -= 1
            end = col
            while end < len(ln) and (ln[end].isalnum() or ln[end] == '_'):
                end += 1
            word = ln[start:end]

    if not word:
        return None
    if word in _KEYWORDS:
        return {"contents": {"kind": "markdown", "value": f"**{word}** — DevLang keyword"}}
    if word in _BUILTIN_NAMES:
        return {"contents": {"kind": "markdown", "value": f"**{word}** — built-in function"}}
    return {"contents": {"kind": "markdown", "value": f"`{word}`"}}


def handle_message(msg: dict):
    method = msg.get('method', '')
    req_id = msg.get('id')
    params = msg.get('params', {})

    if method == 'initialize':
        _CAPABILITIES.update(params.get('capabilities', {}))
        _send_response({
            "result": {
                "capabilities": {
                    "textDocumentSync": 1,
                    "completionProvider": {"triggerCharacters": ['.', '(']},
                    "hoverProvider": True,
                    "documentFormattingProvider": True,
                },
                "serverInfo": _SERVER_INFO,
            }
        }, req_id)
        return

    if method == 'shutdown':
        _send_response({"result": None}, req_id)
        return

    if method == 'exit':
        sys.exit(0)

    if method == 'textDocument/didOpen':
        uri = params.get('textDocument', {}).get('uri', '')
        text = params.get('textDocument', {}).get('text', '')
        _DOCUMENTS[uri] = {'text': text, 'version': params.get('textDocument', {}).get('version', 0)}
        diags = _check_syntax(uri)
        if diags:
            _send_notification('textDocument/publishDiagnostics', {'uri': uri, 'diagnostics': diags})
        return

    if method == 'textDocument/didChange':
        uri = params.get('textDocument', {}).get('uri', '')
        changes = params.get('contentChanges', [])
        if changes:
            _DOCUMENTS[uri] = {'text': changes[-1].get('text', ''), 'version': params.get('textDocument', {}).get('version', 0)}
        diags = _check_syntax(uri)
        _send_notification('textDocument/publishDiagnostics', {'uri': uri, 'diagnostics': diags})
        return

    if method == 'textDocument/completion':
        uri = params.get('textDocument', {}).get('uri', '')
        pos = params.get('position', {})
        line = pos.get('line', 0)
        doc = _DOCUMENTS.get(uri, {})
        text = doc.get('text', '')
        lines = text.splitlines()
        line_text = lines[line] if line < len(lines) else ''
        items = _get_completions(line_text)
        _send_response({"result": {"isIncomplete": False, "items": items}}, req_id)
        return

    if method == 'textDocument/hover':
        uri = params.get('textDocument', {}).get('uri', '')
        pos = params.get('position', {})
        line = pos.get('line', 0)
        col = pos.get('character', 0)
        doc = _DOCUMENTS.get(uri, {})
        text = doc.get('text', '')
        hover = _get_hover(line, col, text)
        if hover:
            _send_response({"result": {"contents": hover["contents"]}}, req_id)
        else:
            _send_response({"result": None}, req_id)
        return

    if method == 'textDocument/formatting':
        uri = params.get('textDocument', {}).get('uri', '')
        doc = _DOCUMENTS.get(uri, {})
        text = doc.get('text', '')
        lines = text.splitlines()
        out_lines = []
        indent = 0
        for raw in lines:
            stripped = strip_inline_comment(raw).strip()
            if stripped.startswith('#') or not stripped:
                out_lines.append(raw)
                continue
            trimmed = raw.lstrip()
            if trimmed.startswith('end') or trimmed.startswith('else') or trimmed.startswith('elif '):
                indent = max(0, indent - 1)
            out_lines.append('    ' * indent + trimmed)
            if any(trimmed.startswith(k) for k in ('if ', 'elif ', 'else', 'repeat ', 'while ', 'for ', 'def ', 'spawn ', 'struct ')):
                indent += 1
        formatted = '\n'.join(out_lines)
        _send_response({"result": [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": len(lines), "character": 0}}, "newText": formatted}]}, req_id)
        return

    if req_id is not None:
        _send_response({"result": None}, req_id)


def run_lsp():
    while True:
        msg = _read_message()
        if msg is None:
            break
        try:
            handle_message(msg)
        except Exception as e:
            _send_response({"error": {"code": -32603, "message": str(e)}}, msg.get('id'))
