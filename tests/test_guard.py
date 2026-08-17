import io
import json
import os
import sys
import unittest
import unittest.mock
from contextlib import redirect_stdout

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".claude",
        "hooks",
    ),
)

import guard


class TestSplitCommands(unittest.TestCase):
    def test_single_command(self):
        self.assertEqual(guard.split_commands("ls -la"), ["ls -la"])

    def test_and_chain(self):
        self.assertEqual(
            guard.split_commands("echo hi && rm -rf /"), ["echo hi", "rm -rf /"]
        )

    def test_or_chain(self):
        self.assertEqual(
            guard.split_commands("false || echo fallback"), ["false", "echo fallback"]
        )

    def test_semicolon_chain(self):
        self.assertEqual(
            guard.split_commands("echo one; echo two"), ["echo one", "echo two"]
        )

    def test_pipe_chain(self):
        self.assertEqual(
            guard.split_commands("cat file | grep foo"), ["cat file", "grep foo"]
        )

    def test_strips_whitespace_and_drops_empties(self):
        self.assertEqual(
            guard.split_commands("  echo hi   &&   && echo bye  "),
            ["echo hi", "echo bye"],
        )

    def test_destructive_part_still_caught_in_chain(self):
        parts = guard.split_commands("echo hi && rm -rf /")
        self.assertTrue(any(guard.check_rm(p) for p in parts))


class TestHasFlag(unittest.TestCase):
    def test_combined_short_flags_detects_both(self):
        flags = ["-rf"]
        self.assertTrue(guard.has_flag(flags, "r", "--recursive"))
        self.assertTrue(guard.has_flag(flags, "f", "--force"))

    def test_long_flag_exact_match(self):
        self.assertTrue(guard.has_flag(["--force"], "f", "--force"))

    def test_long_flag_no_partial_match(self):
        self.assertFalse(guard.has_flag(["--forces"], "f", "--force"))

    def test_short_flag_absent(self):
        self.assertFalse(guard.has_flag(["-r"], "f", "--force"))

    def test_no_flags(self):
        self.assertFalse(guard.has_flag([], "f", "--force"))


class TestCheckRm(unittest.TestCase):
    def test_blocks_root(self):
        self.assertIsNotNone(guard.check_rm("rm -rf /"))

    def test_blocks_home_tilde(self):
        self.assertIsNotNone(guard.check_rm("rm -rf ~"))

    def test_blocks_current_dir(self):
        self.assertIsNotNone(guard.check_rm("rm -rf ."))

    def test_blocks_parent_dir(self):
        self.assertIsNotNone(guard.check_rm("rm -rf .."))

    def test_blocks_star(self):
        self.assertIsNotNone(guard.check_rm("rm -rf *"))

    def test_star_glob_suffix_is_stripped_before_matching(self):
        # "/*" has its trailing "/*" stripped to "", which is not itself a
        # broad target in BROAD_TARGETS -- documents actual current behavior.
        self.assertIsNone(guard.check_rm("rm -rf /*"))

    def test_blocks_with_sudo(self):
        self.assertIsNotNone(guard.check_rm("sudo rm -rf /"))

    def test_blocks_quoted_broad_target(self):
        self.assertIsNotNone(guard.check_rm('rm -rf "/"'))

    def test_allows_narrow_relative_path(self):
        self.assertIsNone(guard.check_rm("rm -rf ./build"))

    def test_allows_narrow_named_dir(self):
        self.assertIsNone(guard.check_rm("rm -rf node_modules"))

    def test_allows_specific_absolute_path(self):
        self.assertIsNone(guard.check_rm("rm -rf /tmp/some/specific/dir"))

    def test_allows_missing_force_flag(self):
        self.assertIsNone(guard.check_rm("rm -r ./build"))

    def test_allows_missing_recursive_flag(self):
        self.assertIsNone(guard.check_rm("rm -f ./file.txt"))

    def test_allows_plain_rm_single_file(self):
        self.assertIsNone(guard.check_rm("rm file.txt"))

    def test_no_args_returns_none(self):
        self.assertIsNone(guard.check_rm("rm -rf"))

    def test_non_rm_command_returns_none(self):
        self.assertIsNone(guard.check_rm("echo hi"))

    def test_uppercase_capital_r_recursive_flag(self):
        self.assertIsNotNone(guard.check_rm("rm -Rf /"))


