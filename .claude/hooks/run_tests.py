"""PostToolUse hook: run the test suite after editing a .py file.

Reads the hook input JSON from stdin. On test failure, prints a
decision:block JSON response so the failure is fed back into the
conversation instead of failing silently.
"""

import json
import subprocess
import sys

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")
if not file_path.endswith(".py"):
    sys.exit(0)

result = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    output = (result.stdout + result.stderr).strip()
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": f"Tests failed after editing {file_path}:\n\n{output[-4000:]}",
                "hookSpecificOutput": {"hookEventName": "PostToolUse"},
            }
        )
    )
