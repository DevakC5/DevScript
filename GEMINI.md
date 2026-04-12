# DevLang — Clean, Beginner-Friendly Programming Language

## Project Overview
DevLang is a modular, high-level programming language designed for simplicity and readability. It features an interpreter written in Python, leveraging the `rich` library for a polished CLI experience. The project includes a full lexer, parser, and AST-based executor.

### Key Technologies
- **Python 3.7+**: Core interpreter and implementation.
- **Rich**: Enhanced terminal output and formatting.
- **AST (Abstract Syntax Tree)**: Intermediate representation for execution.
- **Caching**: `.devc` files for faster execution of pre-parsed source files.

## Directory Structure
- `devlang/`: Core package containing the interpreter implementation.
    - `lexer.py`: Tokenizes source code.
    - `parser.py`: Generates AST from tokens.
    - `nodes.py`: Defines AST node structures.
    - `executor.py`: Handles runtime execution of the AST.
    - `cli.py`: Command-line interface logic.
    - `console.py`: Utility for styled terminal output.
    - `cache.py`: Manages AST caching for performance.
- `docs/`: Documentation and references.
    - `syntax_ref.md`: Comprehensive guide to DevLang syntax.
- `scripts/`: Example programs and demo scripts.
    - `main.dev`: Full-featured demo of DevLang v3.0 capabilities.

## Building and Running
To run DevLang scripts, use the CLI:
```bash
# Run a DevLang program
python -m devlang.cli run scripts/main.dev

# Or use the installed entry point if available
dev run scripts/main.dev
```

### Installation
The project can be installed locally via `setup.py`:
```bash
pip install -e devlang/
```

## Development Conventions
- **Syntax**: Blocks (if, while, repeat, def) must always be terminated with `end`.
- **Indentation**: While the parser is generally flexible, consistent indentation is recommended for readability (as seen in `main.dev`).
- **Error Handling**: Use the custom error/warning utilities in `devlang/console.py` for consistent reporting.
- **Caching**: Changes to `.dev` files automatically trigger a cache invalidation and rebuild of `.devc` files.
- **Testing**: New features should be added to `scripts/main.dev` for manual validation and to demonstrate usage.

## Future Roadmap (TODO)
- [ ] Implement robust unit tests for the lexer and parser.
- [ ] Add more comprehensive standard library functions.
- [ ] Improve error messages with line/column tracking.
