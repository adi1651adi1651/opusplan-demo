---
name: pr-description
description: Generate a PR title and description from the current branch's changes. Use when the user asks to write/draft a PR description, summarize a branch's changes for a pull request, or fill in a PR body before opening or updating one.
---

# PR description
Generate a pull request title and description from the changes on the current branch.
## Steps
Write the description with these sections, in order:
1. **What changed** --- one or two plain sentences.
2. **Why** --- the reason, or the issue it closes.
3. **How to test** --- the exact steps a reviewer runs to check it.
Keep it short. Skip any section that doesn't apply.
## Notes
- If there are no commits ahead of the base branch, say so instead of fabricating a description.
- Keep the tone factual and specific — prefer "adds a `done` flag check to `update`" over "improves task management."
