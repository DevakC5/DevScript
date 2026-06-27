# devlang/cli.py — command-line interface

from __future__ import annotations
import sys
import os
import time

from devlang import __version__
from .console import con, panel, error, warn
from .cache import load_or_parse
from .executor import run_block
from .lexer import strip_inline_comment
from .parser import parse


def show_banner():
    from rich.text import Text
    txt = Text()
    txt.append("  DevLang Interpreter ", style="bold cyan")
    txt.append(f"v{__version__}", style="bold yellow")
    txt.append("  ⚡ modular build", style="dim green")
    txt.append("\n  Clean · Readable · Beginner-Friendly", style="dim white")
    con().print(panel(txt, border_style="cyan"))
    con().print()


def show_usage():
    con().print(panel(
        "[bold cyan]Commands:[/bold cyan]\n"
        "  [yellow]dev run [white]<file.dev>[/white][/yellow]    Run a DevLang program\n"
        "  [yellow]dev repl[/yellow]               Start interactive REPL\n"
        "  [yellow]dev watch [white]<file.dev>[/white][/yellow]  Watch & auto-reload on changes\n"
        "  [yellow]dev check [white]<file.dev>[/white][/yellow]  Syntax-check a file\n"
        "  [yellow]dev fmt [white]<file.dev>[/white][/yellow]    Format a .dev file\n"
        "  [yellow]dev install [white]<url>[/white][/yellow]     Install a package from URL\n"
        "  [yellow]dev lsp[/yellow]                  Start Language Server (stdio)\n"
        "  [yellow]dev version[/yellow]            Show interpreter version\n"
        "  [yellow]dev help[/yellow]               Show this help message\n\n"
        "[bold cyan]Example:[/bold cyan]\n"
        "  [white]dev run main.dev[/white]\n\n"
        "[dim]Cache: .devc files are auto-rebuilt when source changes.[/dim]",
        title="[bold yellow]DevLang CLI[/bold yellow]",
        border_style="cyan"
    ))


def run_file(filepath: str):
    if not filepath.endswith('.dev'):
        warn(f"'{filepath}' does not have a .dev extension. Proceeding anyway.")

    if not os.path.exists(filepath):
        error(f"File not found: '{filepath}'")
        sys.exit(1)

    con().print(f"  [dim]Running:[/dim] [bold white]{filepath}[/bold white]\n")

    t0  = time.perf_counter()
    from .evaluator import clear_cache
    clear_cache()
    ast = load_or_parse(filepath)
    t1  = time.perf_counter()

    variables, functions = {}, {}
    try:
        run_block(ast, variables, functions)
    except KeyboardInterrupt:
        con().print("\n  [bold yellow]Interrupted.[/bold yellow]")
        sys.exit(0)

    t2 = time.perf_counter()
    con().print(
        f"\n  [dim]─── finished in {(t2 - t0) * 1000:.1f}ms "
        f"(parse/cache {(t1 - t0) * 1000:.1f}ms · "
        f"exec {(t2 - t1) * 1000:.1f}ms) ───[/dim]"
    )


def _repl_completer():
    """Build a prompt_toolkit WordCompleter from DevLang keywords."""
    from prompt_toolkit.completion import WordCompleter
    keywords = [
        'say', 'let', 'if', 'else', 'elif', 'end', 'while', 'for',
        'in', 'repeat', 'def', 'return', 'break', 'continue',
        'import', 'input', 'true', 'false', 'not', 'and', 'or',
        'as', 'default', 'mask',
    ]
    return WordCompleter(keywords, ignore_case=True)


def _repl_show_vars(variables: dict):
    from .console import con
    if not variables:
        con().print("  [dim](no variables)[/dim]")
        return
    for k, v in sorted(variables.items()):
        con().print(f"  [cyan]{k}[/cyan] = [yellow]{v!r}[/yellow]")


