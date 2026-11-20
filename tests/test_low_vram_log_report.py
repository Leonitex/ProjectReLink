"""Unit tests for the read-only Vulkan VRAM log parser."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from low_vram_log_report import parse_samples, summarize  # noqa: E402


class TestLowVramReport(unittest.TestCase):
    def test_sample_and_noise(self):
        samples = parse_samples([
            "2026 info: vk: a different message\n",
            "vk: VRAM: 3270 MB used of 3800 MB allowed (220 MB of it free in the blocks); textures 2130 MB (budget 2200 MB), 1290 textures\n",
            "vk: VRAM: 3500 MB used of 3800 MB allowed (75 MB of it free in the blocks); textures 2250 MB (budget 2000 MB), 1320 textures\n",
        ])
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0]["allowed"], 3800)
        summary = summarize(samples)
        self.assertEqual(summary["peak_vram_used_mb"], 3500)
        self.assertEqual(summary["high_pressure_samples"], 1)
        self.assertEqual(summary["textures_over_budget_samples"], 1)
        self.assertEqual(summary["minimum_reported_budget_mb"], 2000)

    def test_empty_and_unknown_allowance(self):
        self.assertIsNone(summarize(parse_samples(["some other log line"])))
        summary = summarize(parse_samples([
            "vk: VRAM: 100 MB used of 0 MB allowed (0 MB of it free in the blocks); textures 0 MB (budget 500 MB)"
        ]))
        self.assertEqual(summary["samples_with_known_allowance"], 0)
        self.assertEqual(summary["high_pressure_samples"], 0)


if __name__ == "__main__":
    unittest.main()
