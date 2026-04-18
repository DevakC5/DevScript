import sys
import os
from lexer import Lexer, LexerError
from parser import Parser, ParserError
from interpreter import Interpreter

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.dev>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    try:
        with open(file_path, 'r') as f:
            code = f.read()

        # 1. Lexical Analysis
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # 2. Parsing
        parser = Parser(tokens)
        commands = parser.parse()

        # 3. Execution
        interpreter = Interpreter()
        interpreter.execute(commands)

    except (LexerError, ParserError) as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
