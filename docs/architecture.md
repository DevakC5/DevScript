# DevScript Architecture

This document describes the internal design and the pipeline of the DevScript interpreter.

## 1. High-Level Pipeline
The interpreter follows a classic pipeline:
**Source Code** $\rightarrow$ **Lexer** $\rightarrow$ **Parser** $\rightarrow$ **AST** $\rightarrow$ **Interpreter** $\rightarrow$ **Output**

### Step-by-Step Flow

#### A. Lexical Analysis (Lexer)
The `Lexer` takes the raw source code (string) and breaks it down into a sequence of **Tokens**.
- **Tokens** are the smallest meaningful units of the language (e.g., `LET`, `IDENTIFIER`, `NUMBER`, `PLUS`, `IF`, `ARROW`).
- The lexer uses regular expressions to identify these tokens and tracks line numbers for accurate error reporting.

#### B. Syntactic Analysis (Parser)
The `Parser` takes the stream of tokens and organizes them into a **Hierarchical Structure** called an **Abstract Syntax Tree (AST)**.
- The parser implements a recursive descent approach.
- It ensures that the tokens follow the grammar rules of DevScript (e.g., a `let` must be followed by an identifier and an equals sign).

#### C. Abstract Syntax Tree (AST)
The AST is a tree representation of the program. Nodes in the tree represent different operations:
- `AssignmentNode`: `let x = 10`
- `IfNode`: `if condition -> then_block else_block`
- `BinOpNode`: `a + b`
- `CallNode`: `sum(arr)`

#### D. Execution (Interpreter)
The `Interpreter` traverses the AST and executes the logic.
- **Environment**: The interpreter maintains an `Environment` (a symbol table) to store variable names and their corresponding values.
- **Evaluation**: Each AST node is evaluated recursively. For example, a `BinOpNode` evaluates its left and right children and then applies the operator.
- **Standard Library**: The interpreter can call Python functions defined in `stdlib` (like `arraylib` and `mathlib`) to extend the language's capabilities.

## 2. Key Components
- `devscript/core/lexer.py`: Tokenizes input.
- `devscript/core/parser.py`: Builds the AST.
- `devscript/core/ast_nodes.py`: Defines the structure of AST nodes.
- `devscript/core/interpreter.py`: Executes the AST.
- `devscript/core/environment.py`: Manages variable scoping.
