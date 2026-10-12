"""Reproducible Codex context benchmark. Standard library only."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
VARIANTS = ("baseline", "lean-agents", "broad-skill", "targeted-skill", "quiet-test-skill", "full-history", "handoff-file")
TASKS = ("bugfix", "log-triage", "noisy-tests", "session-resume")

LEAN_AGENTS = """# Project instructions

- Start with a narrow search of likely files and tests. Expand only if needed.
- Exclude generated and vendor files from normal searches.
- For large logs, locate errors first and read a small window around the first relevant error.
- Verify code changes with the smallest relevant test command.
"""

BROAD_SKILL = """---
name: token-efficient-workflow
description: Always use this skill for every repository task to reduce context and tool output.
---

# Token efficient workflow

Classify the request as simple, standard, or deep. Identify likely owners, search there first,
then read small relevant sections. Avoid generated files and broad scans. Limit log excerpts to
the first relevant error and surrounding lines. Summarize large tool results. After an edit,
run the smallest relevant test. Keep the final answer concise and state verification.
"""

BROAD_AGENTS = """# Project instructions

For every task, read `.agents/skills/token-efficient-workflow/SKILL.md` and follow it.
"""

TARGETED_AGENTS = """# Project instructions

- For code changes, use the `focused-code-change` skill.
- For diagnosis of a large log, use the `first-error-triage` skill.
"""

CODE_SKILL = """---
name: focused-code-change
description: Use when changing code in this repository and selecting a relevant test.
---

# Focused code change

Search for the named behavior in source and tests. Read the matching file sections, make a
minimal change, and run the relevant test module. Expand only if the first evidence is unclear.
"""

LOG_SKILL = """---
name: first-error-triage
description: Use when diagnosing a failure from a large log in this repository.
---

# First error triage

Run `python tools/first_error.py logs/service.log`. Use its bounded output to identify the
first actionable error and cite the line. Inspect more log lines only if the excerpt is
insufficient. Do not change source code for a diagnosis-only request.
"""

FIRST_ERROR = """from pathlib import Path

path = Path('logs/service.log')
lines = path.read_text(encoding='utf-8').splitlines()
hits = [i for i, line in enumerate(lines) if 'ERROR' in line or 'Traceback' in line]
if not hits:
    print('No ERROR or Traceback found')
else:
    i = hits[0]
    for n in range(max(0, i - 3), min(len(lines), i + 8)):
        print(f'{n + 1}: {lines[n]}')
"""

QUIET_AGENTS = """# Project instructions

When running a test that prints many lines, read `.agents/skills/quiet-test-runner/SKILL.md`.
"""

QUIET_SKILL = """---
name: quiet-test-runner
description: Use when a relevant test prints hundreds of routine lines.
---

# Quiet test runner

Run the test via `python .agents/skills/quiet-test-runner/scripts/quiet_test.py -- <command>`.
The helper returns the same exit code. On failure it prints only the last 35 output lines;
on success it prints a short PASS line. If that excerpt omits the root cause, rerun a
focused test or inspect the full local output deliberately.
"""

QUIET_TEST = """import subprocess
import sys

command = sys.argv[1:]
if command and command[0] == '--':
    command = command[1:]
if not command:
    raise SystemExit('Usage: quiet_test.py -- <command>')
result = subprocess.run(command, capture_output=True, text=True, errors='replace')
output = (result.stdout + '\\n' + result.stderr).splitlines()
if result.returncode == 0:
    print(f'PASS: {len(output)} output lines suppressed')
else:
    print('\\n'.join(output[-35:]))
    print(f'FAIL: exit code {result.returncode}; showing last {min(len(output), 35)} lines')
raise SystemExit(result.returncode)
"""

HANDOFF = """# Session handoff

Goal: update `src/store/promo.py` so `final_price` follows the agreed promotion rules.

Verified decision:
- Ordinary customers' discount is capped at 15 percent.
- VIP customers may receive the full requested discount.
- Negative discounts are treated as zero.
- The final price may not be negative.

Relevant check: `python -m unittest tests.test_promo`.
No implementation or test run has been completed in this session.
"""


def put(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_fixture(path: Path, task: str, variant: str) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    put(path / "README.md", "# Small checkout service\n\nUse Python standard library only.\n")
    put(path / "src" / "store" / "checkout" / "fees.py", """def shipping_fee(subtotal: int) -> int:
    \"\"\"Shipping is free for orders of 50 or more.\"\"\"
    return 0 if subtotal > 50 else 7


