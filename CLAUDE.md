# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python 3 command-line task manager. It supports adding tasks, listing them, updating their text, and marking them done, persisting state to `tasks.json` in the working directory.

This was originally a C++17 implementation; it was fully ported to Python, retiring the C++ sources in favor of a Python one.

## Build and run

No build step — run directly with Python 3 (uses only the standard library, no dependencies to install):

```sh
python main.py add "buy milk"
python main.py list
python main.py done 1
python main.py update 1 "buy oat milk"
```

## Tests

Unit tests live in `tests/test_tasks.py` and cover `load_tasks`/`save_tasks`/`next_id` (all defined in `tasks.py`, see Architecture below) via Python's stdlib `unittest`. Run with:

```sh
python -m unittest tests/test_tasks.py -v
```

`main.py`'s argv dispatch logic (`add`/`list`/`done`/`update`) is covered separately, by `tests/test_cli.py`, since it isn't decomposed into testable functions — it reads `sys.argv` directly, writes to stdout, and reads/writes the hardcoded `tasks.json` path. That test drives `python main.py` as a subprocess (once per test, in an isolated temp directory via `tempfile.TemporaryDirectory`) and asserts on its stdout and the resulting `tasks.json`. Run with:

```sh
python -m unittest tests/test_cli.py -v
```

The CI smoke test (`smoke-test` job) is a separate, lighter integration check that just exercises a few CLI invocations inline in the workflow; `test_cli.py` (its own `cli-tests` job) is the fuller, assertion-based equivalent.

`tests/test_claude_workflow.py` structurally validates `.github/workflows/claude.yml` (triggers, the `@claude`-mention gate, permissions, steps) by parsing it with PyYAML — see Tooling below. Run with:

```sh
python -m unittest tests/test_claude_workflow.py -v
```

## Architecture

- **`tasks.py`** — the reusable logic, imported by both `main.py` and `tests/test_tasks.py`:
  - **`Task`** — a `@dataclass` with `id`, `text`, `done`.
  - **`load_tasks`/`save_tasks`** — read/write `tasks.json` (path fixed via `TASKS_FILE`) using the stdlib `json` module. No hand-rolled parser or external JSON dependency — unlike the retired C++ version, Python's stdlib already provides this.
  - **`next_id`** — `max(existing ids) + 1` (not reused after deletion, though there is currently no delete command).
- **`main.py`** — `main(argv)` dispatches on `argv[1]` (`add`, `list`, `done`, `update`) between loading tasks, mutating the in-memory list, and saving back to disk.

`tasks.json` is created at runtime next to wherever the CLI is invoked and is not part of the source tree.

## Tooling

Use the `/permissions` command in Claude Code to view or change which tools/commands are auto-allowed, ask for confirmation, or are denied in this project.

`.claude/settings.json` runs `black` on `.py` files via a `PostToolUse` hook after every Write/Edit, so files are kept auto-formatted during a Claude Code session. Requires `pip install black`; the hook no-ops (rather than failing) if black isn't installed.

`tests/test_claude_workflow.py` parses the Claude workflow YAML with PyYAML for real structural validation. Requires `pip install pyyaml`; if it isn't installed, that test module's cases are skipped (not failed) rather than erroring out the rest of the suite.
