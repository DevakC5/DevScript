# DevScript Syntax Guide

This document provides a detailed overview of the syntax and language constructs used in DevScript.

## 1. Variable Declarations
Variables are declared using the `let` keyword. DevScript is dynamically typed.

```devscript
let x = 10
let name = "Hello DevScript"
let my_array = array([1, 2, 3])
```

## 2. Data Types
- **Numbers**: Integers and floating-point numbers (e.g., `10`, `3.14`).
- **Strings**: Text enclosed in double quotes (e.g., `"Hello"`).
- **Arrays**: Specialized objects created using the `array()` function, containing numbers.
- **Booleans**: Implicitly handled via comparison operations in control flow.

## 3. Operators
### Arithmetic Operators
- `+`: Addition (Numbers or element-wise Array addition)
- `-`: Subtraction (Numbers)
- `*`: Multiplication (Numbers, scalar-array, or element-wise Array multiplication)
- `/`: Division (Numbers)

### Comparison Operators
- `>` : Greater than
- `<` : Less than
- `==`: Equal to
- `>=`: Greater than or equal to
- `<=`: Less than or equal to

## 4. Control Flow
DevScript uses an intuitive `if-else` structure.

### If-Else Statement
The `if` condition is followed by `->` and the block of code to execute. The block is terminated by `end`.

```devscript
if x > 5 ->
  say "x is large"
else ->
  say "x is small"
end
```

## 5. Built-in Functions
### Output
- `say <expression>`: Prints the result of the expression to the console.

### Array Creation
- `array([val1, val2, ...])`: Creates a DevArray object.

## 6. Comments
(Currently, DevScript does not support formal comments, but whitespace is ignored.)
