# GTX 1650 / 4 GB VRAM optimization baseline

This document is for the **Leonitex** fork of Project ReLink. The goal is better **real rendered frame times** and fewer stutters on a Lenovo L340 Gaming with a GTX 1650 and 16 GB RAM, without sacrificing game correctness or risking saves. **No FPS gain has been demonstrated yet.** The laptop's exact CPU, installed GPU driver, and Vulkan feature support still need measurement.

## What upstream already implements

- Vulkan 1.3 renderer, shader preparation and caching, background shader loading, texture eviction and VRAM/Windows commit budgeting.
- **Quality preset: Minimum (4GB)** (`gpu/vk/vk_menu.cpp`): texture budget **2,200 MB**, GPU memory mirror **256 MB**, handheld profile, and 50% render resolution with Lanczos window scaling; it also enables 2x generated frames by default. These are settings, not evidence of 60 real FPS.
- **AMD FSR 3.1** on GPUs where its runtime starts, with a **Quality** render resolution choice (67% of output), plus the game's own upscaler. **NVIDIA DLSS requires an RTX GPU** and must not be assumed available on a GTX 1650.
- **30, smooth** mode in the launcher for machines that cannot sustain 60 real FPS. A stable 30 is often more useful than jumping between 20 and 55.
- The renderer may take a long first launch to prepare the shader/pipeline caches. Don't include this first launch in gameplay benchmarking.

**Warning:** Editing a graphics setting in the in-game menu can mark its quality preset **Custom** and clear the preset's explicit VRAM/mirror caps. When comparing Minimum (4GB) against a customized FSR setup, treat them as *different configurations*. Do not assume you are testing the same memory budget.

## Before changing rendering code

1. On the laptop, open **Windows PowerShell** in the repository folder and run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\gtx1650-hardware.ps1 -OutFile .\hardware-report.json`. Inspect the JSON first. It includes CPU, GPU and Windows/driver versions, **not** usernames or device serial numbers. Confirm actual dedicated VRAM separately with Windows Task Manager, Performance, GPU.
2. Confirm that the game can launch successfully on an up-to-date GTX 1650 driver. Record the Vulkan GPU chosen in the renderer log; don't assume mesh shaders work until verified on this exact driver. Make sure the game chooses the GTX 1650, not the Intel integrated GPU.
3. Build and launch ReLink using only your own compatible game files. **Never commit or upload game files, keys, dumps, save data, or shader caches to GitHub.**
4. Warm the shader caches, then use the **same save, location, route, camera path, display refresh rate, and duration** for all runs. Make at least three passes per configuration. Leave frame generation **off** and choose **Unlocked** FPS when comparing actual game-rendered FPS and input latency. Test the 30-smooth cap separately for playability. If you choose the Minimum preset and then switch frame generation off **in the in-game menu**, it becomes Custom and loses the preset's memory caps; for an apples-to-apples uncapped test, set the preset first, exit the game, and set `frame_generation=0` directly in `relink_options.ini` while it is closed, retaining `quality_preset=1` (verify the key from the saved file).
5. Record average FPS, 1% low FPS (if measured by a frame-time tool), worst visible stutters, render resolution, upscaler, preset, VRAM in use, and whether any scene geometry is missing or corrupt. Keep screenshots local unless they contain no private or copyrighted material you are not authorized to share.

### Suggested A/B configurations

| Run | Settings | What it tests |
| --- | --- | --- |
| A, upstream control | Latest unmodified upstream version; **Minimum (4GB)** preset; frame generation off; unlocked for benchmarking | Existing low-VRAM tuning and stability |
| B, upstream FSR | Same upstream version; **FSR Quality (67%)** if available; frame generation off; unlocked for benchmarking | Whether FSR improves the image/performance trade-off. Note preset may become Custom |
| C, fork (future) | Same route, resolution, and frame-generation policy as whichever upstream setting we choose | Whether our code changes actually help |

**Do not hard-code `RX_VK_VRAM_MB` yet.** An artificially low cap can force repeated texture evictions and *worse* stutter or missing scenery. The automatic budget and Minimum preset should be measured first.

### Vulkan log memory report

When you have a plain-text renderer log from a real gameplay session, run:

```powershell
python .\scripts\low_vram_log_report.py "C:\path\to\relink.log" --csv ".\vram-samples.csv"
```

The script reads only `vk: VRAM: ...` memory diagnostic lines and writes a CSV of memory samples if requested. No game data, private paths or graphics assets are included in the CSV. The parser reports usage and memory pressure, **not FPS**. Logs may include machine names, game paths, or error traces; review/sanitize before sharing.

For local parser tests:

```powershell
python -m unittest discover -s tests -p "test_low_vram_log_report.py" -v
```

## Change acceptance criteria

A renderer optimization is acceptable only when it **preserves visual correctness**, gives equal or lower memory pressure/stutter across repeated tests, and does not materially worsen CPU/RAM usage, startup, or driver compatibility. Use the upstream control on the **same machine**. Revert changes that only increase a headline FPS number by increasing input lag, hiding geometry, or repeatedly evicting active textures.

Target code for the next milestone after measurement: `gpu/vk/vk_texture.cpp` (VRAM allocation/eviction), `gpu/vk/vk_memory.cpp` (mirrors and imports), `gpu/vk/vk_main.cpp` (GPU features and selection), `gpu/vk/vk_framegen.cpp` (pacing), and `gpu/vk/vk_fsr.cpp` (upscaler). Test one subsystem at a time.
