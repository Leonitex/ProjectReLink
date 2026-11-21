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

## FSR Quality + area-transition stress test (uploaded `relink_log(2).txt`)

The user deliberately entered a new, heavier area. The installed executable remains official **v0.7.9.2**; fast sync is still explicitly **off**. The log conclusively shows **AMD FSR 3.1.4 in active use**, with 3D render size **1366x768** upscaled to **2048x1152** (`vk: AMD FSR draws OoT's upscale`); 30 FPS smooth cap remains. Shaders were warm (**3.3 s** startup). Thus the first FSR test *did apply*, but lowering render resolution alone did not make the area playable.

At the highest sampled memory pressure (about 1184 presents): **4732 MB GPU memory used / 3285 MB driver allowance**, **3327 MB textures / 1564 MB dynamic texture budget**, **0 spare images**, **0 recycled** against **2640 new images made**; images included approx. **2016 MB render targets** and **1408 MB others** (these are separate VMA categories, do not sum blindly with texture counts). **2391 MB of texture data was used during the previous eight presents**, limiting how aggressively we can evict without thrashing. Host working set **9915 MB**, process private commit **17431 MB**, **3359 MB system commit left**. Peaks later: **117.5 ms GPU time per frame** and **126.01 ms CPU-side submission, 78.44 ms of that memory sync**. At the end FPS was **8.1 over 5.1 s**, and heavy-scene samples ranged roughly 7–19 FPS. The **3.0 FPS** absolute lowest five-second sample occurred at initial area loading, **before FSR was logged as in active gameplay**; it is a transition stall, not a representative steady heavy-scene average. The driver-reported used amount may exceed physical VRAM because memory can be paged; it is not proof 4.7 GB was physically resident on a 4 GB card.

**Implication for the experimental branch patch:** the new `RX_VK_SPARE_SOFT_PCT` patch only releases aged *spares*; this scene had **zero spares at its worst memory spike**, so it cannot plausibly fix this particular bottleneck alone. Source-level improvements should instead investigate scene-load render targets, active-texture residency, mirror/writeback synchronization, and high draw-call cost. Do not claim the first patch improved frame times without a compiled benchmark.

**CORRECTION (verified 2026-11-21):** the previously supplied INI contained `preset=1`, which is **NOT a recognized option**. It was ignored and the later test **was not a valid 4GB-limit experiment**. `ini_key()` derives the key from the menu row name `Quality preset`, so the correct option is **`quality_preset=1`**. The corrected INI is `relink_options_gtx1650_fsr_quality_4gb_cap_CORRECTED.ini`. For an actual A/B, keep FSR Quality, 30 FPS cap, frame generation off, fast sync disabled, all else unchanged; add only `quality_preset=1` and compare the same camera path after warming caches. On loading, `sync_preset_budgets(1)` establishes nominal limits of **2200 MB textures** and **256 MB mirrors**. This is an experiment that can worsen thrashing and performance; revert by removing `quality_preset=1`. Selecting the 4GB preset in the menu additionally changes other graphics settings and is not an isolated test.

## Wall / open-field camera stress test (`relink_log(3).txt`)

The user tested running around a tree, facing a wall and running into an open view. They observed noticeably higher FPS at the wall and lower FPS facing open terrain. ReLink **v0.7.9.2** was running **FSR Quality 1366x768 -> 2048x1152**, **30 smooth cap**, **frame generation off**, and **RX_VK_FAST_SYNC=0**; the supplied INI for this run included **`preset=1` (ignored)**, therefore **no 4 GB preset limit was in force**. Do not report this run as success or failure of the 4 GB preset.

Selected renderer performance samples from this run (not timestamped to actual wall/open camera direction):
- light sample at ~1440 presents: **238 draws**, GPU **21.1 ms**, reported renderer FPS **22.9**, CPU replay submit **21.94 ms**, memory sync **13.19 ms**;
- moderate sample at ~1200 presents: **533 draws**, GPU **47.5 ms**, renderer FPS **17.7**, CPU submit **49.03 ms**, memory sync **30.19 ms**;
- very heavy sample at ~960 presents: **2502 draws**, GPU **122.2 ms**, renderer FPS **7.4**, CPU submit **129.42 ms**, memory sync **88.97 ms**.

