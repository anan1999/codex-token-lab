---
name: session-handoff
description: Use when the user asks to pause, switch Codex sessions, save progress, or resume from a handoff.
---

# Session handoff

Use only for work that will continue in another session. Do not create a handoff for routine
short tasks.

## Save

1. Inspect current git status and the relevant changed files.
2. Write or update `HANDOFF.md` with the goal, verified decisions, completed work, test
   results, open issues, relevant paths, and the exact next action.
3. Separate verified facts from hypotheses. Never copy credentials or private tokens.
4. Keep it concise; aim for under 500 words. Do not paste the full conversation.

## Resume

1. Read `HANDOFF.md` and the relevant current files.
2. Compare its branch, file status, and claimed test results with current workspace state.
3. Continue from the listed next action. If the workspace changed, update the handoff before
   relying on stale claims.

`HANDOFF.md` is a working checkpoint, not a substitute for running tests or inspecting the
current code.
