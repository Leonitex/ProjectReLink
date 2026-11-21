"""Summarize Project ReLink's Vulkan memory diagnostic lines.

Read-only, standard-library-only. No game dumps, shaders or saves are read.
Usage: python scripts/low_vram_log_report.py relink.log [--csv samples.csv]
"""

import argparse
import csv
import re
from pathlib import Path

VRAM = re.compile(
    r"vk:\s*VRAM:\s*(?P<used>\d+) MB used of (?P<allowed>\d+) MB allowed "
    r"\((?P<block_free>\d+) MB of it free in the blocks\); "
    r"textures (?P<textures>\d+) MB \(budget (?P<budget>\d+) MB\)",
    re.IGNORECASE,
)
FIELDS = ("used", "allowed", "block_free", "textures", "budget")


def parse_samples(lines):
    """Return memory samples in their original log order."""
    samples = []
    for line in lines:
        found = VRAM.search(line)
        if found:
            samples.append({key: int(found.group(key)) for key in FIELDS})
    return samples


def summarize(samples):
    """Return a diagnostic summary; avoid inferring FPS from memory samples."""
    if not samples:
        return None
    known = [s for s in samples if s["allowed"] > 0]
    high_pressure = sum(s["used"] >= 0.90 * s["allowed"] for s in known)
    over_budget = sum(s["textures"] > s["budget"] for s in samples)
    return {
        "samples": len(samples),
        "peak_vram_used_mb": max(s["used"] for s in samples),
        "minimum_reported_budget_mb": min(s["budget"] for s in samples),
        "peak_textures_mb": max(s["textures"] for s in samples),
        "high_pressure_samples": high_pressure,
        "samples_with_known_allowance": len(known),
        "textures_over_budget_samples": over_budget,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Plain-text Project ReLink Vulkan log")
    parser.add_argument("--csv", type=Path, help="Optional CSV of the parsed VRAM samples")
    args = parser.parse_args(argv)
    try:
        with args.log.open("r", encoding="utf-8", errors="replace") as stream:
            samples = parse_samples(stream)
    except OSError as exc:
        parser.error(f"cannot read log: {exc}")
    result = summarize(samples)
    if result is None:
        parser.error("no 'vk: VRAM:' samples found; use a log from an in-game session")
    print("Project ReLink Vulkan VRAM samples (not FPS measurements)")
    for key, value in result.items():
        print(f"  {key}: {value}")
    if args.csv:
        try:
            with args.csv.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(samples)
        except OSError as exc:
            parser.error(f"cannot write CSV: {exc}")
        print(f"  csv: {args.csv}")
    if result["samples_with_known_allowance"] and result["high_pressure_samples"]:
        print("  note: driver memory pressure was >=90% in one or more samples")
    if result["textures_over_budget_samples"]:
        print("  note: textures exceeded their reported budget in one or more samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
