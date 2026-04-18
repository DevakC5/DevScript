# DevScript Usage Guide

This guide explains how to run, test, and develop using the DevScript interpreter.

## 1. Running the Interpreter

### Interactive REPL
To enter the interactive mode where you can type DevScript code and get immediate results:
```bash
python3 main.py
```
Once inside the REPL, you can type your commands line by line. To exit, use `Ctrl+C` or `Ctrl+D`.

### Running a Script File
To execute a `.dev` file:
```bash
python3 main.py path/to/your_script.dev
```

## 2. Practical Examples

### Basic Arithmetic
Create a file named `calc.dev`:
```devscript
let a = 10
let b = 20
say a + b
```
Run it: `python3 main.py calc.dev`

### Working with Arrays
Create a file named `arrays.dev`:
```devscript
let vec1 = array([1, 2, 3])
let vec2 = array([4, 5, 6])
let result = vec1 + vec2
say result
say sum(result)
```
Run it: `python3 main.py arrays.dev`

## 3. Error Handling
DevScript provides descriptive error messages for common issues:
- **Syntax Errors**: Incorrect use of keywords or missing symbols.
- **Runtime Errors**: Type mismatches (e.g., adding a string to a number) or array length mismatches.

Example of an error:
`Runtime Error: Arrays must have the same length for addition`
