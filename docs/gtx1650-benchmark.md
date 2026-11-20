# GTX 1650 / 4 GB VRAM optimization baseline

This document is for the **Leonitex** fork of Project ReLink. The goal is better **real rendered frame times** and fewer stutters on a Lenovo L340 Gaming with a GTX 1650 and 16 GB RAM, without sacrificing game correctness or risking saves. **No FPS gain has been demonstrated yet.** The laptop's exact CPU, driver, and Vulkan mesh-shader support have now been checked locally. Game launch and real performance still need measurement.

## Verified laptop hardware (November 20, 2026 UTC)

The local read-only hardware inventory reports **Intel Core i5-9300HF (4 cores / 8 threads, AVX2 supported by Intel's specifications)**, **GeForce GTX 1650**, **15.91 GB RAM**, **Windows 10 Pro build 19045**, and NVIDIA Windows driver **32.0.15.9579 (= 595.79)**. The subsequent local NVIDIA query confirmed **4096 MiB of VRAM** (595.79 driver). `vulkaninfo` completed successfully, reported **Vulkan API 1.4.329**, identified the **GTX 1650**, listed **`VK_EXT_mesh_shader`**, and reported **`meshShader=true`**. The tool warns that extension/feature flags can aggregate multiple GPUs, so the game must still confirm the actual Vulkan device it selects. **Do not commit the original hardware-report.json or game logs without reviewing them**.

For a second read-only GPU feature probe:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\gtx1650-vulkan-probe.ps1
```

This queries NVIDIA memory statistics through `nvidia-smi` if available and checks reported Vulkan and mesh-shader features if `vulkaninfo.exe` is installed. A missing Epic Online Services `EOSOverlayVkLayer-Win64.json` triggered a Vulkan loader **warning**, but this laptop's probe still succeeded; do not remove registry entries or install drivers solely because of that warning. Successful capability enumeration is not the same as proving ReLink itself initializes or renders correctly; inspect the actual ReLink GPU-selection log.

**Driver A/B control:** NVIDIA 621.24 was published November 12, 2026 and supports GTX 1650. Keep a baseline from installed 595.79 before changing drivers; do not confuse driver improvements with fork improvements.

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

When you have a plain-text renderer log from a real gameplay session, run the analyzer. **The game's log is named `relink_log.txt` in the installed game folder, not `relink.log`**; the previous four runs are rotated to `relink_log.1.txt` through `.4.txt`. These are written when ReLink starts from its launcher without a usable stderr stream (`host/hos_main.c`). The texture subsystem logs a `vk: VRAM:` diagnostic about once every 600 presented frames, so a very short run may have no samples.

Run:

```powershell
python .\scripts\low_vram_log_report.py "C:\path\to\your-game-folder\relink_log.txt" --csv ".\vram-samples.csv"
```

The script reads only `vk: VRAM: ...` memory diagnostic lines and writes a CSV of memory samples if requested. No game data, private paths or graphics assets are included in the CSV. The parser reports usage and memory pressure, **not FPS**. Logs may include machine names, game paths, or error traces; review/sanitize before sharing.

For local parser tests:

```powershell
python -m unittest discover -s tests -p "test_low_vram_log_report.py" -v
```

## First gameplay report: bright grass/Link flashes and stuttering

On the first successful ReLink launch (November 20, 2026), the user reported bright flashes affecting grass and Link, blinking grass, frequent stutters, and slightly lagging cutscenes. These are **observations**, not yet diagnosed renderer defects.

**Very close upstream reproduction:** [pixl27/ProjectReLink issue #143](https://github.com/pixl27/ProjectReLink/issues/143) (opened Nov 19, 2026) describes GTX-like NVIDIA laptop hardware (RTX 3050 Ti 4 GB) running v0.7.9.2, with grass and ground textures flashing around Link. The reporter says adding `RX_VK_FAST_SYNC=0` to the installed game's `relink_env.txt` eliminates the flicker, **but raises GPU time/frame**. This workaround is not yet confirmed on the GTX 1650 and may reduce performance.

**Controlled test (do not commit this setting as a renderer default):**

1. Capture a 1–2 minute run with existing settings; keep `relink_log.txt` and record if/when flashing and cutscene stalls happen. The game writes log files in its installed game folder by default.
2. Fully close the game and place **only** `RX_VK_FAST_SYNC=0` on a new line in `relink_env.txt` beside the installed game executable (keep any existing contents). Start game again and repeat the same route. Verify the log begins with `env: relink_env.txt read: RX_VK_FAST_SYNC=0` (possibly with other settings).
3. Compare visual flashing **and** perceived FPS/stutter. If the flicker disappears but gameplay is much slower, report both and revert this setting before testing other alternatives. If it persists, this is not the same issue or not the only cause.
4. Preserve original and new logs separately. Do not confuse first-run shader compilation with steady-state performance; do not compare incompatible render resolutions or generated FPS.
5. Later, test **30, smooth** cap and **frame generation off** as separate changes. The Minimum (4GB) preset itself enables generated frames; changing a setting *inside the game* can switch the preset to Custom and lose VRAM limits. For valid comparisons verify the resulting `relink_options.ini`.

**Privacy:** `relink_log.txt` may contain local paths or game content details. Review before uploading; never send game dumps, keys, or saves.

## Change acceptance criteria

A renderer optimization is acceptable only when it **preserves visual correctness**, gives equal or lower memory pressure/stutter across repeated tests, and does not materially worsen CPU/RAM usage, startup, or driver compatibility. Use the upstream control on the **same machine**. Revert changes that only increase a headline FPS number by increasing input lag, hiding geometry, or repeatedly evicting active textures.

Target code for the next milestone after measurement: `gpu/vk/vk_texture.cpp` (VRAM allocation/eviction), `gpu/vk/vk_memory.cpp` (mirrors and imports), `gpu/vk/vk_main.cpp` (GPU features and selection), `gpu/vk/vk_framegen.cpp` (pacing), and `gpu/vk/vk_fsr.cpp` (upscaler). Test one subsystem at a time.
