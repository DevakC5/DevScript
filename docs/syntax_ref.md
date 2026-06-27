# DevLang Syntax Reference  `v3.2`

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

Vectorized on lists: `[1,2,3] + [4,5,6]` → `[5,7,9]`

## 4. Comparisons
`>` `<` `>=` `<=` `==` `!=`

## 5. Logic
```
if x > 5 and x < 20 ->  ...  end
if x == 0 or y == 0 ->  ...  end
if not x == 5       ->  ...  end
```

## 6. If / Elif / Else
```
if x > 5 ->
    say "big"
elif x > 2 ->
    say "medium"
else
    say "small"
end

if x == 0 -> say "zero" end       # inline
```

## 7. Loops
```
repeat 5 -> say "hi" end          # fixed count
repeat n -> ... end               # variable count

while i < 5 ->
    let i = i + 1
end

for i in 5 ->                     # numeric, sugar for range(5)
    say i
end

for item in list ->                # iterate list
    say item
end
```
> ⚠️ `while` capped at 100,000 iterations.
> `break` / `continue` work in all loop types.

## 8. Functions
```
def greet(name) ->
    say "Hello, " + name
end

def add(a, b) ->
    return a + b
end

greet("Atharva")          # statement call
let r = add(3, 4)         # expression call
```
> `return` only works inside `def`.

## 9. Async / Await
```
async def fetch(n) ->
    say "starting..."
    wait(200)
    return n * 2
end

let coro = fetch(5)
let result = await coro
say result  # 10
```
> `async def` runs the body on a background thread.
> `await` blocks until the coroutine completes and returns its value.

## 10. Spawn (Threads)
```
spawn ->
    say "in a thread!"
end
thread_join(_last_spawn)
```
> `_last_spawn` holds the last spawned thread handle.

## 11. Input
```
input name -> "Enter name: "
input age as num -> "Enter age: "
input pass mask -> "Password: "
input val default "admin" -> "Username: "
```
> `as num` casts to int/float. `mask` hides input. `default` fallback when empty.

## 12. String Methods
```
name.len()
name.upper()
name.lower()
name.trim()
name.contains("hi")
name.replace("a", "b")
```
> Methods chain: `name.trim().upper()`

## 13. List Methods
```
lst.append(x)
lst.pop()
lst.sort()
lst.len()
lst.sum()
lst.mean()
lst.min()
lst.max()
```

## 14. String / List Slicing
```
x[start:stop:step]
```
Works on strings and lists. All parts optional.

## 15. Dict Literals
```
let d = {"name": "DevLang", "ver": 3.1}
say d["name"]
```

## 16. Structs
```
struct Person ->
    let name = ""
    let age = 0
end

let p = Person("Alice", 30)
say p.name
say p.age
```
> Fields with defaults are optional during construction.
> Defaults can be any expression.

## 17. Enums
```
enum Color -> Red, Green, Blue
say Red    # "Color.Red"
say Green  # "Color.Green"
```

## 18. Matrix
```
let m = matrix([[1,2],[3,4]])
say m              # formatted display
say m.shape        # (2, 2)
say m.T            # transpose
let d = m.dot(identity(3))

let z = zeros_matrix(2, 3)
let i = identity(4)
```
> Arithmetic: `+`, `-`, `*`, `/` with scalars or element-wise.
> `.T` property, `.dot()` method.

## 19. JSON / CSV
```
let d = json_loads('{"a": 1}')
say json_dumps(d)

let rows = csv_parse("a,b\n1,2")
csv_write("out.csv", rows)
let back = csv_read("out.csv")
```

## 20. Terminal UI
```
menu("Pick:", ["a","b"])        # returns selected
confirm("Sure?")                # true/false
password("Secret:")             # masked input

say_table(["Name","Score"], [["Alice",95],["Bob",87]])
say_panel("content", title="Hi")
say_tree("root", title="Tree")

progress_start("Loading", 100)
progress_tick(id)
progress_stop(id)
```

## 21. Live Display
```
live_start("Countdown")
let i = 5
while i > 0 ->
    live_set(str(i))
    wait(1000)
    let i = i - 1
end
live_set("Blastoff!")
wait(500)
live_stop()
```

## 22. Timers / Events
```
def tick() -> say "tick" end
set_timeout("tick", 300)      # one-shot
set_interval("tick", 1000)    # recurring
clear_timer(id)               # cancel
wait_all()                    # block until all timers done
key_wait("Press any key")     # single keypress
```

## 23. Built-in Functions
`time`, `sleep` / `wait`, `file_read`, `file_write`, `range`, `zeros`, `ones`, `arange`, `sum`, `mean`, `min`, `max`, `matmul`, `sqrt`, `sin`, `cos`, `tan`, `floor`, `ceil`, `round`, `abs`, `rand`, `randint`, `matrix`, `zeros_matrix`, `identity`, `thread_join`, `json_loads`, `json_dumps`, `json_read`, `csv_parse`, `csv_read`, `csv_write`, `menu`, `confirm`, `password`, `say_table`, `say_panel`, `say_tree`, `progress_start`, `progress_tick`, `progress_stop`, `live_start`, `live_set`, `live_stop`, `set_timeout`, `set_interval`, `clear_timer`, `wait_all`, `key_wait`, `cv_*` (stubs), `plot_*` (SVG charts).

## 24. Comments
```
# Full line comment
let x = 5   # Inline comment
```

## 25. Import
```
import "math"
import "file"
import "chart"
import "./my_script"
```
> Resolves: same dir → `libs/` → `scripts/`. `.dev` appended automatically.
> Circular imports detected and rejected.

## 26. CLI Commands
| Command | Description |
|---------|-------------|
| `dev run <file>` | Execute a `.dev` program |
| `dev repl` | Interactive REPL (multi-line with prompt_toolkit) |
| `dev watch <file>` | Auto-reload on file change |
| `dev check <file>` | Syntax check |
| `dev fmt <file>` | Format code |
| `dev install <url>` | Download a package to `libs/` |
| `dev lsp` | Start Language Server (stdio JSON-RPC) |
| `dev version` | Show version |
| `dev help` | Show help |

## 27. REPL Meta-Commands
| Command | Description |
|---------|-------------|
| `.exit` | Exit REPL |
| `.vars` | Show variables |
| `.help` | Show help |
| `.clear` | Clear variables and buffer |

---

## Rules & Gotchas
- Every block (`if`, `elif`, `else`, `while`, `for`, `repeat`, `def`, `async def`, `spawn`, `struct`, `enum`) must end with `end`
- `else` / `elif` on their own lines (not inline)
- Variable names: letters/digits/underscores, start with a letter
- Strings: `"double"` or `'single'` quotes
- `return` only works inside `def` / `async def`
- `while` loops capped at 100,000 iterations
- `.devc` cache files auto-rebuilt when source changes
