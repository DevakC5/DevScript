import unittest
from devlang.lexer import tokenise, strip_inline_comment, cast

class TestLexer(unittest.TestCase):
    def test_tokenise_basic(self):
        self.assertEqual(tokenise("say hello"), ["say", "hello"])
        self.assertEqual(tokenise("let x = 10"), ["let", "x", "=", "10"])
        self.assertEqual(tokenise('say "hello world"'), ["say", '"hello world"'])

    def test_tokenise_empty(self):
        self.assertEqual(tokenise(""), [])
        self.assertEqual(tokenise("   "), [])

    def test_tokenise_quoted_strings(self):
        self.assertEqual(tokenise("say 'hello'"), ["say", "'hello'"])
        self.assertEqual(tokenise('say "a b"'), ["say", '"a b"'])

    def test_strip_inline_comment(self):
        self.assertEqual(strip_inline_comment("let x = 5 # comment"), "let x = 5 ")
        self.assertEqual(strip_inline_comment("# full comment"), "")
        self.assertEqual(strip_inline_comment('say "hello # not comment"'), 'say "hello # not comment"')
        self.assertEqual(strip_inline_comment("say 'x # y'"), "say 'x # y'")

    def test_strip_inline_comment_no_hash(self):
        self.assertEqual(strip_inline_comment("let x = 5"), "let x = 5")

    def test_cast_int(self):
        self.assertEqual(cast("42"), 42)
        self.assertEqual(cast("-10"), -10)

    def test_cast_float(self):
        self.assertEqual(cast("3.14"), 3.14)
        self.assertEqual(cast("-2.5"), -2.5)

    def test_cast_string(self):
        self.assertEqual(cast("hello"), "hello")
        self.assertEqual(cast("42abc"), "42abc")

if __name__ == '__main__':
    unittest.main()
