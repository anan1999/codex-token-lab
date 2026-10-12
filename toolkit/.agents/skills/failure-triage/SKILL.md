---
name: failure-triage
description: Use when diagnosing an error from a large text log or command output file.
---

# Failure triage

1. Find the first actionable error with
   `python .agents/skills/failure-triage/scripts/first_error.py <log-path>`.
2. Read the bounded excerpt and cite its original line number.
3. If the excerpt is insufficient, inspect the specific named file or a slightly larger window.
4. State the observed cause separately from any inference. Do not edit code for a diagnosis-only request.

The helper reads locally and prints at most the selected error plus a small context window.
