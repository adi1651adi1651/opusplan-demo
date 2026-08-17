"""Destructive-command rules for guard.sh (PreToolUse, matcher: Bash).

Reads the hook input JSON from stdin. If the Bash command being about to run
matches a known-destructive pattern, prints a permissionDecision:"deny" JSON
response instead of letting it through. This is a safety net for obviously
catastrophic commands, not a security boundary — anything ambiguous is
allowed through to the normal permission flow.
"""

import json
import os
import re
import sys

BROAD_TARGETS = {"/", "~", ".", "..", "*", os.path.expanduser("~")}

FORCE_PUSH_RE = re.compile(r"^\s*(sudo\s+)?git\s+push\b")
FORCE_FLAG_RE = re.compile(r"(--force(?!-with-lease)\b|(?:^|\s)-f\b)")
RESET_HARD_RE = re.compile(r"^\s*(sudo\s+)?git\s+reset\s+.*--hard\b")
CLEAN_FORCE_RE = re.compile(r"^\s*(sudo\s+)?git\s+clean\b")
CLEAN_FLAG_RE = re.compile(r"(--force\b|(?:^|\s)-\w*f\w*\b)")
CHECKOUT_ALL_RE = re.compile(r"^\s*(sudo\s+)?git\s+(checkout|restore)\s+(--\s+)?\.\s*$")
BRANCH_DELETE_FORCE_RE = re.compile(
    r"^\s*(sudo\s+)?git\s+branch\s+.*(-D\b|--delete\s+--force)"
)


def split_commands(cmd: str):
    return [c.strip() for c in re.split(r"&&|\|\||;|\|", cmd) if c.strip()]


def has_flag(flags, short_char, long_name):
    for f in flags:
        if f.startswith("--"):
            if f == long_name:
                return True
        elif f.startswith("-"):
            if short_char in f[1:]:
                return True
    return False


def check_rm(sub: str):
    m = re.match(r"^\s*(?:sudo\s+)?rm\s+(.*)$", sub)
    if not m:
        return None
    tokens = m.group(1).split()
    flags = [t for t in tokens if t.startswith("-")]
    args = [t for t in tokens if not t.startswith("-")]
    if not args:
        return None
    has_r = has_flag(flags, "r", "--recursive") or has_flag(flags, "R", "--recursive")
    has_f = has_flag(flags, "f", "--force")
    if not (has_r and has_f):
        return None
    target = args[0].strip("'\"")
    target = re.sub(r"/\*$", "", target)
    target = os.path.expandvars(target)
    if target in BROAD_TARGETS:
        return f"recursive force-delete of a broad path ({sub!r})"
    return None


def check_git(sub: str):
    if FORCE_PUSH_RE.match(sub) and FORCE_FLAG_RE.search(sub):
        return f"force push ({sub!r}) can overwrite remote history"
    if RESET_HARD_RE.match(sub):
        return f"git reset --hard discards uncommitted changes ({sub!r})"
    if CLEAN_FORCE_RE.match(sub) and CLEAN_FLAG_RE.search(sub):
        return f"git clean -f permanently deletes untracked files ({sub!r})"
    if CHECKOUT_ALL_RE.match(sub):
        return f"discards uncommitted changes across the working tree ({sub!r})"
    if BRANCH_DELETE_FORCE_RE.match(sub):
        return f"force-deletes a branch, even with unmerged commits ({sub!r})"
    return None


def check_npm(sub: str):
    m = re.match(r"^\s*(?:sudo\s+)?npm\s+(.*)$", sub)
    if not m:
        return None
    for t in m.group(1).split():
        if t.startswith("-"):
            continue
        if t == "publish":
            return f"npm publish ({sub!r}) publishes a package publicly and can't be undone"
        break
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    for sub in split_commands(command):
        reason = check_rm(sub) or check_git(sub) or check_npm(sub)
        if reason:
            # TODO: reviewed in print() audit, no cleanup action identified
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": f"Blocked by guard.sh: {reason}. Run manually if you're sure.",
                        }
                    }
                )
            )
            return


if __name__ == "__main__":
    main()