def total(subtotal: int) -> int:
    return subtotal + shipping_fee(subtotal)
""")
    put(path / "tests" / "test_checkout.py", """import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from store.checkout.fees import shipping_fee, total


class CheckoutTests(unittest.TestCase):
    def test_shipping_below_threshold(self):
        self.assertEqual(shipping_fee(49), 7)

    def test_shipping_at_threshold(self):
        self.assertEqual(shipping_fee(50), 0)

    def test_shipping_above_threshold(self):
        self.assertEqual(shipping_fee(51), 0)

    def test_total_at_threshold(self):
        self.assertEqual(total(50), 50)


if __name__ == '__main__':
    unittest.main()
""")
    for n in range(40):
        put(path / "src" / "store" / "catalog" / f"item_{n:02d}.py",
            f"# Catalog note {n}: shipping labels are display-only.\n"
            f"def item_{n:02d}_label():\n    return 'shipping estimate'\n")
    if task == "log-triage":
        lines = [f"2026-10-12 08:{i // 60:02d}:{i % 60:02d} INFO request={i} checkout completed" for i in range(3000)]
        lines[1789] = "2026-10-12 08:29:49 ERROR checkout failed: KeyError: CHECKOUT_REGION"
        lines[1790] = "2026-10-12 08:29:49 Traceback: settings['CHECKOUT_REGION'] in config.py:42"
        lines[1791] = "2026-10-12 08:29:49 ERROR startup configuration missing CHECKOUT_REGION"
        put(path / "logs" / "service.log", "\n".join(lines) + "\n")
        put(path / "src" / "store" / "config.py", """import os

def checkout_region():
    return os.environ['CHECKOUT_REGION']
""")
    if task == "noisy-tests":
        put(path / "src" / "store" / "report.py", """def report_total(values: list[int]) -> int:
    return sum(values[:-1])
""")
        put(path / "tests" / "test_report.py", """import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from store.report import report_total


class ReportTests(unittest.TestCase):
    def test_total(self):
        for n in range(2500):
            print(f'processed routine shard {n}')
        self.assertEqual(report_total([1, 2, 3]), 6)


if __name__ == '__main__':
    unittest.main()
""")
    if task == "session-resume":
        put(path / "src" / "store" / "promo.py", """def final_price(subtotal: int, discount_percent: int, vip: bool = False) -> int:
    return subtotal - subtotal * discount_percent // 100
""")
        put(path / "tests" / "test_promo.py", """import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from store.promo import final_price


class PromoTests(unittest.TestCase):
    def test_discount_cap(self):
        self.assertEqual(final_price(100, 30), 85)

    def test_vip_discount(self):
        self.assertEqual(final_price(100, 30, vip=True), 70)

    def test_negative_discount(self):
        self.assertEqual(final_price(100, -10), 100)

    def test_nonnegative_price(self):
        self.assertEqual(final_price(100, 200, vip=True), 0)


if __name__ == '__main__':
    unittest.main()
