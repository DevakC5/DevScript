import unittest
import tempfile
import os
from devlang.cache import load, save

class TestCache(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.filepath = os.path.join(self.tmpdir, "test.dev")

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_save_and_load(self):
        source = "let x = 1"
        ast = ["dummy_ast"]
        save(self.filepath, source, ast)
        loaded = load(self.filepath, source)
        self.assertEqual(loaded, ast)

    def test_load_missing_file(self):
        result = load(self.filepath, "source")
        self.assertIsNone(result)

    def test_load_invalidated_by_source_change(self):
        source1 = "let x = 1"
        source2 = "let x = 2"
        ast = ["dummy_ast"]
        save(self.filepath, source1, ast)
        loaded = load(self.filepath, source2)
        self.assertIsNone(loaded)

    def test_load_cache_corrupt(self):
        cache_path = self.filepath + "c"
        with open(cache_path, 'wb') as f:
            f.write(b"not pickle data")
        loaded = load(self.filepath, "source")
        self.assertIsNone(loaded)

    def test_cache_path(self):
        save(self.filepath, "source", [])
        cache_path = self.filepath + "c"
        self.assertTrue(os.path.exists(cache_path))

if __name__ == '__main__':
    unittest.main()