def _repl_show_help():
    from .console import con
    con().print(
        "  [bold]DevLang REPL[/bold]\n"
        "  Type DevLang statements. Multi-line blocks (if..end, def..end) "
        "are supported — use continuation prompt.\n\n"
        "  [cyan].exit[/cyan]  Exit the REPL\n"
        "  [cyan].vars[/cyan]  Show current variables\n"
        "  [cyan].help[/cyan]  Show this message\n"
        "  [cyan]Ctrl-C[/cyan]  Cancel current input"
    )


def run_repl():
    con().print("  [cyan]DevLang REPL — type '.exit' to quit, '.help' for info[/cyan]\n")

    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style

        history_file = os.path.expanduser("~/.devlang_history")
        style = Style.from_dict({'prompt': 'cyan', 'continuation': 'dim'})
        session = PromptSession(
            history=FileHistory(history_file),
            completer=_repl_completer(),
            style=style,
            complete_while_typing=True,
        )
        _run_repl_ptk(session)
    except ImportError:
        _run_repl_simple()
    except Exception:
        _run_repl_simple()


def _run_repl_ptk(session):
    from .evaluator import clear_cache
    variables, functions = {}, {}
    buf = []
    meta_commands = {'.exit', '.vars', '.help', '.clear'}

    while True:
        try:
            prompt_str = "  [cyan]⟩⟩⟩[/cyan] " if not buf else "  [dim]...[/dim] "
            line = session.prompt(prompt_str)
        except KeyboardInterrupt:
            if buf:
                con().print("  [yellow]Cancelled[/yellow]")
                buf = []
            continue
        except EOFError:
            con().print("\n  [dim]bye[/dim]")
            break

        if not line and not buf:
            continue

        line = line.strip()
        if line in ('.exit', 'exit'):
            break
        if line == '.vars':
            _repl_show_vars(variables)
            continue
        if line == '.help':
            _repl_show_help()
            continue
        if line == '.clear':
            buf = []
            variables.clear()
            functions.clear()
            con().print("  [dim]Cleared variables and buffer[/dim]")
            continue

        buf.append(line)

        src = '\n'.join(buf)
        try:
            clear_cache()
            lines = src.splitlines()
            line_nos = list(range(1, len(lines) + 1))
            ast = parse(lines, line_nos)
            run_block(ast, variables, functions)
            buf = []
        except Exception as e:
            err_str = str(e)
            if 'Missing' in err_str and 'end' in err_str:
                continue
            if 'was never closed' in err_str:
                continue
            error(f"REPL: {e}")
            buf = []


def _run_repl_simple():
    """Fallback single-line REPL (no prompt_toolkit)."""
    from .evaluator import clear_cache
    con().print("  [dim](single-line mode — install prompt_toolkit for multi-line)[/dim]")
    variables, functions = {}, {}
    while True:
        try:
            line = input("  [cyan]⟩⟩⟩[/cyan] ")
        except (EOFError, KeyboardInterrupt):
            con().print("\n  [dim]bye[/dim]")
            break
        if not line:
            continue
        line = line.strip()
        if line in ('.exit', 'exit'):
            break
        if line == '.vars':
            _repl_show_vars(variables)
            continue
        if line == '.help':
            _repl_show_help()
            continue
        try:
            clear_cache()
            ast = parse([line], [1])
            run_block(ast, variables, functions)
        except Exception as e:
            error(f"REPL: {e}")


def run_watch(filepath: str):
    if not os.path.exists(filepath):
        error(f"File not found: '{filepath}'")
        return

    con().print(f"  Watching [bold white]{filepath}[/bold white] — [dim]Ctrl+C to stop[/dim]\n")
    last_mtime = os.path.getmtime(filepath)

    try:
        while True:
            time.sleep(0.5)
            mtime = os.path.getmtime(filepath)
            if mtime != last_mtime:
                last_mtime = mtime
                con().print("  [dim](file changed, re-running)[/dim]\n")
                run_file(filepath)
                con().print(f"\n  Watching [bold white]{filepath}[/bold white] — [dim]Ctrl+C to stop[/dim]\n")
    except KeyboardInterrupt:
        con().print("\n  [yellow]Watch stopped.[/yellow]")


