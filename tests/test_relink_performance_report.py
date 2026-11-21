"""Unit tests for performance log parser."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from relink_performance_report import measures, summarize


class ReLinkPerformanceReportTest(unittest.TestCase):
    def test_fast_sync_off_with_low_fps_and_vram_pressure(self):
        lines = [
            "[hos host] env: relink_env.txt read: RX_VK_FAST_SYNC=0\n",
            "[hos Presentation Thread] vk: 30 fps cap: each frame held for 2 refreshes\n",
            "[hos Presentation Thread] vi: 1666 frames presented (6.5 fps over the last 5.1 s, interval 1)\n",
            "[hos Presentation Thread] vk: GPU time 63.0 ms a frame (longest 80)\n",
            "[hos Presentation Thread] vk: a frame's replay time (ms): submit 86.67, present 2.66, draw 27.59, memory sync 43.49, queue submit 1.52\n",
            "[hos Presentation Thread] vk: VRAM: 3917 MB used of 3361 MB allowed (321 MB of it free in the blocks); textures 2337 MB (budget 1680 MB), 1044 textures\n",
            "[hos Presentation Thread] vk: 1680 presents, 8.9 fps; a frame: 1102 draws (0 skipped), 73 dispatches, 1468 textures (3356 MB)\n",
            "[hos Presentation Thread] vk: texture #10 0x123 the GPU drew: evicted, its texels kept in system memory (900 KB)\n",
        ]
        report = summarize(measures(lines))
        self.assertEqual((report["fps_min"], report["gpu_ms_max"], report["sync_ms_max"]), (6.5, 63.0, 43.49))
        self.assertEqual(report["live_texture_mb_max"], 3356)
        self.assertEqual(report["vram_over_allowance"], 1)
        self.assertEqual(report["ram_parked_events"], 1)
        self.assertEqual(report["fast_sync"], "off")
        self.assertEqual(report["fps_cap"], "30")

    def test_mirror_scan_telemetry(self):
        sample = "vk: mirror scan (1024 syncs, RX_VK_SYNC_EDGE_SKIP=1): 41000 inspected, 300000 clean skipped, 9.25 ms CPU scan"
        report = summarize(measures([sample]))
        self.assertEqual(report["edge_skip"], "on")
        self.assertEqual(report["scan_ms_median"], 9.25)
        self.assertEqual(report["scan_inspected_max"], 41000)
        self.assertEqual(report["scan_skipped_max"], 300000)

    def test_no_samples(self):
        report = summarize(measures(["unrelated entry"]))
        self.assertEqual(report["fps_count"], 0)
        self.assertEqual(report["vram_over_allowance"], 0)


if __name__ == "__main__":
    unittest.main()
