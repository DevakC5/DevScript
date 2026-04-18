import sys
import argparse
from rich.console import Console
from devscript.core.lexer import Lexer
from devscript.core.parser import Parser
from devscript.core.interpreter import Interpreter
from devscript.core.environment import Environment
from devscript.utils.errors import report_error, DevScriptError
from devscript.cli.repl import run_repl, create_global_env

console = Console()

def main():
    parser = argparse.ArgumentParser(description="DevScript Interpreter")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a .dev file")
    run_parser.add_argument("file", help="Path to the .dev file")

    # Repl command
    subparsers.add_parser("repl", help="Start interactive REPL")

    # Version command
    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if args.command == "run":
        run_file(args.file)
    elif args.command == "repl":
        run_repl()
    elif args.command == "version":
        console.print("DevScript version 0.1.0")
    else:
        parser.print_help()

def run_file(file_path):
    try:
        with open(file_path, 'r') as f:
            source = f.read()
        
        global_env = create_global_env()
        interpreter = Interpreter(global_env)
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        block = parser.parse()
        
        interpreter.interpret(block)
        
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] File {file_path} not found.")
    except (DevScriptError, Exception) as e:
        if isinstance(e, DevScriptError):
            report_error(e)
        else:
            console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
