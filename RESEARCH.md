# GitHub approaches surveyed

Reviewed on 2026-10-12. This is an architecture inventory, not a ranking of maintainers or
an endorsement of each repository. The benchmark tests representative *patterns* implemented
locally, not the upstream repositories' exact code.

| Source | Pattern | Codex-native? | Practical observation |
|---|---|---|---|
| [openai/codex AGENTS.md](https://github.com/openai/codex/blob/main/AGENTS.md) | Bound every injected context fragment; avoid cache churn | Yes | A useful design rule for harness authors |
| [openai/codex skill creator](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md) | Skill metadata → instructions → optional resources | Yes | Keep entrypoints short and load details on demand |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python/blob/main/AGENTS.md) | Conditional skill routing from AGENTS.md | Yes | Precise triggers avoid loading unrelated procedures |
| [openai/openai-cookbook](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/migrate-from-claude-agent-sdk/README.md) | Separate repo conventions, procedures, and references | Yes | Good placement guide for each kind of instruction |
| [Creativebrook/codex-token-optimizer-kit](https://github.com/Creativebrook/codex-token-optimizer-kit) | Task tiers, narrow search, log limits, helper scripts | Mostly | Broad skill descriptions can become recurring context cost |
| [luziyezz/codex-skills](https://github.com/luziyezz/codex-skills/blob/main/token-efficient-workflow/SKILL.md) | Always-on search/output discipline | Yes | Test whether repeated instruction loading pays for itself |
| [Phelan164/codex-howto](https://github.com/Phelan164/codex-howto/blob/main/modules/10-context-and-token-efficiency/README.md) | Context hierarchy and ablation testing | Yes | Evaluate quality and token use together |
| [lwp659/codex-memory-skill](https://github.com/lwp659/codex-memory-skill) | Explicit, compact handoff.md | Yes | Useful for interrupted work, with a write/read cost |
| [lifang336/codex-session-handoff](https://github.com/lifang336/codex-session-handoff) | Structured cross-session checkpoints | Yes | Better fit for long work than routine tiny edits |
| [suzxa/codex-skills](https://github.com/suzxa/codex-skills/blob/main/codex-context-manager/SKILL.md) | Scripted persistent memory and recall | Yes, with scripts | Adds retrieval and maintenance cost |
| [swannysec/context-keeper](https://github.com/swannysec/context-keeper) | Memory init/sync/handoff workflows | Yes | Community implementation still needs verification |
| [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | Shell output compression proxy | Extra CLI | Can reduce tool output; separate installation/runtime |
| [oraios/serena](https://github.com/oraios/serena) | Semantic code retrieval/editing | Extra MCP | Can help large repos; tool schemas and server add overhead |

The local benchmark covers four Codex-native instruction patterns on a code fix and log triage,
a bounded test-output helper, and a separate cross-session handoff scenario. Semantic retrieval
and external proxies need different environments and are not ranked here.