def check_file(filepath: str):
    if not os.path.exists(filepath):
        error(f"File not found: '{filepath}'")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    lines = source.splitlines()
    line_nos = list(range(1, len(lines) + 1))
    try:
        ast = parse(lines, line_nos)
        con().print(f"  [bold green]✓[/bold green] Syntax OK — {len(ast)} top-level node(s)")
    except Exception as e:
        error(f"Syntax error: {e}")


def fmt_file(filepath: str):
    if not os.path.exists(filepath):
        error(f"File not found: '{filepath}'")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    lines = source.splitlines()
    line_nos = list(range(1, len(lines) + 1))
    try:
        ast = parse(lines, line_nos)
    except Exception as e:
        error(f"Cannot format — syntax error: {e}")
        return
    # Simple normalizing pretty-printer
    out_lines = []
    indent = 0
    for i, raw in enumerate(source.splitlines()):
        stripped = strip_inline_comment(raw).strip()
        if stripped.startswith('#') or not stripped:
            out_lines.append(raw)
            continue
        trimmed = raw.lstrip()
        if trimmed.startswith('end') or trimmed.startswith('else') or trimmed.startswith('elif '):
            indent = max(0, indent - 1)
        out_lines.append('    ' * indent + trimmed)
        if any(trimmed.startswith(k) for k in ('if ', 'elif ', 'else', 'repeat ', 'while ', 'for ', 'def ')):
            indent += 1
    out = '\n'.join(out_lines)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(out)
    con().print(f"  [bold green]✓[/bold green] Formatted '{filepath}'")


def run_install(pkg: str):
    import urllib.request
    libs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'libs')
    os.makedirs(libs_dir, exist_ok=True)

    # Resolve URL
    if pkg.startswith(('http://', 'https://')):
        url = pkg
    elif pkg.count('/') >= 2:
        url = f'https://raw.githubusercontent.com/{pkg}'
    else:
        url = f'https://raw.githubusercontent.com/{pkg}/{pkg}.dev'

    pkg_name = os.path.basename(url.split('?')[0])
    if not pkg_name.endswith('.dev'):
        pkg_name += '.dev'
    dest = os.path.join(libs_dir, pkg_name)

    con().print(f"  [dim]Downloading[/dim] [yellow]{url}[/yellow]")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            content = resp.read().decode('utf-8')
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        con().print(f"  [bold green]✓[/bold green] Installed to [cyan]{dest}[/cyan]")
    except Exception as e:
        error(f"Failed to install '{pkg}': {e}")


def main():
    show_banner()
    args = sys.argv[1:]

    if not args:
        show_usage()
        sys.exit(0)

    cmd = args[0]

    if cmd == 'run':
        if len(args) < 2:
            error("Missing file argument.  Usage:  dev run <file.dev>")
            sys.exit(1)
        run_file(args[1])

    elif cmd == 'repl':
        run_repl()

    elif cmd == 'watch':
        if len(args) < 2:
            error("Missing file argument.  Usage:  dev watch <file.dev>")
            sys.exit(1)
        run_watch(args[1])

    elif cmd == 'check':
        if len(args) < 2:
            error("Missing file argument.  Usage:  dev check <file.dev>")
            sys.exit(1)
        check_file(args[1])

    elif cmd == 'fmt':
        if len(args) < 2:
            error("Missing file argument.  Usage:  dev fmt <file.dev>")
            sys.exit(1)
        fmt_file(args[1])

    elif cmd == 'install':
        if len(args) < 2:
            error("Missing package.  Usage:  dev install <url> or <user>/<repo>/<path>")
            sys.exit(1)
        run_install(args[1])

    elif cmd == 'lsp':
        from .lsp import run_lsp
        run_lsp()

    elif cmd == 'version':
        con().print(f"  [bold cyan]DevLang[/bold cyan] [yellow]v{__version__}[/yellow]  [dim green]⚡ modular[/dim green]")

    elif cmd == 'help':
        show_usage()

    else:
        # Treat bare argument as filename: dev main.dev
        run_file(cmd)


if __name__ == "__main__":
    main()