Max reported VRAM use **4385/3283 MB**, at a different periodic sample. Other VRAM reports **4027/3283 MB** and **4143/3283 MB**. The dynamic texture budget was squeezed to ~1.4–1.5 GB but textures in use were 2.1–2.9 GB. The driver repeatedly placed images in system memory due to **full VRAM**. **Zero spare images** were present at several memory reports, so `RX_VK_SPARE_SOFT_PCT` cannot substantially solve this scene. The ~10 GB process working set and ~17 GB private commit further discourage forcing additional RAM parking.

This confirms **view-dependent draw count, GPU work, and CPU-side memory synchronization** are major bottlenecks. Without frame-level camera markers the wall/field mapping is a plausible interpretation, not an exact trace correlation. Like-for-like FSR-only `relink_log(2).txt` was a different route, so apparent aggregate FPS changes do not establish a VRAM-cap benefit. **The next controlled test must use the corrected `quality_preset=1` key**, or if that worsens performance, revert and test `handheld_profile=1` separately. Avoid experimenting with 2–4 GB additional RAM parking given process commitment.

## Corrected 4GB memory cap: repeated wall/open view (user `relink_log(6).txt`)

The test finally used the **correct** `quality_preset=1` key, while preserving **AMD FSR Quality** (`dlss=3`, `resolution=3` = 1366x768 -> 2048x1152), **30 FPS smooth** (`frame_rate=2`), **zero generated frames**, docked profile and `RX_VK_FAST_SYNC=0`. The installed binary remains **official v0.7.9.2**: these measurements **do not test the renderer changes in our branch**. Preset activation was confirmed by the diagnostic **2200 MB texture-budget starting value** and **256 MB GPU mirror limit**.

| Diagnostic | Uncapped wall/open test `relink_log(3).txt` | Corrected-cap test `relink_log(6).txt` |
| --- | ---: | ---: |
| Median 5s presented-FPS (samples with >=1200 presents) | 10.05 | 11.10 |
| Last 5s presented-FPS sample | 9.4 | 10.2 |
| Peak sampled total GPU memory used | 4385 MB / 3283 MB allowed | 4269 MB / 3284 MB allowed |
| Peak sampled GPU time / frame | 122.2 ms | 104.3 ms |
| Peak sampled CPU-side memory sync | 88.97 ms | 70.68 ms |
| Max GPU buffer mirror residency | 480 MB | **256 MB** |
| Most demanding sampled draw count | 2502/frame | **3005/frame** |
| Active texture snapshot at highest VRAM use | 2869 MB (budget 1458 MB) | **3069 MB (budget 1797 MB)** |
| Warm-cache startup | 5.5 s | 5.2 s |

The medians are **not** per-frame synchronization of the same camera view; scenes and load timing vary, and the corrected run had 2649 presents rather than 2256. The cap yields some promising lower peak use and lower sampled GPU/CPU cost, but **is not a validated reproducible FPS improvement**. **Both exceed driver VRAM allowance badly**, and open terrain still commonly runs around 7–12 FPS. In the cap run, a 3005-draw sample consumed **104.3 ms GPU / 111.94 ms CPU replay / 70.68 ms memory sync**. Even the limit cannot evict active textures without causing thrash and blank patches; shadows, framebuffers and render targets count outside the texture budget. There were further `VRAM full:` fallback allocations in system memory.

**Do not further reduce texture or mirror caps blindly.** Aged spare-image reclaim has low impact when there are zero spares. Next **single-variable** diagnostic: copy the corrected INI, change **only** `handheld_profile=0` to `handheld_profile=1`. ReLink's v0.7.9.2 source says Handheld uses a 1536x864 game output, reducing FSR Quality's render size approximately to 1024x576; this may reduce render-target pixel cost but not per-draw CPU work. Keep the 4GB cap, FSR, frame cap, framegen and fast-sync unchanged. The user-facing file is `relink_options_gtx1650_4gb_handheld_test.ini`. Compare the same wall/tree/open route, give a qualitative smoothness judgement, preserve both logs; revert if visibility or FPS worsens.

This result shifts our source priority to **view-dependent high draw counts + costly memory sync** (rather than parked texture RAM size alone), while retaining the VRAM pressure safeguards. Work toward cutting redundant per-draw operations, avoiding GPU/CPU synchronization, render-target reuse, and accurate matched-scene benchmarking; don't claim code-speedup until custom DLL is built and tested.

## Handheld FSR Quality + corrected 4GB caps (`relink_log(7).txt`, 2026-11-21)

