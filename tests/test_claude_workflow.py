"""Structural validation for .github/workflows/claude.yml.

Parses the workflow with PyYAML and asserts its shape hasn't drifted:
the trigger events, the @claude-mention gate on the `claude` job, the
permissions block, and the checkout + claude-code-action steps.

Requires PyYAML (`pip install pyyaml`). If it isn't installed, all
tests in this module are skipped (rather than failing) so the rest of
the suite still runs cleanly.
"""

import os
import unittest

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_PATH = os.path.join(REPO_ROOT, ".github", "workflows", "claude.yml")

# PyYAML follows the YAML 1.1 spec, where an unquoted `on` key is parsed
# as the boolean True rather than the string "on" (the classic GitHub
# Actions "on: true" gotcha). Look it up either way so this test doesn't
# depend on that quirk.
_ON_KEYS = ("on", True)


def _get_on(workflow: dict):
    for key in _ON_KEYS:
        if key in workflow:
            return workflow[key]
    raise KeyError("no 'on' trigger key found (checked 'on' and True)")


@unittest.skipUnless(HAS_YAML, "PyYAML is not installed (pip install pyyaml)")
class TestClaudeWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.raw = f.read()
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.workflow = yaml.safe_load(f)

    def test_file_exists_and_parses_to_a_mapping(self):
        self.assertTrue(os.path.exists(WORKFLOW_PATH))
        self.assertIsInstance(self.workflow, dict)

    def test_has_name(self):
        self.assertIn("name", self.workflow)
        self.assertTrue(self.workflow["name"])

    def test_triggers(self):
        on = _get_on(self.workflow)
        self.assertIsInstance(on, dict)

        self.assertIn("issue_comment", on)
        self.assertEqual(on["issue_comment"].get("types"), ["created"])

        self.assertIn("pull_request_review_comment", on)
        self.assertEqual(on["pull_request_review_comment"].get("types"), ["created"])

        self.assertIn("issues", on)
        self.assertEqual(on["issues"].get("types"), ["opened", "assigned"])

        self.assertIn("pull_request_review", on)
        self.assertEqual(on["pull_request_review"].get("types"), ["submitted"])

    def test_has_claude_job(self):
        self.assertIn("jobs", self.workflow)
        self.assertIn("claude", self.workflow["jobs"])

    def test_claude_job_runs_on_ubuntu(self):
        job = self.workflow["jobs"]["claude"]
        self.assertEqual(job.get("runs-on"), "ubuntu-latest")

    def test_claude_job_if_gates_on_claude_mention(self):
        job = self.workflow["jobs"]["claude"]
        self.assertIn("if", job)
        condition = job["if"]
        self.assertIsInstance(condition, str)

        # Every trigger event's mention source is checked for '@claude'.
        self.assertIn("@claude", condition)
        expected_fragments = [
            "github.event_name == 'issue_comment'",
            "github.event.comment.body",
            "github.event_name == 'pull_request_review_comment'",
            "github.event_name == 'pull_request_review'",
            "github.event.review.body",
            "github.event_name == 'issues'",
            "github.event.issue.body",
            "github.event.issue.title",
        ]
        for fragment in expected_fragments:
            self.assertIn(
                fragment, condition, f"expected {fragment!r} in job `if` condition"
            )

    def test_claude_job_permissions(self):
        job = self.workflow["jobs"]["claude"]
        self.assertEqual(
            job.get("permissions"),
            {
                "contents": "read",
                "pull-requests": "read",
                "issues": "read",
                "id-token": "write",
            },
        )

    def test_steps_checkout_then_claude_code_action(self):
        job = self.workflow["jobs"]["claude"]
        steps = job.get("steps")
        self.assertIsInstance(steps, list)
        self.assertEqual(len(steps), 2)

        checkout, claude_step = steps

        self.assertEqual(checkout.get("uses"), "actions/checkout@v4")

        self.assertEqual(claude_step.get("uses"), "anthropics/claude-code-action@v1")
        self.assertEqual(
            claude_step.get("with", {}).get("anthropic_api_key"),
            "${{ secrets.ANTHROPIC_API_KEY }}",
        )

    def test_no_leftover_tab_characters(self):
        # YAML disallows tabs for indentation; guard against accidental
        # tab/space mixing creeping back in via an editor.
        self.assertNotIn("\t", self.raw)


if __name__ == "__main__":
    unittest.main()
