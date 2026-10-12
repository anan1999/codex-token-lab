# Codex project guidance

- Search for the task's named behavior or error in likely source and test paths first.
- Read complete large files or logs only if a focused excerpt is insufficient.
- Exclude generated, dependency, and build directories from ordinary searches.
- For large logs, read `.agents/skills/failure-triage/SKILL.md` and follow it.
- After a code change, run the smallest relevant test, then expand if it fails.

Replace this example with your repository's actual entry points and test commands. Remove
instructions that do not apply. Keep large architecture notes in separate files and link them
only under the conditions when they matter.
