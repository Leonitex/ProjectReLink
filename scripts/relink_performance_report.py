"""Compare Project ReLink FPS, frame costs and memory pressure across text logs.

Read-only, stdlib-only; no saves or game files are opened.
Usage: python scripts/relink_performance_report.py relink_log.txt [other logs...]
"""
import argparse
import re
import statistics
from pathlib import Path

NUM = r"([0-9]+(?:\.[0-9]+)?)"
FPS = re.compile(r"vi: \d+ frames presented \(" + NUM + r" fps over the last " + NUM + r" s")
GPU = re.compile(r"vk: GPU time " + NUM + r" ms a frame")
REPLAY = re.compile(r"vk: a frame's replay time \(ms\): submit " + NUM + r".*?memory sync " + NUM)
VRAM = re.compile(r"vk: VRAM: (\d+) MB used of (\d+) MB allowed \(\d+ MB of it free in the blocks\); textures (\d+) MB \(budget (\d+) MB\)")
TEX = re.compile(r"vk: \d+ presents, " + NUM + r" fps; a frame:.*?\b(\d+) textures \((\d+) MB\)")


def measures(lines):
    out = {k: [] for k in ("fps", "gpu_ms", "submit_ms", "sync_ms", "vram_used", "vram_allowed", "textures", "texture_budget", "live_texture_mb")}
    out.update(fast_sync="unknown", fps_cap="unknown", ram_parked_events=0)
    for line in lines:
        if "env: relink_env.txt read:" in line and "RX_VK_FAST_SYNC=0" in line:
            out["fast_sync"] = "off"
        if "vk: fast sync: the exposure meter is met" in line:
            out["fast_sync"] = "on"
        if "vk: 30 fps cap:" in line:
            out["fps_cap"] = "30"
        if "the GPU drew: evicted, its texels kept in system memory" in line:
            out["ram_parked_events"] += 1
        if m := FPS.search(line):
            out["fps"].append(float(m[1]))
        if m := GPU.search(line):
            out["gpu_ms"].append(float(m[1]))
        if m := REPLAY.search(line):
            out["submit_ms"].append(float(m[1]))
            out["sync_ms"].append(float(m[2]))
        if m := VRAM.search(line):
            for key, val in zip(("vram_used", "vram_allowed", "textures", "texture_budget"), m.groups()):
                out[key].append(int(val))
        if m := TEX.search(line):
            out["live_texture_mb"].append(int(m[3]))
    return out


def summarize(data):
    summary = {k: data[k] for k in ("fast_sync", "fps_cap", "ram_parked_events")}
    for k, v in data.items():
        if isinstance(v, list):
            summary[k + "_count"] = len(v)
            if v:
                summary[k + "_min"] = min(v)
                summary[k + "_median"] = round(statistics.median(v), 2)
                summary[k + "_max"] = max(v)
    summary["vram_over_allowance"] = sum(u > a for u, a in zip(data["vram_used"], data["vram_allowed"]) if a)
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("logs", type=Path, nargs="+")
    args = p.parse_args(argv)
    for path in args.logs:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                result = summarize(measures(f))
        except OSError as exc:
            p.error(f"cannot read {path.name}: {exc}")
        print(f"\n{path.name}: fast sync {result['fast_sync']}; cap {result['fps_cap']}")
        for k in ("fps", "gpu_ms", "submit_ms", "sync_ms", "vram_used", "live_texture_mb"):
            n = result[k + "_count"]
            if n:
                print(f"  {k}: {n} samples; min {result[k + '_min']}, median {result[k + '_median']}, max {result[k + '_max']}")
        print(f"  VRAM samples over allowance: {result['vram_over_allowance']}; GPU-to-RAM park events: {result['ram_parked_events']}")
    print("\nCompare matched scenes with the same settings. Presented FPS can include generated frames.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
