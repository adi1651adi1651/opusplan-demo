# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file C++17 command-line task manager (`main.cpp`). It supports adding tasks, listing them, and marking them done, persisting state to `tasks.json` in the working directory.

## Build and run

There is no build system file (no CMakeLists.txt, Makefile, or vcxproj) — compile directly:

```sh
g++ -std=c++17 -o tasks main.cpp
./tasks add "buy milk"
./tasks list
./tasks done 1
```

No compiler is guaranteed to be present in the dev environment (g++/clang++/cl may all be absent) — verify with `g++ --version` before assuming a build will succeed.

There is no test suite.

## Architecture

Everything lives in `main.cpp`:

- **`Task` struct** — `{ id, text, done }`.
- **`JsonParser`** — a hand-rolled recursive-descent parser scoped only to the exact array-of-`{id,text,done}` shape this program writes (see `parseTasks`/`parseTask`). It is not a general JSON parser: unknown keys are skipped via `skipValue`, but the overall shape (top-level array of flat objects) is assumed, not validated.
- **`loadTasks`/`saveTasks`** — read/write `tasks.json` (path fixed via `kTasksFile`) using the parser above and manual string escaping (`escapeJson`) for serialization. There is no external JSON dependency.
- **`main`** — dispatches on `argv[1]` (`add`, `list`, `done`) between loading tasks, mutating the in-memory vector, and saving back to disk. IDs are assigned via `nextId`, which is `max(existing ids) + 1` (not reused after deletion, though there is currently no delete command).

`tasks.json` is created at runtime next to the executable and is not part of the source tree.
