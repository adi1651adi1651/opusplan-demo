import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import Task, load_tasks, next_id, save_tasks


class TestNextId(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(next_id([]), 1)

    def test_contiguous(self):
        tasks = [Task(1, "a", False), Task(2, "b", False), Task(3, "c", False)]
        self.assertEqual(next_id(tasks), 4)

    def test_non_contiguous(self):
        tasks = [Task(1, "a", False), Task(5, "b", False), Task(3, "c", False)]
        self.assertEqual(next_id(tasks), 6)

    def test_single(self):
        self.assertEqual(next_id([Task(7, "a", False)]), 8)

    def test_gap_no_fill(self):
        tasks = [Task(2, "a", False), Task(4, "b", False)]
        self.assertEqual(next_id(tasks), 5)


class TestLoadSaveTasks(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp_dir.name, "test_tasks.json")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_roundtrip(self):
        original = [
            Task(1, "buy milk", False),
            Task(2, "say \"hi\"\nbye\tthere", True),
            Task(3, "walk the dog", False),
        ]
        save_tasks(self.path, original)
        self.assertEqual(load_tasks(self.path), original)

    def test_empty_roundtrip(self):
        save_tasks(self.path, [])
        self.assertEqual(load_tasks(self.path), [])

    def test_nonexistent_path_returns_empty(self):
        missing = os.path.join(self.tmp_dir.name, "does_not_exist_12345.json")
        self.assertEqual(load_tasks(missing), [])


if __name__ == "__main__":
    unittest.main()
