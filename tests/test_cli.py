"""Process-level tests for main.py's argv dispatch logic.

Drives the CLI as a subprocess (python main.py ...) in an isolated temp
directory per test, and asserts on both stdout and the resulting tasks.json.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PY = os.path.join(REPO_ROOT, "main.py")


def run_cli(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, MAIN_PY] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def read_tasks(cwd: str) -> list[dict]:
    path = os.path.join(cwd, "tasks.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cwd = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_add_and_list(self):
        r1 = run_cli(["add", "buy milk"], self.cwd)
        self.assertEqual(r1.returncode, 0)
        self.assertIn("Added task 1: buy milk", r1.stdout)

        tasks = read_tasks(self.cwd)
        self.assertEqual(tasks, [{"id": 1, "text": "buy milk", "done": False}])

        r2 = run_cli(["add", "walk the dog"], self.cwd)
        self.assertIn("Added task 2: walk the dog", r2.stdout)

        r3 = run_cli(["list"], self.cwd)
        self.assertEqual(r3.returncode, 0)
        self.assertIn("[ ] 1: buy milk", r3.stdout)
        self.assertIn("[ ] 2: walk the dog", r3.stdout)

    def test_add_missing_text(self):
        r = run_cli(["add"], self.cwd)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error: please provide task text.", r.stdout)
        self.assertEqual(read_tasks(self.cwd), [])

    def test_list_empty(self):
        r = run_cli(["list"], self.cwd)
        self.assertEqual(r.returncode, 0)
        self.assertIn("No tasks yet.", r.stdout)

    def test_done(self):
        run_cli(["add", "buy milk"], self.cwd)
        r = run_cli(["done", "1"], self.cwd)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Marked task 1 as done.", r.stdout)
        self.assertTrue(read_tasks(self.cwd)[0]["done"])

    def test_done_not_found(self):
        run_cli(["add", "buy milk"], self.cwd)
        r = run_cli(["done", "99"], self.cwd)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Task 99 not found.", r.stdout)
        self.assertFalse(read_tasks(self.cwd)[0]["done"])

    def test_done_missing_id(self):
        r = run_cli(["done"], self.cwd)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Error: please provide a task id.", r.stdout)

    def test_update(self):
        run_cli(["add", "buy milk"], self.cwd)
        r = run_cli(["update", "1", "buy oat milk"], self.cwd)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Updated task 1: buy oat milk", r.stdout)
        self.assertEqual(read_tasks(self.cwd)[0]["text"], "buy oat milk")

    def test_update_not_found(self):
        run_cli(["add", "buy milk"], self.cwd)
        r = run_cli(["update", "99", "nope"], self.cwd)
        self.assertIn("Task 99 not found.", r.stdout)
        self.assertEqual(read_tasks(self.cwd)[0]["text"], "buy milk")

    def test_update_missing_args(self):
        r1 = run_cli(["update"], self.cwd)
        self.assertEqual(r1.returncode, 1)
        self.assertIn("Error: please provide a task id and new text.", r1.stdout)

        r2 = run_cli(["update", "1"], self.cwd)
        self.assertEqual(r2.returncode, 1)
        self.assertIn("Error: please provide a task id and new text.", r2.stdout)

    def test_unknown_command(self):
        r = run_cli(["bogus"], self.cwd)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Usage:", r.stdout)

    def test_no_args(self):
        r = run_cli([], self.cwd)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Usage:", r.stdout)


if __name__ == "__main__":
    unittest.main()
