# DevScript Standard Library

DevScript comes with a set of built-in libraries to handle mathematical operations and array manipulations.

## 1. Array Library (`arraylib`)
Arrays in DevScript are powered by the `DevArray` class, allowing for vector-like operations.

### Functions
- `array([list])`: Creates a new array from a list of numbers.
- `sum(arr)`: Returns the sum of all elements in the array.
- `mean(arr)`: Returns the arithmetic mean of the elements.

### Array Operators
| Operator | Description | Example | Result |
|-----------|-------------|---------|---------|
| `+` | Element-wise addition | `array([1, 2]) + array([3, 4])` | `array([4, 6])` |
| `*` (Scalar) | Multiplies every element by a number | `array([1, 2]) * 3` | `array([3, 6])` |
| `*` (Array) | Element-wise multiplication | `array([1, 2]) * array([3, 4])` | `array([3, 8])` |

## 2. Math Library (`mathlib`)
The math library provides standard scientific functions.

### Functions
- `sqrt(x)`: Returns the square root of `x`.
- `pow(x, y)`: Returns `x` raised to the power of `y`.
- `sin(x)`: Returns the sine of `x` (in radians).
- `cos(x)`: Returns the cosine of `x` (in radians).

## 3. Core Built-ins
- `say <value>`: The primary function for printing output to the console.
