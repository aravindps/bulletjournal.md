#!/usr/bin/env python3
"""Merge existing bullet journal entries into bjmd.py generated template."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BJMD = SCRIPT_DIR / "bjmd.py"
DEFAULT_REFERENCE = Path.home() / "Documents/reference/notes/reference/bullet_journal.md"
DEFAULT_OUTPUT = Path.home() / "bulletjournal/bulletjournal-2026.md"


def parse_date(heading: str):
    text = heading.strip().lstrip("#").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            part = text.split()[0] if " " in text else text
            dt = datetime.strptime(part, fmt)
            return (dt.year, dt.month, dt.day)
        except ValueError:
            continue
    return None


def is_month_heading(line: str) -> bool:
    return line.startswith("## ") and not line.startswith("### ")


def is_day_heading(line: str) -> bool:
    return line.startswith("### ")


def is_separator(line: str) -> bool:
    s = line.strip()
    return bool(s) and set(s) == {"-"}


def parse_reference(path: Path) -> dict:
    entries = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_day_heading(line):
            key = parse_date(line)
            if key:
                block = []
                i += 1
                while i < len(lines) and not is_month_heading(lines[i]):
                    if is_day_heading(lines[i]):
                        break
                    block.append(lines[i])
                    i += 1
                content = "\n".join(block).strip()
                if content:
                    entries[key] = entries.get(key, "") + ("\n" if key in entries else "") + content
                continue
        i += 1
    return entries


def merge_template(template: str, entries: dict) -> str:
    lines = template.splitlines()
    out = []
    i = 0
    merged_count = 0

    while i < len(lines):
        line = lines[i]

        if is_day_heading(line):
            key = parse_date(line)
            out.append(line)
            i += 1
            day_lines = []
            while i < len(lines):
                if is_day_heading(lines[i]) or is_month_heading(lines[i]) or is_separator(lines[i]):
                    break
                day_lines.append(lines[i])
                i += 1
            out.extend(day_lines)
            if key and key in entries:
                out.append("")
                out.append("#### Log")
                out.append(entries[key])
                out.append("")
                merged_count += 1
            continue

        out.append(line)
        i += 1

    header = f"<!-- merged from reference on {datetime.now():%Y-%m-%d %H:%M} -->"
    if out and not out[0].startswith("<!--"):
        out.insert(0, header)
    print(f"Merged {merged_count} day(s) from reference", file=sys.stderr)
    return "\n".join(out) + "\n"


def main():
    reference = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REFERENCE
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    if not reference.is_file():
        sys.exit(f"Reference not found: {reference}")

    result = subprocess.run(
        [sys.executable, str(BJMD)],
        capture_output=True,
        text=True,
        check=True,
        cwd=SCRIPT_DIR,
    )
    entries = parse_reference(reference)
    merged = merge_template(result.stdout, entries)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(merged, encoding="utf-8")
    print(f"Wrote {output} ({len(merged.splitlines())} lines)")


if __name__ == "__main__":
    main()
