import sys
from rich.console import Console
from devscript.core.lexer import Lexer
from devscript.core.parser import Parser
from devscript.core.interpreter import Interpreter
from devscript.core.environment import Environment
from devscript.utils.errors import report_error, DevScriptError
from devscript.stdlib import mathlib, arraylib

console = Console()

def create_global_env():
    env = Environment()
    # Register mathlib
    env.define("sqrt", mathlib.sqrt)
    env.define("pow", mathlib.pow)
    env.define("sin", mathlib.sin)
    env.define("cos", mathlib.cos)
    # Register arraylib
    env.define("array", arraylib.array)
    env.define("sum", arraylib.sum)
    env.define("mean", arraylib.mean)
    env.define("len", len) # Python built-in len works for DevArray
    return env

def run_repl():
    global_env = create_global_env()
    interpreter = Interpreter(global_env)
    
    console.print("[bold green]DevScript REPL[/bold green] - Type 'exit' to quit")
    
    buffer = ""
    while True:
        try:
            prompt = ">>> " if not buffer else "... "
            line = input(prompt)
            
            if line.strip() == "exit":
                break
                
            buffer += line + "\n"
            
            # Basic check if the block is complete
            # We count 'if'/'while' and 'end'
            if "if" in buffer or "while" in buffer:
                opens = buffer.count("if") + buffer.count("while")
                closes = buffer.count("end")
                if opens > closes:
                    continue
            
            # Try to execute
            lexer = Lexer(buffer)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            block = parser.parse()
            interpreter.interpret(block)
            
            buffer = "" # Clear buffer after successful execution
            
        except (DevScriptError, Exception) as e:
            if isinstance(e, DevScriptError):
                report_error(e)
            else:
                console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
            buffer = "" # Clear buffer on error to avoid loop