""")
        if variant == "handoff-file":
            put(path / "HANDOFF.md", HANDOFF)
    if variant == "lean-agents":
        put(path / "AGENTS.md", LEAN_AGENTS)
    elif variant == "broad-skill":
        put(path / "AGENTS.md", BROAD_AGENTS)
        put(path / ".agents" / "skills" / "token-efficient-workflow" / "SKILL.md", BROAD_SKILL)
    elif variant == "targeted-skill":
        put(path / "AGENTS.md", TARGETED_AGENTS)
        put(path / ".agents" / "skills" / "focused-code-change" / "SKILL.md", CODE_SKILL)
        put(path / ".agents" / "skills" / "first-error-triage" / "SKILL.md", LOG_SKILL)
        put(path / "tools" / "first_error.py", FIRST_ERROR)
    elif variant == "quiet-test-skill":
        put(path / "AGENTS.md", QUIET_AGENTS)
        put(path / ".agents" / "skills" / "quiet-test-runner" / "SKILL.md", QUIET_SKILL)
        put(path / ".agents" / "skills" / "quiet-test-runner" / "scripts" / "quiet_test.py", QUIET_TEST)


def run_one(task: str, variant: str, repeat: int, model: str, timeout: int) -> dict:
    run_id = f"{task}__{variant}__{repeat}"
    path = RUNS / run_id
    make_fixture(path, task, variant)
    prompts = {
        "bugfix": "Customers with exactly 50 subtotal are still charged shipping. Fix this behavior, preserve the other cases, and verify with a relevant test.",
        "log-triage": "Diagnose the first checkout failure in logs/service.log. Give its root cause and cite the log line. This is diagnosis only; do not edit files.",
        "noisy-tests": "The report total for [1, 2, 3] is wrong. Fix it and verify with the relevant test. The test emits a large amount of routine progress output.",
    }
    if task == "session-resume":
        if variant == "full-history":
            transcript = []
            for n in range(90):
                transcript.append(
                    f"Earlier discussion {n + 1}: reviewed routine catalog formatting, naming, "
                    "a shipping label, and report layout. No promotion rule was decided in this part."
                )
            transcript.append("Final verified decision: ordinary customers' discount is capped at 15 percent; VIP customers may receive the full requested discount; negative discounts count as zero; final price cannot be negative. Relevant code: src/store/promo.py. Verify with python -m unittest tests.test_promo.")
            prompt = "Continue the previously agreed promotion change. Here is the full prior transcript:\n" + "\n".join(transcript) + "\nImplement and verify it."
        else:
            prompt = "Continue the previously agreed promotion change. Read HANDOFF.md, implement its verified decision, and run the relevant test."
    else:
        prompt = prompts[task]
    cmd = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--json",
           "--sandbox", "workspace-write", "--model", model,
           "--config", 'model_reasoning_effort="low"', prompt]
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=path, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        exit_code = 124
    elapsed = round(time.monotonic() - start, 2)
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    usage = next((e.get("usage", {}) for e in reversed(events) if e.get("type") == "turn.completed"), {})
    messages = [e["item"].get("text", "") for e in events
                if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
    tool_events = [e for e in events if e.get("type") == "item.completed" and
                   e.get("item", {}).get("type") not in ("agent_message", None)]
    final = messages[-1] if messages else ""
    if task == "bugfix":
        verify = subprocess.run(["python", "-m", "unittest", "discover", "-s", "tests"],
                                cwd=path, capture_output=True, text=True)
        correct = verify.returncode == 0 and "return 0 if subtotal >= 50" in (path / "src/store/checkout/fees.py").read_text(encoding="utf-8")
        test_claim = bool(re.search(r"test|unittest|passed", final, re.I))
    elif task == "noisy-tests":
        verify = subprocess.run(["python", "-m", "unittest", "tests.test_report"],
                                cwd=path, capture_output=True, text=True)
        correct = verify.returncode == 0 and "return sum(values)" in (path / "src/store/report.py").read_text(encoding="utf-8")
        test_claim = bool(re.search(r"test|unittest|passed", final, re.I))
    elif task == "session-resume":
        verify = subprocess.run(["python", "-m", "unittest", "tests.test_promo"],
                                cwd=path, capture_output=True, text=True)
        correct = verify.returncode == 0
        test_claim = bool(re.search(r"test|unittest|passed", final, re.I))
    else:
        correct = "CHECKOUT_REGION" in final and bool(re.search(r"1790|1789|1791|config.py", final))
        test_claim = None
    record = {
        "run_id": run_id, "task": task, "variant": variant, "repeat": repeat,
        "model": model, "exit_code": exit_code, "elapsed_seconds": elapsed,
        "usage": usage, "correct": correct, "mentions_test": test_claim,
        "tool_events": len(tool_events), "final": final, "stderr_tail": stderr[-1500:],
    }
    put(path / "events.jsonl", stdout)
    put(path / "result.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument("--variants", nargs="+", choices=VARIANTS)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--start-repeat", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    RUNS.mkdir(exist_ok=True)
    results_file = ROOT / "results.json"
    results = json.loads(results_file.read_text(encoding="utf-8")) if results_file.exists() else []
    for task in args.tasks:
        if task == "noisy-tests":
            default_variants = ("baseline", "quiet-test-skill")
        elif task == "session-resume":
            default_variants = ("full-history", "handoff-file")
        else:
            default_variants = VARIANTS[:4]
        for variant in args.variants or default_variants:
            for repeat in range(args.start_repeat, args.start_repeat + args.repeats):
                if args.prepare_only:
                    make_fixture(RUNS / f"{task}__{variant}__{repeat}", task, variant)
                    continue
                print(f"Running {task} / {variant} / {repeat}", flush=True)
                result = run_one(task, variant, repeat, args.model, args.timeout)
                results = [old for old in results if old["run_id"] != result["run_id"]]
                results.append(result)
                print(json.dumps({k: result[k] for k in ("run_id", "correct", "elapsed_seconds", "usage")}), flush=True)
                put(results_file, json.dumps(results, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
