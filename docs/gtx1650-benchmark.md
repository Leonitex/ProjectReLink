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

## First three captured runs: quantitative findings

Three **local** logs from official upstream **v0.7.9.2**, collected after first install, were analyzed on November 21, 2026. **Raw game logs are deliberately not committed to this public fork.** Their actual option settings were not captured, so the comparisons are not an A/B benchmark of graphics presets.

| Local run | Evidence | Interpretation |
| --- | --- | --- |
| `relink_log.2.txt` | Shader preparation interrupted after about 893 of 38,809 shaders; no gameplay FPS or VRAM samples | Incomplete shader preparation, not useful for performance comparison |
| `relink_log.1.txt` | Startup shader stage took 1369.1 seconds; 151 shader translation failures recorded; 5-second presented FPS observations eventually reached 19.6; peak sampled VRAM usage 1002 MB | Mostly preparation/light scenes, before heavy gameplay. Translation failures require further investigation if missing graphics recur |
| `relink_log.txt` | Shader startup took 94.5 seconds; Vulkan selected **GTX 1650** with mesh shaders; AMD FSR 3.1.4 available; fast sync enabled; 5-second presented FPS fell to **9.4–9.7** at the end; highest reported GPU time sample **83.4 ms/frame**; high scene draw counts (up to 2219/frame) | Severe real rendering workload plus probable memory pressure; not just a slow first-time shader startup |

**VRAM observations in `relink_log.txt`:** the highest diagnostic observed **3917 MB GPU memory used vs 3361 MB driver-reported allowed**, **2337 MB of textures vs 1680 MB effective texture budget**; additional high-pressure snapshots include **3601/3361 MB** and **3887/3361 MB**. The budget shrank as the scene grew, and textures were repeatedly retired to release memory. These measurements are evidence of memory pressure, *not* proof that it alone causes every stutter. Driver budget/usage values are dynamic and are not equivalent to an independent hardware VRAM profiler.

**Late-scene GPU samples** were generally ~40–83 ms/frame, corresponding to a GPU throughput limit of roughly 12–25 frames/s at those sampled times. CPU-side memory sync and replay also took significant time in at least one report (~34.75 ms sync / ~57.65 ms submit), so simply reducing render resolution may not eliminate all stalls. Reported private commit reached ~17 GB, with ~3.9 GB Windows commit headroom remaining (distinct from physical resident RAM). Across all sampled present-interval buckets in that run, about 3,989 of 13,053 presented intervals (**30.6%**) exceeded 40 ms. Note that *presented* FPS is not necessarily real game-rendered FPS if frame generation was enabled; the exact settings were not attached.

