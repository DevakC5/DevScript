# DevLang — AGENTS.md

## Project
A custom programming language interpreter written in Python.  
Single package `devlang/`. No CI, linter, or typechecker.

## Setup & Run
```bash
pip install -e .
dev run scripts/main.dev
python -m devlang.cli run scripts/main.dev   # same, without install
```

## Test
```bash
python -m pytest tests/
dev run scripts/test_all_features.dev         # end-to-end
dev check <file.dev>                          # syntax check
dev fmt <file.dev>                            # format
```

## Key Architecture
- **Entrypoint**: `devlang.cli:main` → `run_file()` → `load_or_parse()` (lex/parse/cache) → `run_block()` (AST walker, `devlang/executor.py`)
- **Pipeline**: source → `lexer.tokenise()` → `parser.parse()` → AST (node objects in `nodes.py`) → `executor.run_block()`
- **Expressions** compiled to closures by `evaluator._compile_expr()`, cached in `_EXPR_CACHE`
- **Cache**: `.devc` files (pickled AST) beside `.dev` source, invalidated on md5 or version change

## Language Features
- `elif <cond> ->` (nested via chained `IfNode` in else_body)
- `break` / `continue` in `while`, `for`, `repeat` loops (via `BreakSignal`/`ContinueSignal` exceptions)
- `for i in N ->` (numeric range, sugar for `range(N)`)
- Dict literals `{"key": val}`, string-key indexing `d["key"]`
- String/list slicing: `x[start:stop:step]`
- List methods: `.append(x)`, `.pop()`, `.sort()`, `.sum()`, `.mean()`, `.min()`, `.max()`
- Expression statements: method calls as statements (`lst.append(4)`)
- Import auto-appends `.dev` extension, resolves: same dir → `libs/` → `scripts/`
- Circular import detection (tracks absolute paths in `_import_stack`)
- Enhanced `input` with `as num`, `default`, `mask`
- `struct Name -> ... end` — user-defined structs with named fields, defaults, dot access
- `enum Name -> A, B, C` — named constant values
- `spawn -> ... end` — run block on background thread, handle in `_last_spawn`
- `async def name() -> ... end` / `await expr` — thread-based coroutines
- `matrix()` data type with `.T`, `.dot()`, element-wise ops, pretty display
- `json_loads`, `json_dumps`, `json_read`, `csv_parse`, `csv_read`, `csv_write`
- Terminal UI: `menu`, `confirm`, `password`, `say_table`, `say_panel`, `say_tree`, progress bars
- Live display: `live_start`, `live_set`, `live_stop` (Rich Live)
- Events: `wait`, `set_timeout`, `set_interval`, `clear_timer`, `wait_all`, `key_wait`
- `dev repl` (multi-line with prompt_toolkit), `dev check`, `dev fmt`, `dev watch`, `dev install`, `dev lsp`

## Built-in Functions (in evaluator.py BUILTINS dict)
`time`, `_sleep`/`wait`, `file_read`, `file_write`, `range`, `zeros`, `ones`, `arange`, `sum`, `mean`, `min`, `max`, `matmul`, `sqrt`, `sin`, `cos`, `tan`, `floor`, `ceil`, `round`, `abs`, `rand`, `randint`, `matrix`, `zeros_matrix`, `identity`, `thread_join`, `json_loads`, `json_dumps`, `json_read`, `csv_parse`, `csv_read`, `csv_write`, `menu`, `confirm`, `password`, `say_table`, `say_panel`, `say_tree`, `progress_start`, `progress_tick`, `progress_stop`, `live_start`, `live_set`, `live_stop`, `set_timeout`, `set_interval`, `clear_timer`, `wait_all`, `key_wait`, `cv_*` (functional stubs), `plot_*` (SVG chart rendering)

## Libs (import without path)
`math` (PI, E, abs, fact, clamp, even, odd), `file` (read, write), `chart` (bar, line, scatter, ...), `vision` (imread, blur, grayscale, ...), `time` (sleep, now), `str` (repeat, split, join), `list` (first, last, reverse, contains), `interact` (pick, yesno, secret, show_table, show_panel, show_tree), `event` (after, every, cancel, pause, key)

## Key Files
- `devlang/evaluator.py`: Expression compiler, all builtins, Matrix class, Coro class, `_compile_expr` ~400 lines
- `devlang/executor.py`: AST walker `run_block()`, `call_function()`
- `devlang/parser.py`: Lex + parse, block extraction, inline `end` support
- `devlang/nodes.py`: All AST node classes + `StructInstance`, `Coro`
- `devlang/cli.py`: CLI entrypoint, REPL, watch, install, LSP commands
- `devlang/lsp.py`: stdio JSON-RPC Language Server
- `devlang/cache.py`: `.devc` pickle cache, md5 invalidation
- `libs/`: Standard library scripts (importable by name)

## Constraints
- All blocks (`if`, `while`, `repeat`, `for`, `def`, `spawn`, `struct`, `enum`) must end with `end`
- `else` on its own line; `elif <cond> ->` on its own line
- `return` only works inside `def` / `async def`
- `while` loops capped at 100,000 iterations
- Dependency: `rich` (>=3.7)
- C extension `devmath.{dll,so}` for matmul (optional, ignored if absent)
- REPL requires `prompt_toolkit` for multi-line mode (falls back to single-line)
