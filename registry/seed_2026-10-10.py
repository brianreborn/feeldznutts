#!/usr/bin/env python3
"""One-off seed: transcribes measured results already published in this repo
(LESSONS-LEARNED.md, gpu-legacy/*.md on feat/qodesh-legacy-gpu, graph.yaml notes,
#24/#34). Nothing here is new measurement. Run once; records.jsonl is append-only."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import registry as R

LG = "gpu-legacy/LESSONS-LEARNED.md@feat/qodesh-legacy-gpu"
I24 = "https://github.com/brianreborn/familia/issues/24"
I34 = "https://github.com/brianreborn/familia/issues/34"
SMOL = {"repo": "HuggingFaceTB/SmolLM2-135M-Instruct", "arch": "llama", "params": "135M"}
G84 = {"kind": "gpu", "name": "NVIDIA GeForce 8600 GT (G84, sm_11, 256 MiB)", "backend": "cuda-sm11-ptx", "driver": "341.92"}
ATH = {"kind": "cpu", "name": "AMD Athlon II X2 B24", "backend": "cpu"}
KBL = {"kind": "cpu", "name": "Intel Core i5-7200U", "backend": "cpu"}
HD620 = {"kind": "gpu", "name": "Intel HD Graphics 620", "backend": "vulkan", "driver": "Mesa 26.0.8"}
XCL = {"kind": "gpu", "name": "Samsung Xclipse 550", "backend": "vulkan", "driver": "SPAL 25.4.7"}
A57CPU = {"kind": "cpu", "name": "Exynos 1680 (3 Termux-visible cores)", "backend": "cpu"}
SM11 = {"name": "gpu-legacy smol_sm11 / run_sm11", "branch": "feat/qodesh-legacy-gpu"}
recs = []
def r(host, hw, dev, rt, model, settings, metrics, src, ts, correct=None, conc=None, note=None):
    recs.append({"host": host, "hardware_profile": hw, "device": dev, "runtime": rt, "model": model,
                 "settings": settings, "metrics": metrics, "concurrency": conc,
                 "correctness": correct, "timestamp": ts, "source": src, "notes": note})
# qodesh 8600 GT SmolLM2 arc (end-to-end tok/s, tg)
arc = [("2026-10-10T00:00-07:00", "per-op ggml hook, ~211 syncs/token", 4.49, 4.49, "BENCH-SMOLLM2-GPU.md", None),
       ("2026-10-10T00:30-07:00", "full forward on GPU, 1 wait/token, async+SPSC", 7.9, 7.9, LG, "32/32 vs CPU ref"),
       ("2026-10-10T01:05-07:00", "fusion without register prefetch (v3)", 9.53, 9.78, LG, "32/32 vs CPU ref, 4 prompts"),
       ("2026-10-10T01:12-07:00", "rmsnorm once per token", 9.86, 9.93, LG, "32/32 vs CPU ref"),
       ("2026-10-10T03:00-07:00", "v4 texture Q4, rows_per_thread=2", 12.86, 12.91, LG, "32/32 vs CPU, 3 prompts"),
       ("2026-10-10T05:00-07:00", "Q8 classifier via texture, MR4", 14.58, 14.58, LG, "32/32"),
       ("2026-10-10T06:00-07:00", "v6 per-shape MR tuned on rotating cold bench", 14.80, 14.83, LG, "32/32"),
       ("2026-10-10T09:30-07:00", "replay-tuned: 256-thread CTAs, 5 rows/thread", 15.31, 16.87, LG, "32/32 on all runs")]
for ts, s, lo, hi, src, c in arc:
    rt = {"name": "llama.cpp b11540 + ggml-sm11 hook"} if lo < 5 else SM11
    r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", G84, rt, dict(SMOL, quant="Q4_0", size_mib=87.4),
      {"ngl": 99, "step": s, "rows_per_thread": 5 if "5 rows" in s else (2 if "=2" in s else None)},
      {"tg_tps": {"min": lo, "max": hi, "measured": True}}, src, ts, c)
    recs[-1]["timestamp_approx"] = True  # order is from the tuning arc; exact clock time was not logged
r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", ATH, {"name": "llama.cpp b11540 win-cpu", "commit": "1e6f04a75"},
  dict(SMOL, quant="Q4_0"), {"threads": 1, "pin": "CPU0"}, {"tg_tps": {"min": 12.03, "max": 12.03, "measured": True}},
  "gpu-legacy/BENCH-SMOLLM2-GPU.md@feat/qodesh-legacy-gpu", "2026-10-10T00:00-07:00")
r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", ATH, {"name": "llama.cpp b11540 win-cpu"}, dict(SMOL, quant="Q4_0"),
  {"threads": 1, "pin": "CPU0"}, {"tg_tps": {"min": 10.59, "max": 10.59, "measured": True}},
  "gpu-legacy/BENCH-SMOLLM2-GPU.md@feat/qodesh-legacy-gpu", "2026-10-10T00:00-07:00",
  conc={"co_runner": "SmolLM2 GPU per-op offload", "co_runner_tps": 4.52})
st = {"repo": "karpathy/tinyllamas stories15M (llama2.c)", "file": "stories15M.bin", "arch": "llama2c", "quant": "fp32",
      "sha256": "cd590644d963867a2b6e5a1107f51fad663c41d79c149fbecbbb1f95fa81f49a", "size_mib": 57}
r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", G84, SM11, st, {"omp_threads": 2, "resident_mib": 57},
  {"tg_tps": {"min": 34.04, "max": 34.31, "measured": True}}, "gpu-legacy/bench-concurrency/SUMMARY.md@feat/qodesh-legacy-gpu",
  "2026-10-09T23:00-07:00", "stdout identical before/after async", note="best-of-3 era; idle-desktop runs later hit 57-71 t/s (desktop load, not code)")
r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", G84, SM11, st, {"omp_threads": 2}, {"tg_tps": {"min": 25.91, "max": 25.91, "measured": True}},
  "gpu-legacy/bench-concurrency/SUMMARY.md@feat/qodesh-legacy-gpu", "2026-10-09T23:00-07:00",
  conc={"co_runner": "llama-bench Q4_0 tg256 CPU0 -t1", "co_runner_tps": 69.74, "co_runner_alone_tps": 88.53})
r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", G84, SM11, st, {}, {"tg_tps": {"min": 33.33, "max": 33.33, "measured": True}},
  "gpu-legacy/bench-decision/SUMMARY.md@feat/qodesh-legacy-gpu", "2026-10-09T23:30-07:00",
  conc={"co_runner": "SmolLM2-135M Q4_0 CPU -t1", "co_runner_tps": 11.47, "co_runner_alone_tps": 11.95})
r("qodesh", "nvidia-g84-8600gt-athlon2x2-win10", G84, SM11, dict(SMOL, quant="Q4_0"), {"rows_per_thread": 2, "wait_mode": 1},
  {"tg_tps": {"min": 12.35, "max": 12.35, "measured": True}, "latency_ms": {"avg": 76.5, "max": 78}}, LG, "2026-10-10T04:00-07:00", "32/32",
  conc={"co_runner": "llama-bench stories15M Q4_0 -t1 CPU0", "co_runner_tps": 124.6})
# miryam
VK = {"name": "llama.cpp b11541 ubuntu-vulkan-x64 prebuilt", "commit": "f2918cabb"}
SQ = dict(SMOL, quant="Q4_0")
r("miryam", "intel-kbl-i5-7200u-hd620-linux", KBL, VK, SQ, {"threads": 2, "ngl": 0},
  {"pp_tps": {"min": 430.4, "max": 430.4, "measured": True}, "tg_tps": {"min": 101.4, "max": 101.4, "measured": True}},
  "graph.yaml hosts.miryam; " + I24, "2026-10-10T02:47-07:00", "identical output CPU vs Vulkan temp 0")
r("miryam", "intel-kbl-i5-7200u-hd620-linux", HD620, VK, SQ, {"ngl": 99},
  {"pp_tps": {"min": 320.0, "max": 320.0, "measured": True}, "tg_tps": {"min": 46.2, "max": 46.2, "measured": True}, "free_ram_min_mib": 4096},
  "graph.yaml hosts.miryam; " + I24, "2026-10-10T02:47-07:00", "identical output CPU vs Vulkan temp 0")
LFM = {"repo": "LiquidAI LFM2.5-1.2B", "arch": "lfm2", "quant": "Q4_K_M", "params": "1.2B"}
r("miryam", "intel-kbl-i5-7200u-hd620-linux", KBL, VK, LFM, {"threads": 3},
  {"pp_tps": {"min": 43.5, "max": 43.5, "measured": True}, "tg_tps": {"min": 13.9, "max": 13.9, "measured": True}}, I24, "2026-10-10T08:40-07:00")
r("miryam", "intel-kbl-i5-7200u-hd620-linux", KBL, VK, LFM, {"threads": 3},
  {"pp_tps": {"min": 26.9, "max": 26.9, "measured": True}, "tg_tps": {"min": 14.7, "max": 14.7, "measured": True}, "free_ram_min_mib": 3160},
  I24, "2026-10-10T08:40-07:00", conc={"co_runner": "SmolLM2 Q4_0 Vulkan -ngl 99 -t1", "co_runner_tps": 16.9, "co_runner_alone_tps": 45.8})
r("miryam", "intel-kbl-i5-7200u-hd620-linux", HD620, VK, SQ, {"ngl": 99, "threads": 1},
  {"pp_tps": {"min": 134.4, "max": 134.4, "measured": True}, "tg_tps": {"min": 16.9, "max": 16.9, "measured": True}, "free_ram_min_mib": 3160},
  I24, "2026-10-10T08:40-07:00", conc={"co_runner": "LFM2.5-1.2B Q4_K_M CPU -t3", "co_runner_tps": 14.7, "co_runner_alone_tps": 13.9})
# phones
SK = dict(SMOL, quant="Q4_K_M")
r("phone7", "samsung-a57-sm-a576u-exynos1680-android16", XCL, {"name": "Termux llama-cpp", "pkg": "0.5.0"}, SK, {"ngl": 99, "threads": 3},
  {"pp_tps": {"min": 823, "max": 1106, "measured": True}, "tg_tps": {"min": 66, "max": 78, "measured": True}}, I34, "2026-10-10T00:45-07:00", "output correct")
r("phone7", "samsung-a57-sm-a576u-exynos1680-android16", A57CPU, {"name": "Termux llama-cpp", "pkg": "0.5.0"}, SK, {"ngl": 0, "threads": 3},
  {"pp_tps": {"min": 42.7, "max": 42.7, "measured": True}, "tg_tps": {"min": 30.5, "max": 30.5, "measured": True}}, I34, "2026-10-10T00:45-07:00")
r("phone8", "samsung-a57-sm-a576u-exynos1680-android16", XCL, {"name": "Termux llama-cpp", "pkg": "0.6.0"}, SK, {"ngl": 99, "threads": 3},
  {"pp_tps": {"min": 1400, "max": 1406, "measured": True}, "tg_tps": {"min": 78.8, "max": 79.4, "measured": True}}, I34, "2026-10-10T08:40-07:00", "output correct")
out = os.path.join(os.path.dirname(__file__), "records.jsonl")
if os.path.exists(out): sys.exit("records.jsonl exists; seed is one-off (append with registry.py add)")
for x in recs:
    R.append(R.normalize(x), out)
print(len(recs), "records")
