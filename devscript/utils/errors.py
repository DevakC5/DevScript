from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

console = Console()

class DevScriptError(Exception):
    """Base class for all DevScript errors."""
    def __init__(self, message: str, line: int = None, column: int = None, source_code: str = None):
        self.message = message
        self.line = line
        self.column = column
        self.source_code = source_code
        super().__init__(self.message)

class LexerError(DevScriptError):
    """Errors that occur during lexical analysis."""
    pass

class ParserError(DevScriptError):
    """Errors that occur during parsing."""
    pass

class RuntimeError(DevScriptError):
    """Errors that occur during execution."""
    pass

def report_error(error: DevScriptError):
    """
    Uses rich to print a beautiful error message.
    """
    msg = Text(f"Error: {error.message}", style="bold red")
    
    if error.line is not None:
        loc = Text(f"→ Line {error.line}, Column {error.column if error.column else '?'}", style="yellow")
        msg.append("\n")
        msg.append(loc)

        if error.source_code:
            lines = error.source_code.splitlines()
            if 0 < error.line <= len(lines):
                code_line = lines[error.line - 1]
                
                # Create a syntax highlighted snippet of the failing line
                snippet = Syntax(code_line, "python", theme="monokai", line_numbers=False)
                
                # Create the pointer
                pointer_line = " " * (error.column - 1 if error.column else 0) + "^"
                pointer_text = Text(pointer_line, style="bold red")
                
                console.print(Panel(msg, title="DevScript Error", border_style="red"))
                console.print(snippet)
                console.print(pointer_text)
                return

    console.print(Panel(msg, title="DevScript Error", border_style="red"))
