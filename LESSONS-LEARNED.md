# LESSONS-LEARNED.md

> **Status note (2026-10-09):** earlier content was a coding agent's private session notes (artifact paths, tool names) and claimed files and regression tests that did not exist. It has been replaced with project lessons.

## L1. Renames leave a long tail (#16)
Renaming feeldznutts → familia left the installer, docs, log prefixes and the logo pointing at the old name. Grep for the old name in code *and* docs, and replace assets in the same change.

## L2. Agent context must match the server slot (#19)
hermes-agent with compression off sent ~18–21k-token requests to a 16,384-token `coder` slot and looped on HTTP 400. Fix: declare both in `graph.yaml`, require `context_length` == per-slot ctx, and launch hermes through `scripts/hermes.sh` with compression on.

## L3. Escaped quotes break shell scripts silently (#14)
A stray `\"` left `android_start.sh` unparseable. Run `sh -n` / shellcheck in CI.

## L4. Never pack a small host's RAM (2026-10-09)
miryam (7 GiB) hard-hung when the 64k coder server, an embed test and a compaction self-test ran together. Keep `reserve_ram_mib: 3072`, ~2 GiB free after estimates, and one heavy process at a time. See `docs/ram-safety.md`.

## L5. SSH passwords
Use key-only SSH to the phones; the android scripts read addr/user/port from graph.yaml (or ANDROID_HOST/USER/PORT) and never take passwords or disable host-key checking (#18).

## L6. Use ASCII in names and code
Non-breaking hyphens (U+2011) in file names and Python expressions break copy-paste. Keep identifiers ASCII.

## L7. Android Vulkan needs the system loader
Termux's Vulkan loader only sees llvmpipe. llama.cpp finds the phone GPU (Xclipse 550) only when LD_LIBRARY_PATH holds both libvulkan.so and libvulkan.so.1 linked to /system/lib64/libvulkan.so; familia-start does this. On the A57, SmolLM2-135M Vulkan -ngl 99 gives tg 66-79 t/s against 30 t/s on 3 CPU threads (#34).

## L8. Phones drop off Wi-Fi during long runs
Both A57s left the LAN (no route to host) minutes into a detached benchmark. Take termux-wake-lock and keep the screen-off Wi-Fi policy in mind before long runs, write results to a log on the phone, and poll with backoff instead of holding one SSH session open.

## L9. Same hardware is not same software
phone7 had Termux llama-cpp 0.5.0 while a fresh install on phone8 pulled 0.6.0. Record the runtime version with every benchmark before comparing phones.

## L10. A small iGPU can be slower than the CPU
On miryam the HD 620 runs SmolLM2-135M at 46 t/s tg, versus 101 on 2 CPU threads. Its value is offloading the decision model so the CPU stays free for the coder. When both ran together, though, the Vulkan side fell from 46 to 17 t/s tg, while the CPU coder held about 14 t/s (#24).


## L11. Measure once, look it up afterwards (model + hardware registry)
Each tuning round re-learned facts we already had: the A57 Vulkan loader fix, the iGPU being slower than miryam's CPU, contention on shared memory. Every measured result now goes into `registry/records.jsonl` (append-only, labelled measured or estimated), and the hardware setup facts go into shareable `registry/hardware/` profiles. `registry.py suggest` proposes a placement from those records instead of a new sweep, and `match` gives identical hardware the known-good setup. Watts are spec-sheet upper bounds until measured. See `docs/model-registry.md`.

## L-miryam-perf. On a 2-core laptop, use 2 threads, and the iGPU costs RAM (2026-10-10)
llama-bench on miryam (i5-7200U, 2C/4T, HD 620), Qwen3.5-2B Q4_K_M, CPU only, fa on, 2 reps, spread shown as +/-:

| setting | pp256 t/s | tg32 t/s |
|---|---|---|
| b11374, -t 4 | 29.4 +/-1.3 | 5.86 +/-0.27 |
| b11540 CPU, -t 4 | 31.6 +/-1.7 | 5.82 +/-0.18 |
| b11541 (Vulkan build, -dev none), -t 4 | 30.6 +/-0.9 | 6.26 +/-0.34 |
| b11541, **-t 2** | 32.4 +/-0.4 | **8.44 +/-0.06** |

LFM2.5-1.2B Q4_K_M: -t 2 pp 50.7 / tg 17.1; -t 3 47.4 / 15.2; -t 4 49.3 / 14.2.

- **Threads = physical cores.** Hyperthreads add contention on the shared FPU and memory path: -t 2 is +35% decode for the coder (+20% for LFM) and slightly faster prefill. The coder node now sets `threads: 2`.
- **Builds:** b11374, b11540 and b11541 are within noise. The coder stays on b11374, which is verified for qwen35.
- **KV type** (-d 1024, tg): f16 / q8_0 / q4_0 for K and V all land within 6.3-8.0 t/s at -t 4. That is inside the -t 4 noise, because Qwen3.5 is hybrid and has few full-attention layers. q8_0 stays for the 64k config. fa off was no faster (6.8).
- **ubatch** 128 / 256 / 512 at b 512: 32.3 / 33.0 / 32.9 t/s pp. No change from the default.
- **mmap flag:** this build renamed `-mmp` to `-lm` (load_mode), so it wasn't swept.
- **CPU clock:** it sits at 2.5 GHz on all cores under load, down from 3.1 GHz idle turbo. That's the 15 W limit. no_turbo=0, and turbo can't be adjusted without root.
- **iGPU and RAM:** every Vulkan run of the 2B coder (op-offload with -ngl 0, or -ngl 99) dropped MemAvailable from about 3.2 to 2.2-2.6 GiB. That tripped the 3 GiB guard within seconds, so the runs were killed before they produced numbers. On a shared-memory iGPU the driver allocates its own buffers in addition to the mmapped weights. Under the 3 GiB-free rule, the coder can't use the iGPU on miryam at all. Smaller models (LFM, embed) are tested for iGPU roles separately.
- **iGPU clock cap:** gt_max_freq_mhz (1000 MHz, min 300) isn't writable without root, and intel_gpu_top isn't installed, so a capped iGPU clock wasn't tested.

