import unittest
from devlang.parser import parse

class TestParser(unittest.TestCase):
    def test_say(self):
        ast = parse(["say hello"], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "SayNode")
        self.assertEqual(ast[0].line, 1)

    def test_let(self):
        ast = parse(["let x = 10"], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "LetNode")
        self.assertEqual(ast[0].name, "x")
        self.assertEqual(ast[0].line, 1)

    def test_if(self):
        ast = parse(["if x > 5 ->", '    say "big"', "end"], [1, 2, 3])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "IfNode")
        self.assertEqual(len(ast[0].body), 1)

    def test_if_else(self):
        src = ["if x > 5 ->", '    say "big"', "else", '    say "small"', "end"]
        ast = parse(src, list(range(1, len(src) + 1)))
        self.assertEqual(ast[0].__class__.__name__, "IfNode")
        self.assertEqual(len(ast[0].body), 1)
        self.assertEqual(len(ast[0].else_body), 1)

    def test_if_elif_else(self):
        src = ["if x > 10 ->", '    say "big"', "elif x > 5 ->", '    say "medium"', "else", '    say "small"', "end"]
        ast = parse(src, list(range(1, len(src) + 1)))
        self.assertEqual(ast[0].__class__.__name__, "IfNode")
        # elif should create a nested if in else_body
        self.assertIsNotNone(ast[0].else_body)
        self.assertEqual(len(ast[0].else_body), 1)
        self.assertEqual(ast[0].else_body[0].__class__.__name__, "IfNode")

    def test_if_inline(self):
        ast = parse(['if x == 0 -> say "zero" end'], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "IfNode")

    def test_repeat(self):
        ast = parse(["repeat 5 ->", '    say "hi"', "end"], [1, 2, 3])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "RepeatNode")

    def test_while(self):
        ast = parse(["while i < 5 ->", "    let i = i + 1", "end"], [1, 2, 3])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "WhileNode")

    def test_for(self):
        ast = parse(["for i in range(5) ->", '    say i', "end"], [1, 2, 3])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "ForNode")
        self.assertEqual(ast[0].var_name, "i")

    def test_def(self):
        ast = parse(["def greet(name) ->", '    say "hi"', "end"], [1, 2, 3])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "FuncDefNode")
        self.assertEqual(ast[0].name, "greet")
        self.assertEqual(ast[0].params, ["name"])

    def test_return(self):
        ast = parse(["return x + 1"], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "ReturnNode")

    def test_break_continue(self):
        ast = parse(["break", "continue"], [1, 2])
        self.assertEqual(len(ast), 2)
        self.assertEqual(ast[0].__class__.__name__, "BreakNode")
        self.assertEqual(ast[1].__class__.__name__, "ContinueNode")

    def test_import(self):
        ast = parse(['import "math"'], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "ImportNode")

    def test_call(self):
        ast = parse(["greet(name)"], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "CallNode")
        self.assertEqual(ast[0].name, "greet")

    def test_input(self):
        ast = parse(['input name -> "Enter: "'], [1])
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].__class__.__name__, "InputNode")
        self.assertEqual(ast[0].name, "name")

    def test_multiple_statements(self):
        src = ["let x = 1", "let y = 2", 'say "done"']
        ast = parse(src, [1, 2, 3])
        self.assertEqual(len(ast), 3)

    def test_comments(self):
        ast = parse(["# comment", "let x = 1", "# another"], [1, 2, 3])
        self.assertEqual(len(ast), 1)

    def test_empty_lines(self):
        ast = parse(["", "let x = 1", "", ""], [1, 2, 3, 4])
        self.assertEqual(len(ast), 1)

if __name__ == '__main__':
    unittest.main()
