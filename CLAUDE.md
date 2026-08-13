# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A C++17 command-line task manager. It supports adding tasks, listing them, and marking them done, persisting state to `tasks.json` in the working directory.

## Build and run

There is no build system file (no CMakeLists.txt, Makefile, or vcxproj) — compile directly:

```sh
g++ -std=c++17 -o tasks main.cpp
./tasks add "buy milk"
./tasks list
./tasks done 1
```

No compiler is guaranteed to be present in the dev environment (g++/clang++/cl may all be absent) — verify with `g++ --version` before assuming a build will succeed. GitHub Actions (`.github/workflows/build.yml`) is where the project is actually built and tested on every push/PR.

## Tests

Unit tests live in `tests/test_tasks.cpp` and cover `escapeJson`, `JsonParser`, `loadTasks`/`saveTasks`, and `nextId` directly (all defined in `tasks.hpp`, see Architecture below). They use a small hand-rolled `check`/`checkEq` harness — no external test framework, consistent with this project's zero-dependency approach (the same reasoning behind hand-rolling `JsonParser` instead of taking a JSON library dependency). Build and run with:

```sh
g++ -std=c++17 -o test_tasks tests/test_tasks.cpp
./test_tasks
```

A non-zero exit code indicates a failing assertion; failure output prints actual vs. expected for each check.

The CI smoke test (in the `build` job) is a separate, integration-level check — it exercises the compiled CLI binary end-to-end (argv parsing, file persistence across process invocations) — deliberately distinct from the unit tests, which never touch `main()`'s dispatch logic.

## Architecture

- **`tasks.hpp`** — the reusable logic, included by both `main.cpp` and `tests/test_tasks.cpp`:
  - **`Task` struct** — `{ id, text, done }`.
  - **`JsonParser`** — a hand-rolled recursive-descent parser scoped only to the exact array-of-`{id,text,done}` shape this program writes (see `parseTasks`/`parseTask`). It is not a general JSON parser: unknown keys are skipped via `skipValue`, but the overall shape (top-level array of flat objects) is assumed, not validated. It is also tolerant of missing trailing `}`/`]` (see tests) rather than erroring.
  - **`loadTasks`/`saveTasks`** — read/write `tasks.json` (path fixed via `kTasksFile`) using the parser above and manual string escaping (`escapeJson`) for serialization. There is no external JSON dependency.
  - **`nextId`** — `max(existing ids) + 1` (not reused after deletion, though there is currently no delete command).
- **`main.cpp`** — `main` dispatches on `argv[1]` (`add`, `list`, `done`) between loading tasks, mutating the in-memory vector, and saving back to disk.

`tasks.json` is created at runtime next to the executable and is not part of the source tree.
