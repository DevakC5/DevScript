# DevScript 🚀

DevScript is a lightweight, modular interpreted language designed for simplicity and ease of use, featuring built-in support for array operations and mathematical functions.

## ✨ Features

- **Simple Variable Assignment**: Use `let` to define variables.
- **Rich Array Support**: 
  - Element-wise addition and multiplication.
  - Scalar multiplication for arrays.
  - Built-in functions like `sum()` and `mean()`.
- **Mathematical Library**: Includes `sqrt()`, `pow()`, `sin()`, and `cos()`.
- **Control Flow**: Intuitive `if-else` blocks.
- **Interactive REPL**: An interactive shell for testing code snippets.
- **Script Execution**: Run `.dev` files directly from the command line.

## 🚀 Getting Started

### Installation

Ensure you have Python 3.10+ installed. Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/DevakC5/DevScript.git
cd DevScript
```

### Running the Interpreter

You can start the interactive REPL:
```bash
python3 main.py
```

Or run a DevScript file:
```bash
python3 main.py test_final.dev
```

## 📖 Language Guide

### Variables and Types
```devscript
let x = 10
let name = "DevScript"
let my_array = array([1, 2, 3, 4])
```

### Array Operations
DevScript makes array manipulation effortless:
```devscript
let a = array([1, 2, 3])
let b = array([4, 5, 6])

let sum_arr = a + b       // Result: array([5, 7, 9])
let scalar_mul = a * 2    // Result: array([2, 4, 6])
let element_mul = a * b   // Result: array([4, 10, 18])

say sum(a)                // Prints the sum of elements
say mean(a)               // Prints the average of elements
```

### Control Flow
Use `if`, `else`, and `end` for conditional logic:
```devscript
let score = 85

if score > 80 ->
  say "Excellent!"
else ->
  say "Keep practicing!"
end
```

### Math Functions
```devscript
say sqrt(16)              // 4.0
say pow(2, 3)             // 8.0
say sin(3.14159)          // ~0
```

## 🛠️ Project Structure

- `devscript/core/`: The heart of the interpreter (Lexer, Parser, Interpreter).
- `devscript/cli/`: CLI and REPL implementation.
- `devscript/stdlib/`: Standard library containing `arraylib` and `mathlib`.
- `devscript/utils/`: Error handling and token definitions.

## 📜 License
This project is open source and available under the MIT License.
