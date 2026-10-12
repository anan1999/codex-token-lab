# Pilot results — 2026-10-12

Twenty Codex runs: three tasks, two runs per applicable variant. Every run completed its
task correctly. The second pass reversed variant order. These are exploratory measurements,
not statistically reliable estimates of savings in other repositories.

Environment: Windows, `codex-cli 0.155.0-alpha.16`, `gpt-6-luna`, low reasoning effort,
existing local Codex configuration, isolated Python-standard-library fixtures. The Codex
JSONL `turn.completed.usage` event supplied token counts. `input_tokens` **includes**
`cached_input_tokens`; the table does not estimate billing or Codex quota consumption.

## Average input tokens

| Task | Variant | Correct | Two runs | Mean input | Difference from task baseline |
|---|---|---:|---:|---:|---:|
| Shipping threshold bug | Plain Codex | 2/2 | 115,817; 72,880 | 94,349 | reference |
| Shipping threshold bug | Short `AGENTS.md` | 2/2 | 96,568; 96,568 | 96,568 | +2.4% |
| Shipping threshold bug | Always-on broad Skill | 2/2 | 124,532; 77,423 | 100,978 | +7.0% |
| Shipping threshold bug | Conditional Skills | 2/2 | 115,110; 93,211 | 104,161 | +10.4% |
| 3,000-line log diagnosis | Plain Codex | 2/2 | 56,852; 108,734 | 82,793 | reference |
| 3,000-line log diagnosis | Short `AGENTS.md` | 2/2 | 68,238; 50,729 | 59,484 | −28.2% |
| 3,000-line log diagnosis | Always-on broad Skill | 2/2 | 77,250; 61,492 | 69,371 | −16.2% |
| 3,000-line log diagnosis | Conditional Skill + bounded excerpt script | 2/2 | 67,908; 50,734 | 59,321 | −28.4% |
| 2,500-line test output | Plain Codex | 2/2 | 85,354; 84,675 | 85,015 | reference |
| 2,500-line test output | Quiet-test Skill + output filter | 2/2 | 86,284; 86,474 | 86,379 | +1.6% |

Means are rounded to the nearest whole token. See [`benchmark.py`](benchmark.py) for fixture
generation, exact prompts, variants, and correctness checks. Raw Codex events stay local;
they can contain machine-specific details.

## What the runs actually showed

- The plain bug-fix runs differed by 42,937 input tokens despite the same fixture and correct
  result. Two repetitions are too few to prove the small differences between variants.
- In the log task, the short guidance and the conditional Skill had lower two-run averages,
  but the baseline range overlaps their ranges. The bounded helper *did* run in the
  conditional-Skill trials.
- The broad Skill needed an explicit `AGENTS.md` pointer to load reliably. An earlier trial
  tried an incorrect global path; that invalid trial was replaced and is absent from the table.
  In one corrected bug-fix run, the broad Skill led to additional directory listing and a
  repeated search.
- In the noisy-test baseline, Codex redirected the large test output to `$null` and reported
  the pass result. The extra Skill and helper duplicated behavior Codex already performed in
  that run.

## Practical decision

Keep project instructions short and specific. Add a bounded helper when a *real* recurring
command or log is flooding Codex's context, then benchmark it on that workflow. Do not install
an always-on token optimization Skill solely on the expectation that it will save tokens.

The `toolkit/` files are optional examples, not a claimed universal winner. For a new project,
run the baseline first. Keep only configuration that preserves correctness and measurably helps
on several representative tasks.

Handoff memory, semantic retrieval, external CLI proxies, and different models were not
tested here. They require distinct task designs and would not be fairly ranked by these three
short fixtures.