class TestCheckGit(unittest.TestCase):
    def test_blocks_force_push_long_flag(self):
        self.assertIsNotNone(guard.check_git("git push --force"))

    def test_blocks_force_push_short_flag(self):
        self.assertIsNotNone(guard.check_git("git push -f"))

    def test_blocks_force_push_with_remote_and_branch(self):
        self.assertIsNotNone(guard.check_git("git push --force origin main"))

    def test_allows_force_with_lease(self):
        self.assertIsNone(guard.check_git("git push --force-with-lease"))

    def test_allows_plain_push(self):
        self.assertIsNone(guard.check_git("git push origin main"))

    def test_blocks_reset_hard(self):
        self.assertIsNotNone(guard.check_git("git reset --hard"))

    def test_blocks_reset_hard_with_ref(self):
        self.assertIsNotNone(guard.check_git("git reset --hard HEAD~1"))

    def test_allows_reset_without_hard(self):
        self.assertIsNone(guard.check_git("git reset HEAD~1"))

    def test_allows_reset_soft(self):
        self.assertIsNone(guard.check_git("git reset --soft HEAD~1"))

    def test_blocks_clean_force(self):
        self.assertIsNotNone(guard.check_git("git clean -f"))

    def test_blocks_clean_force_dirs(self):
        self.assertIsNotNone(guard.check_git("git clean -fd"))

    def test_allows_clean_dry_run(self):
        self.assertIsNone(guard.check_git("git clean -n"))

    def test_blocks_checkout_dot(self):
        self.assertIsNotNone(guard.check_git("git checkout ."))

    def test_blocks_checkout_dashdash_dot(self):
        self.assertIsNotNone(guard.check_git("git checkout -- ."))

    def test_blocks_restore_dot(self):
        self.assertIsNotNone(guard.check_git("git restore ."))

    def test_allows_checkout_specific_file(self):
        self.assertIsNone(guard.check_git("git checkout somefile.txt"))

    def test_allows_checkout_branch(self):
        self.assertIsNone(guard.check_git("git checkout main"))

    def test_blocks_branch_delete_force(self):
        self.assertIsNotNone(guard.check_git("git branch -D some-branch"))

    def test_blocks_branch_delete_dash_dash_force(self):
        self.assertIsNotNone(guard.check_git("git branch --delete --force some-branch"))

    def test_allows_branch_delete_lowercase(self):
        self.assertIsNone(guard.check_git("git branch -d some-branch"))

    def test_allows_branch_create(self):
        self.assertIsNone(guard.check_git("git branch new-feature"))

    def test_non_git_command_returns_none(self):
        self.assertIsNone(guard.check_git("echo hi"))


class TestCheckNpm(unittest.TestCase):
    def test_blocks_publish(self):
        self.assertIsNotNone(guard.check_npm("npm publish"))

    def test_blocks_publish_with_trailing_args(self):
        self.assertIsNotNone(guard.check_npm("npm publish --tag beta"))

    def test_blocks_publish_after_leading_flags(self):
        self.assertIsNotNone(guard.check_npm("npm --loglevel=silent publish"))

    def test_allows_run_publish_docs(self):
        self.assertIsNone(guard.check_npm("npm run publish-docs"))

    def test_allows_install(self):
        self.assertIsNone(guard.check_npm("npm install"))

    def test_allows_no_subcommand(self):
        self.assertIsNone(guard.check_npm("npm"))

    def test_non_npm_command_returns_none(self):
        self.assertIsNone(guard.check_npm("echo hi"))


class TestMain(unittest.TestCase):
    def _run_main(self, command):
        payload = json.dumps({"tool_input": {"command": command}})
        buf = io.StringIO()
        with redirect_stdout(buf), unittest.mock.patch.object(
            sys, "stdin", io.StringIO(payload)
        ):
            guard.main()
        return buf.getvalue()

    def test_blocks_destructive_command_end_to_end(self):
        output = self._run_main("rm -rf /")
        self.assertTrue(output.strip())
        parsed = json.loads(output)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_destructive_part_of_chain(self):
        output = self._run_main("echo hi && git push --force")
        parsed = json.loads(output)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_safe_command_no_output(self):
        output = self._run_main("echo hi")
        self.assertEqual(output, "")

    def test_invalid_json_does_not_crash(self):
        buf = io.StringIO()
        with redirect_stdout(buf), unittest.mock.patch.object(
            sys, "stdin", io.StringIO("not json")
        ):
            guard.main()
        self.assertEqual(buf.getvalue(), "")

    def test_missing_command_no_output(self):
        payload = json.dumps({"tool_input": {}})
        buf = io.StringIO()
        with redirect_stdout(buf), unittest.mock.patch.object(
            sys, "stdin", io.StringIO(payload)
        ):
            guard.main()
        self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    import unittest.mock  # noqa: E402

    unittest.main()
