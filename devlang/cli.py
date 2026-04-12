# devlang/cli.py — command-line interface

from __future__ import annotations
import sys
import os
import time

from devlang import __version__
from .console import con, panel, error, warn
from .cache import load_or_parse
from .executor import run_block


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
        "  [yellow]dev run [white]<file.dev>[/white][/yellow]   Run a DevLang program\n"
        "  [yellow]dev version[/yellow]          Show interpreter version\n"
        "  [yellow]dev help[/yellow]             Show this help message\n\n"
        "[bold cyan]Example:[/bold cyan]\n"
        "  [white]dev run main.dev[/white]\n\n"
        "[dim]Cache: .devc files are auto-rebuilt when source changes.[/dim]\n"
        "[dim]v3.1: modular • else • while • def/return • and/or/not • string methods[/dim]",
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

    elif cmd == 'version':
        con().print(f"  [bold cyan]DevLang[/bold cyan] [yellow]v{__version__}[/yellow]  [dim green]⚡ modular[/dim green]")

    elif cmd == 'help':
        show_usage()

    else:
        # Treat bare argument as filename: dev main.dev
        run_file(cmd)


if __name__ == "__main__":
    main()