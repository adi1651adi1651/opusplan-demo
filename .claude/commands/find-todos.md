---
description: Find TODO/FIXME comments in the codebase and list them with file:line references
---
Search the codebase for `TODO`, `FIXME`, and `XXX` comments (case-insensitive), excluding build artifacts and `tasks.json`.

Report them grouped by file, each entry as `file:line — comment text`. If none are found, say so plainly instead of fabricating any.
