"""Direct tests for the run_cli/read_tasks helpers defined in tests/test_cli.py.

Those helpers are otherwise only exercised indirectly, as a side effect of the
CLI behavior tests in test_cli.py. These tests check the helpers themselves.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS_DIR)

from test_cli import read_tasks, run_cli


class TestReadTasks(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cwd = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_no_file_returns_empty_list(self):
        self.assertEqual(read_tasks(self.cwd), [])

    def test_reads_existing_file_with_known_content(self):
        tasks = [
            {"id": 1, "text": "buy milk", "done": False},
            {"id": 2, "text": "walk the dog", "done": True},
        ]
        path = os.path.join(self.cwd, "tasks.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tasks, f)

        self.assertEqual(read_tasks(self.cwd), tasks)

    def test_reads_empty_list_file(self):
        path = os.path.join(self.cwd, "tasks.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

        self.assertEqual(read_tasks(self.cwd), [])


class TestRunCli(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cwd = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_returns_completed_process_with_expected_attrs(self):
        r = run_cli([], self.cwd)
        self.assertIsInstance(r, subprocess.CompletedProcess)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Usage:", r.stdout)
        self.assertIsInstance(r.stderr, str)

    def test_respects_cwd_argument(self):
        other_dir = tempfile.TemporaryDirectory()
        try:
            run_cli(["add", "buy milk"], self.cwd)

            self.assertEqual(
                read_tasks(self.cwd), [{"id": 1, "text": "buy milk", "done": False}]
            )
            self.assertEqual(read_tasks(other_dir.name), [])
            self.assertFalse(os.path.exists(os.path.join(other_dir.name, "tasks.json")))
        finally:
            other_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
