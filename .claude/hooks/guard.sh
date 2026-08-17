#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) — blocks obviously destructive commands
# before they run. Rules live in guard.py, next to this script.
exec python "$(dirname "${BASH_SOURCE[0]}")/guard.py"
