"""Print a bounded excerpt around the first actionable log error."""

from __future__ import annotations

import argparse
import re
from collections import deque
from pathlib import Path


ERROR = re.compile(r"\b(ERROR|FATAL|Traceback|Exception)\b", re.IGNORECASE)


def first_error(path: Path, before: int, after: int) -> list[tuple[int, str]]:
    previous: deque[tuple[int, str]] = deque(maxlen=before)
    selected: list[tuple[int, str]] = []
    remaining = -1
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.rstrip("\r\n")
            if remaining >= 0:
                selected.append((line_number, line))
                remaining -= 1
                if remaining < 0:
                    break
            elif ERROR.search(line):
                selected.extend(previous)
                selected.append((line_number, line))
                remaining = after - 1
                if after == 0:
                    break
            else:
                previous.append((line_number, line))
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--before", type=int, default=3)
    parser.add_argument("--after", type=int, default=7)
    args = parser.parse_args()
    if not 0 <= args.before <= 20 or not 0 <= args.after <= 20:
        parser.error("--before and --after must each be between 0 and 20")
    try:
        excerpt = first_error(args.log_path, args.before, args.after)
    except OSError as exc:
        parser.error(str(exc))
    if not excerpt:
        print("No ERROR, FATAL, Traceback, or Exception marker found.")
    for line_number, line in excerpt:
        print(f"{line_number}: {line}")


if __name__ == "__main__":
    main()
