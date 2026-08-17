# File Summary

- **CLAUDE.md** — Guidance for Claude Code on this repo: build/run/test commands and architecture overview.
- **main.cpp** — CLI entry point; dispatches `add`/`list`/`done`/`update` subcommands and saves state.
- **tasks.hpp** — Shared logic: `Task` struct, hand-rolled `JsonParser`, `loadTasks`/`saveTasks`, and `nextId`.
