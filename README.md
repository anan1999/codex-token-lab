# Codex Token Lab

Reproducible experiments and small, Codex-native tools for reducing unnecessary context use.

Read the [measured results](RESULTS.md) before installing anything. In this pilot, no
configuration won across every task; Codex already suppressed a large test output on its own.
The [GitHub research inventory](RESEARCH.md) explains which approaches informed the tests.

## Scope

This repository compares a plain Codex run with a short `AGENTS.md`, a broad always-on skill,
conditionally routed skills with a bounded log helper, a quiet-test helper, and a separate
cross-session handoff. It measures token use **and** task correctness. These are small
controlled fixtures; results are not a universal claim about every repository or model.

The reusable configuration lives under `toolkit/`. Its short project guidance is the first
thing to try. The log skill is optional because a capable Codex run may already isolate the
error efficiently.

## Use inside Codex

1. Ask Codex to merge [`toolkit/AGENTS.example.md`](toolkit/AGENTS.example.md) into your
   project's `AGENTS.md`. Keep your existing repository rules and remove guidance that does
   not apply.
2. For large log files, ask Codex to copy
   [`toolkit/.agents/skills/failure-triage`](toolkit/.agents/skills/failure-triage)
   into your project's `.agents/skills/`. The bundled Python helper uses only the standard
   library; it runs from Codex when that skill is selected.
3. For long work that crosses sessions, copy
   [`toolkit/.agents/skills/session-handoff`](toolkit/.agents/skills/session-handoff)
   into the same skills directory and invoke it when you need a checkpoint. The
   [handoff template](toolkit/HANDOFF.example.md) shows the intended content.
4. Work normally in Codex. There is no separate agent service or replacement CLI.

Always inspect a downloaded script before adding it to a project. See [RESULTS.md](RESULTS.md)
for cases where extra instructions cost more than they save.

## Reproduce

Requirements: Python 3.10+, an authenticated Codex installation, and access to the selected
model. The benchmark invokes Codex; it does not replace Codex or run a separate agent.

```shell
python benchmark.py --model gpt-6-luna
```

For a second pass in reverse variant order:

```shell
python benchmark.py --model gpt-6-luna --tasks bugfix log-triage --variants targeted-skill broad-skill lean-agents baseline --start-repeat 2
```

The script creates an isolated folder per run under `runs/`, records Codex JSON events locally,
checks the resulting answer or code, and writes `results.json`. These local results and raw
events may contain environment details and are intentionally ignored by Git. `RESULTS.md`
contains the reviewed, shareable measurements.

The default command runs 12 Codex tasks and consumes account usage. For a small first check,
run `python benchmark.py --tasks log-triage --variants baseline lean-agents`.

## Measurements

- `input_tokens`: all input tokens reported by Codex, including cached input.
- `cached_input_tokens`: the cached subset of input tokens.
- `output_tokens` and `reasoning_output_tokens`: output measurements from Codex.
- `correct`: task-specific correctness check.
- `elapsed_seconds`: wall time, including tool calls.

Each run has the same model, reasoning effort, prompt, base fixture, and local Codex setup;
the variant controls only project instructions, skills, and one bounded log helper. Since model
behavior varies, use repeated runs before making strong claims. Compare token use only among
variants that completed the task correctly.
