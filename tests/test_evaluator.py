import unittest
from devlang.evaluator import evaluate, clear_cache, _compile_expr, BUILTINS, val_to_str, split_args

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_literal_int(self):
        self.assertEqual(evaluate("42", {}, 1, {}), 42)
        self.assertEqual(evaluate("-5", {}, 1, {}), -5)

    def test_literal_float(self):
        self.assertEqual(evaluate("3.14", {}, 1, {}), 3.14)

    def test_literal_string(self):
        self.assertEqual(evaluate('"hello"', {}, 1, {}), "hello")
        self.assertEqual(evaluate("'world'", {}, 1, {}), "world")

    def test_literal_bool(self):
        self.assertEqual(evaluate("true", {}, 1, {}), True)
        self.assertEqual(evaluate("false", {}, 1, {}), False)

    def test_variable_lookup(self):
        self.assertEqual(evaluate("x", {"x": 10}, 1, {}), 10)

    def test_addition(self):
        self.assertEqual(evaluate("2 + 3", {}, 1, {}), 5)

    def test_subtraction(self):
        self.assertEqual(evaluate("10 - 3", {}, 1, {}), 7)

    def test_multiplication(self):
        self.assertEqual(evaluate("4 * 5", {}, 1, {}), 20)

    def test_division(self):
        self.assertEqual(evaluate("10 / 3", {}, 1, {}), 10 / 3)
        self.assertEqual(evaluate("5 / 0", {}, 1, {}), 0)

    def test_modulo(self):
        self.assertEqual(evaluate("10 % 3", {}, 1, {}), 1)

    def test_power(self):
        self.assertEqual(evaluate("2 ** 3", {}, 1, {}), 8)

    def test_comparisons(self):
        self.assertEqual(evaluate("5 > 3", {}, 1, {}), True)
        self.assertEqual(evaluate("5 < 3", {}, 1, {}), False)
        self.assertEqual(evaluate("5 == 5", {}, 1, {}), True)
        self.assertEqual(evaluate("5 != 5", {}, 1, {}), False)
        self.assertEqual(evaluate("5 >= 5", {}, 1, {}), True)
        self.assertEqual(evaluate("5 <= 4", {}, 1, {}), False)

    def test_logic_and(self):
        self.assertEqual(evaluate("true and true", {}, 1, {}), True)
        self.assertEqual(evaluate("true and false", {}, 1, {}), False)

    def test_logic_or(self):
        self.assertEqual(evaluate("true or false", {}, 1, {}), True)
        self.assertEqual(evaluate("false or false", {}, 1, {}), False)

    def test_logic_not(self):
        self.assertEqual(evaluate("not true", {}, 1, {}), False)
        self.assertEqual(evaluate("not false", {}, 1, {}), True)

    def test_string_concat(self):
        self.assertEqual(evaluate('"hello" + " world"', {}, 1, {}), "hello world")

    def test_list_literal(self):
        self.assertEqual(evaluate("[1, 2, 3]", {}, 1, {}), [1, 2, 3])
        self.assertEqual(evaluate("[]", {}, 1, {}), [])

    def test_list_indexing(self):
        self.assertEqual(evaluate("[10, 20, 30][1]", {}, 1, {}), 20)

    def test_list_slicing(self):
        self.assertEqual(evaluate("[1, 2, 3, 4, 5][1:3]", {}, 1, {}), [2, 3])
        self.assertEqual(evaluate("[1, 2, 3, 4, 5][:3]", {}, 1, {}), [1, 2, 3])

    def test_string_indexing(self):
        self.assertEqual(evaluate('"hello"[0]', {}, 1, {}), "h")
        self.assertEqual(evaluate('"hello"[4]', {}, 1, {}), "o")

    def test_string_slicing(self):
        self.assertEqual(evaluate('"hello"[1:4]', {}, 1, {}), "ell")
        self.assertEqual(evaluate('"hello"[:3]', {}, 1, {}), "hel")

    def test_builtin_range(self):
        self.assertEqual(evaluate("range(5)", {}, 1, {}), [0, 1, 2, 3, 4])
        self.assertEqual(evaluate("range(2, 5)", {}, 1, {}), [2, 3, 4])

    def test_builtin_zeros(self):
        self.assertEqual(evaluate("zeros(3)", {}, 1, {}), [0, 0, 0])

    def test_builtin_ones(self):
        self.assertEqual(evaluate("ones(3)", {}, 1, {}), [1, 1, 1])

    def test_builtin_sum_mean(self):
        self.assertEqual(evaluate("sum([1, 2, 3])", {}, 1, {}), 6)
        self.assertEqual(evaluate("mean([1, 2, 3])", {}, 1, {}), 2.0)

    def test_builtin_min_max(self):
        self.assertEqual(evaluate("min([3, 1, 2])", {}, 1, {}), 1)
        self.assertEqual(evaluate("max([3, 1, 2])", {}, 1, {}), 3)

    def test_builtin_abs(self):
        self.assertEqual(evaluate("abs(-5)", {}, 1, {}), 5)

    def test_builtin_sqrt(self):
        self.assertEqual(evaluate("sqrt(9)", {}, 1, {}), 3.0)

    def test_builtin_sin_cos(self):
        import math
        self.assertAlmostEqual(evaluate("sin(0)", {}, 1, {}), 0.0)
        self.assertAlmostEqual(evaluate("cos(0)", {}, 1, {}), 1.0)

    def test_builtin_floor_ceil_round(self):
        self.assertEqual(evaluate("floor(3.7)", {}, 1, {}), 3)
        self.assertEqual(evaluate("ceil(3.2)", {}, 1, {}), 4)
        self.assertEqual(evaluate("round(3.5)", {}, 1, {}), 4)

    def test_builtin_rand(self):
        r = evaluate("rand()", {}, 1, {})
        self.assertGreaterEqual(r, 0)
        self.assertLess(r, 1)

    def test_builtin_randint(self):
        r = evaluate("randint(1, 10)", {}, 1, {})
        self.assertGreaterEqual(r, 1)
        self.assertLessEqual(r, 10)

    def test_builtin_arange(self):
        self.assertEqual(evaluate("arange(5)", {}, 1, {}), [0, 1, 2, 3, 4])

    def test_builtin_file_read_write(self):
        result = evaluate('file_write("test_tmp.txt", "hello")', {}, 1, {})
        self.assertEqual(result, True)
        result2 = evaluate('file_read("test_tmp.txt")', {}, 1, {})
        self.assertEqual(result2, "hello")
        import os
        os.remove("test_tmp.txt")

    def test_builtin_file_read_missing(self):
        result = evaluate('file_read("nonexistent_file_12345.txt")', {}, 1, {})
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("[Error"))

    def test_string_method_len(self):
        self.assertEqual(evaluate('"hello".len()', {}, 1, {}), 5)

    def test_string_method_upper(self):
        self.assertEqual(evaluate('"hello".upper()', {}, 1, {}), "HELLO")

    def test_string_method_lower(self):
        self.assertEqual(evaluate('"HELLO".lower()', {}, 1, {}), "hello")

    def test_string_method_trim(self):
        self.assertEqual(evaluate('"  hi  ".trim()', {}, 1, {}), "hi")

    def test_string_method_contains(self):
        self.assertEqual(evaluate('"hello world".contains("world")', {}, 1, {}), True)
        self.assertEqual(evaluate('"hello world".contains("xyz")', {}, 1, {}), False)

    def test_string_method_replace(self):
        self.assertEqual(evaluate('"a b a".replace("a", "c")', {}, 1, {}), "c b c")

    def test_list_method_len(self):
        self.assertEqual(evaluate("[1, 2, 3].len()", {}, 1, {}), 3)

    def test_list_method_sum(self):
        self.assertEqual(evaluate("[1, 2, 3].sum()", {}, 1, {}), 6)

    def test_list_method_mean(self):
        self.assertEqual(evaluate("[1, 2, 3].mean()", {}, 1, {}), 2.0)

    def test_list_method_min_max(self):
        self.assertEqual(evaluate("[3, 1, 2].min()", {}, 1, {}), 1)
        self.assertEqual(evaluate("[3, 1, 2].max()", {}, 1, {}), 3)

    def test_list_method_append(self):
        self.assertEqual(evaluate("x", {"x": [1, 2]}, 1, {}), [1, 2])
        # append side-effect: compile a call that appends and returns the modified list
        fn = _compile_expr("x.append(3)")
        result = fn({"x": [1, 2]}, 1, {})
        self.assertEqual(result, [1, 2, 3])



    def test_list_method_pop(self):
        result = evaluate("[1, 2, 3].pop()", {}, 1, {})
        self.assertEqual(result, 3)

    def test_list_method_sort(self):
        result = evaluate("[3, 1, 2].sort()", {}, 1, {})
        self.assertEqual(result, [1, 2, 3])

    def test_dict_literal(self):
        d = evaluate('{"a": 1, "b": 2}', {}, 1, {})
        self.assertEqual(d, {"a": 1, "b": 2})

    def test_dict_empty(self):
        d = evaluate("{}", {}, 1, {})
        self.assertEqual(d, {})

    def test_nested_expr(self):
        self.assertEqual(evaluate("(2 + 3) * 4", {}, 1, {}), 20)
        self.assertEqual(evaluate("2 + 3 * 4", {}, 1, {}), 14)

    def test_precedence(self):
        self.assertEqual(evaluate("2 + 3 * 4", {}, 1, {}), 14)
        self.assertEqual(evaluate("2 * 3 + 4", {}, 1, {}), 10)
        self.assertEqual(evaluate("2 ** 3 * 4", {}, 1, {}), 32)

    def test_val_to_str(self):
        self.assertEqual(val_to_str(True), "true")
        self.assertEqual(val_to_str(False), "false")
        self.assertEqual(val_to_str(42), "42")
        self.assertEqual(val_to_str("hello"), "hello")
        self.assertEqual(val_to_str([1, 2, 3]), "[1, 2, 3]")
        self.assertEqual(val_to_str([True, False]), "[true, false]")

    def test_split_args(self):
        self.assertEqual(split_args("1, 2, 3"), ["1", " 2", " 3"])
        self.assertEqual(split_args('"a, b", 2'), ['"a, b"', ' 2'])
        self.assertEqual(split_args("f(1, 2), 3"), ["f(1, 2)", " 3"])

if __name__ == '__main__':
    unittest.main()