**Visual glitch:** the log records active fast sync (`vk: fast sync: the exposure meter is met...`), which makes upstream [issue #143](https://github.com/pixl27/ProjectReLink/issues/143) a close match to the reported bright flashing grass/Link. This remains a hypothesis until A/B tested with `RX_VK_FAST_SYNC=0`. There is **no confirmed Vulkan device-loss error** in these logs; the `device lost diagnostics...` startup line only reports supported debugging features.

**Next controlled runs:** (1) keep all graphics settings unchanged, apply only `RX_VK_FAST_SYNC=0` in `relink_env.txt`, compare flashes, FPS, memory, and logs; (2) after reverting/recording that result, compare the `Minimum (4GB)` preset with generated frames off, checking memory caps remain active. Compare locations and warm caches; do not impose a lower `RX_VK_VRAM_MB` cap without evidence. A 30-FPS cap cannot rescue a scene already running at ~10–20 FPS.

## Fast-sync-off run (uploaded as `relink_log(1).txt`)

This run **does** show `env: relink_env.txt read: RX_VK_FAST_SYNC=0`; the shader/pipeline cache was warm (startup **5.7 seconds**) and the GTX 1650 remained selected. It also shows a **30 FPS smooth cap (HOS_FPS_CAP=30)**, **unlike** the prior `relink_log.txt` baseline, which had no such cap. Therefore these logs are *not* a controlled fast-sync-only A/B test. The user reported some flashing still, but less than before, and explicitly prefers performance to fewer flashes.

| Fast-sync-off observation | Value |
| --- | --- |
| Minimum five-second presented-FPS sample | **6.5 FPS** near end |
| Worst sampled GPU time per frame | **100.0 ms** |
| Renderer texture residency early (1200 presents) | **131 MB / 123 textures** |
| Renderer texture residency late (1680 presents) | **3356 MB / 1468 textures** |
| Renderer per-frame submission (1560-present sample) | **106.93 ms**, including **69.76 ms memory sync** |
| Late sampled draw count | **1631 per frame** (1560-present interval) |

The first two periodic `vk: VRAM:` reports in this short run were only **1031/3364 MB** and **1159/3364 MB**, during relatively lightweight scenes; **do not misstate these as the peak game VRAM use**. The log does not include a later total-VRAM snapshot. The late **3356 MB** is explicitly **texture memory**, not total GPU VRAM.

Next diagnostic priority: **restore default fast sync** (delete its opt-out line) if the user wants maximal performance; **read/review `relink_options.ini`** to see the actual preset, scaling, framegen and cap; benchmark the same scene with warmed caches and a single fixed set of graphics options (baseline 4GB preset and 30-FPS cap tested separately). The severe slowdown is real even with fast sync off. Measure GPU vs CPU-side memory-sync work before changing mirror/texture reclamation policy. Avoid claiming the 30 FPS cap caused the slowdown (it limits the ceiling, but cannot explain the ~6-10 FPS samples on its own).

## RAM texture offload and first opt-in renderer experiment

**Already upstream:** `gpu/vk/vk_texture.cpp` parks *some GPU-rendered textures* in **system memory** before evicting their Vulkan image (`park_texture` and `park_restore`). With 16 GB of host RAM the default `RX_VK_PARK_MB` cap is **1024 MiB** (min of 1024 MiB and RAM / 16); it declines to park when Windows commit is short. Textures whose original compressed bytes are still present in guest memory can be reconstructed instead of kept as duplicate full-resolution GPU images. ReLink also imports and mirrors guest buffer memory separately. It is **incorrect** to claim every active GPU texture can be moved to system RAM without a frame-time penalty. GPU readback / reupload / page faults can introduce more stalls, and the GTX 1650's PCIe 3.0 link has much lower bandwidth than local GDDR5.

**Why not force extra RAM parking now:** the user has 16 GB physical RAM, while a prior run logged 17 GB process private commit and limited system commit headroom. Raising the parking cap to 2–4 GB could increase Windows pagefile pressure and worsen stutters. Keep the default parking cap until benchmark data shows otherwise. Also do **not** lower `RX_VK_VRAM_MB` blindly, as repeatedly reloading hot textures reduces performance.

**First experimental source improvement, branch-only:** `gpu/vk/spare_pressure.h` and `gpu/vk/vk_texture.cpp` now implement an **opt-in early release of unused Vulkan *spare images***. It is not a new RAM texture cache. Setting `RX_VK_SPARE_SOFT_PCT=85` on a build compiled from this branch will, once Vulkan reports >=85% of the driver's memory allowance in use, release eligible unused spare images that have been idle for >=60 presents. Images still being used, and newly retired images likely to be reused, are not selected by this extra policy. Existing retirement safety and destruction caps remain. The option is **off by default**; on an unmodified upstream binary the setting has no effect. Reclaiming old spares may lower VRAM pressure, *or* cause extra allocations and lower performance; run a controlled A/B comparison before retaining it. A standalone C++ helper test passes with g++ C++17; **a complete Windows build and gameplay test remain unverified**.

For a compiled fork, preserve whichever fast-sync setting you want to test and compare otherwise identical runs with no `RX_VK_SPARE_SOFT_PCT` and with:

```ini
RX_VK_SPARE_SOFT_PCT=85
```

Log markers to compare include `experimental spare reclaim`, `vk: images:`, `vk: VRAM:`, GPU time, CPU replay time (`memory sync`), and 5-second presented FPS. The choice to leave `RX_VK_FAST_SYNC=0` enabled is the user's current preference; do not silently remove it while running tests. The A/B routes must match, and the current run's **30-FPS cap** needs to be held constant or separately tested.

A new stdlib-only CLI `scripts/relink_performance_report.py` compares renderer-reported performance indicators:

```powershell
python .\scripts\relink_performance_report.py "C:\Users\Scott\Games\ReLink\relink_log.txt" "C:\Users\Scott\Games\ReLink\relink_log.1.txt"
```

The script reads logs only, does not expose paths from their contents, and does **not** equate generated/presented FPS with real rendered FPS. Python parser tests are in `tests/test_relink_performance_report.py`; isolated C++ policy tests in `tests/spare_pressure_test.cpp`.

## User's actual graphics options (uploaded 2026-11-21)

The supplied `relink_options.ini` contains only 13 settings, **no explicit quality-preset/memory-cap keys**. ReLink's defaults apply for absent keys. Verified against `launcher/Settings.cs`, `launcher/Home.cs`, `gpu/vk/upscaler_rows.h`:

- `resolution=1`: Native / **100% 3D render resolution** (costly on the GTX 1650). ReLink's logs indicate game output 2048x1152, desktop swapchain 1920x1080.
- `dlss=0`: the game's own upscaler, *not* AMD FSR; `dlss=3` selects AMD FSR.
- `frame_rate=2`: **30 FPS smooth cap**; do not infer this causes the observed 6-10 FPS (cannot sustain the cap in heavy scenes).
- `frame_generation=0`, `frame_pacing=0`, `v-sync=0`: all disabled.
- `handheld_profile=0`: docked. Enabling it later is a separate performance experiment.
- `upscaling=0`: **window scaling filter** (simple), *not* the AMD FSR selector.
- `sharpness=0`: no extra sharpening.

**First controlled settings test on official v0.7.9.2:** change exactly `resolution=1 → resolution=3` (**67%, FSR Quality**) and `dlss=0 → dlss=3` (AMD FSR), keeping the user's preference `RX_VK_FAST_SYNC=0`, existing 30 FPS cap, and all other values unchanged. The linked local test ini is delivered to the user separately, not checked into GitHub, to avoid overwriting user preferences. The estimated rendered 3D pixel area is ~45% of native; **this is not a measured FPS increase**, because GPU upscaler overhead, VRAM, CPU-side replay and memory sync still matter. If not enough, next test is `resolution=4` (50% FSR Performance), or `handheld_profile=1`, **one change at a time**. ReLink's own menu suggests optional `sharpness=80` with FSR; leave sharpness at 0 for the first controlled test.

Keep a backup and compare the *same* heavy scene with a warmed cache. The official `relink_options.ini` does not specify a 4GB preset; the in-game Quality preset changes memory caps, render resolution, framegen and profile together and would confound this first A/B experiment. Do not combine it with this test. Raw logs and local file paths should not be committed.

## Change acceptance criteria

A renderer optimization is acceptable only when it **preserves visual correctness**, gives equal or lower memory pressure/stutter across repeated tests, and does not materially worsen CPU/RAM usage, startup, or driver compatibility. Use the upstream control on the **same machine**. Revert changes that only increase a headline FPS number by increasing input lag, hiding geometry, or repeatedly evicting active textures.

Target code for the next milestone after measurement: `gpu/vk/vk_texture.cpp` (VRAM allocation/eviction), `gpu/vk/vk_memory.cpp` (mirrors and imports), `gpu/vk/vk_main.cpp` (GPU features and selection), `gpu/vk/vk_framegen.cpp` (pacing), and `gpu/vk/vk_fsr.cpp` (upscaler). Test one subsystem at a time.