The user ran the same type of wall/tree/open-scene route. The official v0.7.9.2 log confirms **handheld 1536x864 game output**, **FSR Quality at 1024x576 3D internal resolution** (`vk: AMD FSR draws OoT's upscale`), **30 FPS smooth cap**, **frame generation off**, and `RX_VK_FAST_SYNC=0`. `quality_preset=1` remained in use: initial dynamic texture budget was 2200 MB, and logged buffer mirror residency was **256 MB**. Startup shaders took **3.0 seconds** (warm cache).

| Metric | Corrected capped Docked (`relink_log(6).txt`) | Capped Handheld (`relink_log(7).txt`) |
| --- | ---: | ---: |
| Median 5-second presented-FPS after 1200 presents | 11.1 (22 samples) | **13.4 (26 samples)** |
| Last five-second FPS sample | 10.2 | **11.5** |
| Peak sampled Vulkan GPU time/frame | 104.3 ms | **82.7 ms** |
| Peak sampled CPU memory-sync time/frame | 70.7 ms | **56.34 ms** |
| Peak reported GPU-memory use | 4269 MB | **4027 MB** |
| Driver memory allowance (high pressure snapshots) | ~3284 MB | ~3279 MB |
| Highest demanding-scene sampled draw count | 3005/frame | 2810/frame |
| Example >2600-draw sample | 3005 draws, 8.5 FPS, 104.3 ms GPU, 70.7 ms sync | 2810 draws, 12.0 FPS, 73.7 ms GPU, 47.56 ms sync |

Additional draw-count-binned evidence (not exact matched frames; bins are coarse and short, so do not claim an exact benchmark speedup):
- 1000–1799 draws/frame after 1200 presents: Docked 11.4 FPS, 72.7 ms GPU, 49.1 ms memory sync (3 samples); Handheld **13.1 FPS, 66.7 ms GPU, 44.9 ms sync** (5 samples).
- 1800–2599 draws/frame: Docked 10.4 FPS, 84.0 ms GPU, 60.4 ms sync (3); Handheld **12.1 FPS, 73.5 ms GPU, 49.0 ms sync** (3).

**Caveat:** FPS samples include different camera positions / scene loading; no frame-level user camera markers exist and run lengths differ (2649 vs 3095 presents). Roughly **21% higher median sample FPS** is a promising association with Handheld, **not** a controlled hardware performance claim. 30 FPS remains unattainable in heavy outdoor views.

**Remaining constraint:** the Handheld run's VRAM reports were **4027/3279**, **3687/3279**, **4006/3279**, and **3961/3284 MB**, with **texture-cache snapshots ~2.2–2.8 GB above ~1.65–1.78 GB effective budget**. ReLink logged images allocated in **system memory because VRAM was full**. Image recycling reports repeatedly contained **zero spare images**, so branch-only `RX_VK_SPARE_SOFT_PCT` is unlikely to help these scenes. CPU-side synchronization peaked **56.34 ms per frame** and was often 20–55 ms; this still scales with draws.

**Next recommendation:** retain Handheld+FSR Quality+corrected 4GB cap as the best observed **performance-first configuration**, subject to the user's judgement of picture clarity / actual smoothness. Do not pile on `RX_VK_WB_LAZY`, additional RAM parking, or tighter memory caps without A/B evidence. Start profiling/debugging the fork's **per-draw Vulkan replay, buffer-mirror dirty-page sync/writeback, renderer resource allocation, and render-target reuse**. Build an experimental DLL and A/B with the *same* scene; the current logs are **from the official binary only**. One optional single-variable graphics experiment is Handheld+FSR Performance (50%); diminishing returns expected if CPU memory sync is dominant.

## Change acceptance criteria

A renderer optimization is acceptable only when it **preserves visual correctness**, gives equal or lower memory pressure/stutter across repeated tests, and does not materially worsen CPU/RAM usage, startup, or driver compatibility. Use the upstream control on the **same machine**. Revert changes that only increase a headline FPS number by increasing input lag, hiding geometry, or repeatedly evicting active textures.

Target code for the next milestone after measurement: `gpu/vk/vk_texture.cpp` (VRAM allocation/eviction), `gpu/vk/vk_memory.cpp` (mirrors and imports), `gpu/vk/vk_main.cpp` (GPU features and selection), `gpu/vk/vk_framegen.cpp` (pacing), and `gpu/vk/vk_fsr.cpp` (upscaler). Test one subsystem at a time.
