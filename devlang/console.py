# devlang/console.py — shared Rich console + helpers

from __future__ import annotations

_con = None

def con():
    global _con
    if _con is None:
        from rich.console import Console
        _con = Console()
    return _con

def panel(content, **kw):
    from rich.panel import Panel
    from rich import box as rbox
    kw.setdefault('box', rbox.ROUNDED)
    kw.setdefault('expand', False)
    return Panel(content, **kw)

def error(msg: str, line_no: int = None):
    loc = f"[bold red]Ln {line_no}:[/bold red] " if line_no else ""
    con().print(panel(
        f"{loc}[red]{msg}[/red]",
        title="[bold red]DevLang Error[/bold red]",
        border_style="red"
    ))

def warn(msg: str, line_no: int = None):
    loc = f"[yellow]Ln {line_no}:[/yellow] " if line_no else ""
    con().print(f"  [bold yellow]Warning:[/bold yellow] {loc}{msg}")