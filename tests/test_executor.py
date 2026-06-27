import unittest
from devlang.executor import run_block
from devlang.parser import parse

class TestExecutor(unittest.TestCase):
    def _run(self, src_lines):
        ast = parse(src_lines, list(range(1, len(src_lines) + 1)))
        variables = {}
        functions = {}
        run_block(ast, variables, functions)
        return variables, functions

    def test_let(self):
        v, _ = self._run(["let x = 42"])
        self.assertEqual(v["x"], 42)

    def test_let_expr(self):
        v, _ = self._run(["let x = 2 + 3"])
        self.assertEqual(v["x"], 5)

    def test_repeat(self):
        v, _ = self._run(["let x = 0", "repeat 5 ->", "    let x = x + 1", "end"])
        self.assertEqual(v["x"], 5)

    def test_while(self):
        v, _ = self._run(["let i = 0", "while i < 3 ->", "    let i = i + 1", "end"])
        self.assertEqual(v["i"], 3)

    def test_for_range(self):
        v, _ = self._run(["let s = 0", "for i in range(4) ->", "    let s = s + i", "end"])
        self.assertEqual(v["s"], 6)

    def test_for_numeric(self):
        v, _ = self._run(["let s = 0", "for i in 4 ->", "    let s = s + i", "end"])
        self.assertEqual(v["s"], 6)

    def test_for_list(self):
        v, _ = self._run(["let s = 0", "for i in [1, 2, 3] ->", "    let s = s + i", "end"])
        self.assertEqual(v["s"], 6)

    def test_if_true(self):
        v, _ = self._run(["let x = 0", "if true ->", "    let x = 1", "end"])
        self.assertEqual(v["x"], 1)

    def test_if_false(self):
        v, _ = self._run(["let x = 1", "if false ->", "    let x = 2", "end"])
        self.assertEqual(v["x"], 1)

    def test_if_else(self):
        v, _ = self._run(["let x = 0", "if false ->", "    let x = 1", "else", "    let x = 2", "end"])
        self.assertEqual(v["x"], 2)

    def test_if_elif(self):
        v, _ = self._run(["let x = 7", "let r = ''", "if x > 10 ->", '    let r = "big"', "elif x > 5 ->", '    let r = "medium"', "else", '    let r = "small"', "end"])
        self.assertEqual(v["r"], "medium")

    def test_if_elif_else(self):
        v, _ = self._run(["let x = 2", "let r = ''", "if x > 10 ->", '    let r = "big"', "elif x > 5 ->", '    let r = "medium"', "else", '    let r = "small"', "end"])
        self.assertEqual(v["r"], "small")

    def test_break_in_while(self):
        v, _ = self._run(["let i = 0", "while true ->", "    let i = i + 1", "    if i == 3 ->", "        break", "    end", "end"])
        self.assertEqual(v["i"], 3)

    def test_continue_in_while(self):
        v, _ = self._run(["let s = 0", "let i = 0", "while i < 5 ->", "    let i = i + 1", "    if i == 3 ->", "        continue", "    end", "    let s = s + 1", "end"])
        # continue skips s = s + 1 when i == 3, so s should be 4
        self.assertEqual(v["s"], 4)

    def test_break_in_for(self):
        v, _ = self._run(["let s = 0", "for i in range(10) ->", "    if i == 3 ->", "        break", "    end", "    let s = s + i", "end"])
        self.assertEqual(v["s"], 0 + 1 + 2)

    def test_continue_in_repeat(self):
        v, _ = self._run(["let s = ''", "repeat 5 ->", "    let i = 1", "    if i == 1 ->", "        let s = s + 'a'", "        continue", "    end", "    let s = s + 'b'", "end"])
        # continue skips 'b' every iteration, so only 'a' 5 times
        self.assertEqual(v["s"], "aaaaa")

    def test_nested_loops_with_break(self):
        v, _ = self._run([
            "let r = ''",
            "let x = 1",
            "for i in range(3) ->",
            "    for j in range(3) ->",
            "        if j == 1 ->",
            "            break",
            "        end",
            "        let r = r + x",
            "    end",
            "end"
        ])
        # Each i iteration: only j=0 runs before break, so r = "1" + "1" + "1"
        self.assertEqual(v["r"], "111")

    def test_def_and_call(self):
        v, _ = self._run([
            "def add(a, b) ->",
            "    return a + b",
            "end",
            "let r = add(3, 4)"
        ])
        self.assertEqual(v["r"], 7)

    def test_def_no_return(self):
        fns = {}
        src = ["def greet(name) ->", '    say "hi"', "end"]
        ast = parse(src, list(range(1, len(src) + 1)))
        run_block(ast, {}, fns)
        self.assertIn("greet", fns)
        self.assertEqual(fns["greet"]["params"], ["name"])

    def test_vectorized_add(self):
        v, _ = self._run(["let x = [1, 2] + [3, 4]"])
        self.assertEqual(v["x"], [4, 6])

    def test_vectorized_mul(self):
        v, _ = self._run(["let x = [1, 2] * 3"])
        self.assertEqual(v["x"], [3, 6])

if __name__ == '__main__':
    unittest.main()
