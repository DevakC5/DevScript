# DevLang Syntax Reference  `v3.0`

---

## 1. Print
```
say "Hello"
say x
say x + 5
say "Hi " + name
```

## 2. Variables
```
let x = 10
let name = "Atharva"
let pi = 3.14
let result = x * 2 + 1
```

## 3. Arithmetic
| Op  | Meaning   |   | Op   | Meaning |
|-----|-----------|---|------|---------|
| `+` | Add/Concat|   | `%`  | Modulo  |
| `-` | Subtract  |   | `**` | Power   |
| `*` | Multiply  |   | `/`  | Divide  |

## 4. Comparisons
`>` `<` `>=` `<=` `==` `!=`

## 5. Logic Operators
```
if x > 5 and x < 20 ->  ...  end
if x == 0 or y == 0 ->  ...  end
if not x == 5       ->  ...  end
```

## 6. If / Else
```
if x > 5 ->
    say "big"
else
    say "small"
end

# Inline (no else)
if x == 0 -> say "zero" end
```

## 7. Repeat Loop
```
repeat 5 ->
    say "hi"
end

repeat n -> say "hi" end   # variable count
```

## 8. While Loop
```
let i = 0
while i < 5 ->
    say i
    let i = i + 1
end
```
> ⚠️ Safety cap: 100,000 iterations max to prevent infinite loops.

## 9. Functions
```
def greet(name) ->
    say "Hello, " + name
end

def add(a, b) ->
    return a + b
end

greet("Atharva")          # call (no return value used)
let r = add(3, 4)         # call (capture return value)
say r
```

## 10. Input
```
input name -> "Enter name: "
input age  -> "Enter age: "
```
> Numbers are auto-cast. Anything else stays a string.

## 11. String Methods
```
name.len()                  # length
name.upper()                # UPPERCASE
name.lower()                # lowercase
name.trim()                 # strip whitespace
name.contains("hi")         # true / false
name.replace("a", "b")      # replace all
```
> Methods can be chained: `name.trim().upper()`

## 12. Comments
```
# Full line comment
let x = 5   # Inline comment
```

## 13. Boolean Literals
```
let flag = true
let done = false
```

---

## Rules & Gotchas
- Every `if`, `repeat`, `while`, `def` block **must** end with `end`
- `else` goes on its own line between `end`-less `if` body and `end`
- Variable names: letters/digits/underscores, must start with a letter
- Strings: `"double"` or `'single'` quotes
- `return` only works inside a `def` block
