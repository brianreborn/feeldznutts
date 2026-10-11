# Small models alongside a pentest node: familia research (2026-10-10)
Web research only. Numbers are copied from the cited source. "unknown" means I found no documented figure. Third-party estimate sites are marked (est).

## 1. Translation
| Model | Memory | License | CPU/GPU | Source |
|---|---|---|---|---|
| NLLB-200-distilled-600M, CTranslate2 int8 | model.bin ~591 MB; runtime RAM unknown | CC-BY-NC-4.0 (non-commercial, "not for production") | CPU int8, or CUDA int8_float16 | huggingface.co/osa911/nllb-200-distilled-600M-ct2-int8 ; huggingface.co/facebook/nllb-200-distilled-600M |
| MADLAD-400 MT 3B | unknown (3B params, 32 layers) | not confirmed here | unknown | github.com/google-research/google-research/tree/master/madlad_400 |
| TranslateGemma 4B (GGUF) | Q4_K_M 3.5 GB / Q8_0 5.8 GB / FP16 10.4 GB (est) | Gemma Terms | CPU via llama.cpp, faster on GPU | fitmyllm.com/model/translategemma-4b |

## 2. TTS
| Model | Memory | License | CPU/GPU | Source |
|---|---|---|---|---|
| Kokoro-82M ONNX | files: fp32 310–326 MB, fp16 ~164–169 MB, int8 88–114 MB, plus voices 28 MB. Measured RAM: int8 ~170 MB, fp16 ~280 MB, fp32 ~540 MB | weights Apache-2.0; kokoro-onnx MIT; espeak-ng GPL-3 | CPU-only works (RTF 1.4x fp16 on a 2010 Xeon E5620; int8 was the slowest on CPU) | blog.nemesisnet.co.za/self-hosted-tts-with-kokoro-onnx… ; github.com/thewh1teagle/kokoro-onnx/releases ; huggingface.co/hexgrad/Kokoro-82M |
| Piper (VITS ONNX) | medium voice ~60–150 MB; high >500 MB; Pi 4 with 2 GB+ runs medium | piper1-gpl code GPL-3.0; license varies per voice | CPU (built for Pi 4) | pidiylab.com/text-to-speech-raspberry-pi-piper ; github.com/OHF-Voice/piper1-gpl |
| F5-TTS | unknown (not researched in depth) | unknown | needs GPU in practice (unverified) | n/a |

## 3. Speaker diarization / separation
| Model | Memory | License | CPU/GPU | Source |
|---|---|---|---|---|
| pyannote speaker-diarization-community-1 (pyannote.audio 4.x) | 72-min file: discrete_diarization peak 9.54 GB VRAM (3.3.2 used 1.59 GB). With embedding_batch_size=4: max_allocated ~0.46 GiB, reserved ~0.97 GiB | gated on HF (accept conditions); exact license not confirmed here | runs on CPU by default; GPU optional | github.com/pyannote/pyannote-audio/issues/1963 ; HF model README |
| pyannote 3.1 (legacy) | segmentation 0.40 GB, embeddings 0.05 GB, reconstruction 1.59 GB (same 72-min test) | same as above | CPU/GPU | same issue |
| WhisperX diarize, SepFormer, Demucs | unknown | unknown | unknown | not documented in the sources I found |

## 4. Vision input (VLM)
| Model | Memory | License | CPU/GPU | Source |
|---|---|---|---|---|
| SmolVLM(2)-256M | single image 0.8 GB VRAM; video 1.38 GB | Apache-2.0 (HF card) | GPU figures given; also runs in MLX/llama.cpp | arxiv.org/html/2504.05299v1 ; HF SmolVLM2-256M card |
| SmolVLM(2)-500M | image 1.2 GB; video 1.8 GB | Apache-2.0 | same | same |
| SmolVLM(2)-2.2B | image 4.9 GB; video 5.2 GB | Apache-2.0 | GPU recommended | same |
| Moondream 0.5B | int8 996 MiB / int4 816 MiB | Apache-2.0 | CPU-capable | pypi.org/project/moondream/0.0.6 |
| Moondream 2B | int8 2,624 MiB / int4 2,002 MiB | Apache-2.0 | CPU-capable, faster on GPU | same ; HF moondream-2b-2025-04-14-4bit |
| Qwen2.5-VL-3B | theoretical min INT4 1.44 GB / INT8 2.87 GB (real use ≥1.2x that) | Qwen Research License (non-commercial) | GPU preferred | HF Qwen/Qwen2.5-VL-3B-Instruct |
| Phi vision | unknown (not researched) | MIT (Phi family; not verified here) | — | — |

## 5. Image generation
| Model | Memory | License | CPU/GPU | Source |
|---|---|---|---|---|
| SD 1.5 (0.86B) | Q4 ~0.5 GB, FP16 1.72 GB (est, weights only). sd.cpp measured SD1.5 Q8: diffusion compute 559 MB + VAE 1664 MB | CreativeML Open RAIL-M | CPU possible but slow; GPU preferred | hardwarehq.io/models/sd-1.5 ; github.com/tetherto/qvac-ext-stable-diffusion.cpp/pull/31 |
| SD-Turbo / LCM-LoRA | unknown | — | — | — |
| SDXL-Turbo | FP32 ~11.5 GB, FP16 ~5.7 GB, INT4 ~1.4 GB (est) | Stability AI model license | GPU | aquanode.io/models/stable-diffusion-xl/sdxl-turbo |
| FLUX.1-schnell, stable-diffusion.cpp GGUF | diffusion weights q8_0 12,068 MB, q4_0/q4_k ~6,395 MB, q3_k 4,888 MB, q2_k 3,736 MB. Docs: "6GB or even 4GB VRAM". Issue log: T5 9,084 MB in RAM with clip-on-cpu; RAM spikes to ~13–15 GB during load | Apache-2.0 (schnell) | GPU plus big RAM | github.com/leejet/stable-diffusion.cpp/blob/cc734292/docs/flux.md ; issue #376 |
| SANA-0.6B | 9 GB VRAM standard; 4-bit <8 GB | NVIDIA license (check) | GPU | github.com/NVlabs/Sana/blob/08c656c3/docs/sana.md |

**Models built to swap or coexist:** sd.cpp `--offload-to-cpu`, `--max-vram -1` (keeps ~1 GiB headroom), and `--stream-layers` make "roughly 3–4x larger" models fit. Its time-share plan reloads params from disk. The sd-fit-params PR notes ~0.5 GiB CUDA context per GPU (docs/performance.md, PR #31). pyannote memory is set by the batch size.

## Part 2: Time-slicing on one GPU or iGPU
**Frameworks**
- llama.cpp router: `--models-max N` (default 4) evicts the least-recently-used idle model; `POST /models/load` loads one explicitly (tools/server/README.md). This is the best fit for familia because it is already our runtime.
- Ollama: `OLLAMA_KEEP_ALIVE` (set 0 to unload after each request) and `OLLAMA_MAX_LOADED_MODELS`.
- vLLM sleep mode: level 1 moves weights to CPU and drops KV; level 2 drops both; wake with `/wake_up?tags=weights|kv_cache` (docs.vllm.ai sleep_mode). It needs a modern GPU, so it is not usable on the 8600GT or HD620.
- CUDA MPS and unified memory: MPS needs Volta or newer, so it is irrelevant for qodesh's 8600 GT (my own knowledge, not sourced in this pass). Unified memory paging thrashes when the working set is larger than VRAM. Prefer explicit load and unload.
- Triton and LocalAI: they offer explicit model load/unload APIs. I did not verify details this pass.

**Scheduling (reasoning from familia measurements, not from sources)**
1. Keep only one heavy GPU model resident (VLM or image gen). Run Kokoro or Piper TTS, NLLB-ct2 int8 and pyannote on the CPU, pinned to cores the pentest node doesn't use. They are small, and CPU is the tier the user allows to be used heavily.
2. Swap when the modality changes, not per request. Batch image jobs together. Pre-warm the next model while the current one is in its tail.
3. On miryam's HD620, compute and decode share DRAM bandwidth, and we already measured that the iGPU loses on decode. Run there one at a time: never pair the iGPU with a CPU decode or with a pentest scan that is bandwidth-heavy. Use the iGPU only for prompt, embed, or VAE bursts.
4. On qodesh: the one-wait-per-token win (211 host syncs down to 1 per token) shows that sync count dominates. Avoid frameworks that sync per layer or per op. Run swaps between requests, never inside a decode loop.
5. RAM: keep fuzzy headroom (≥1 GiB plus 0.5 GiB CUDA context). Treat the sd.cpp load spike (weights sit in RAM and VRAM at the same time) as the real peak. Flux is out on small hosts.

**Alignment and false sharing**
- Give each model its own arena or allocator: separate processes, or separate ggml backends. Concurrent models then never share cache lines or pages with each other or with pentest tools.
- Pad shared host-side ring buffers (audio frames, SPSC queues) to 64 B. Use 128 B where adjacent-line prefetch exists (Intel).
- Allocate pinned (page-locked) staging buffers once at startup and reuse them. Don't re-pin on every swap.
- Use cgroup memory limits per service plus earlyoom/zram (matches familia #29).

## Recommended small-system default (voice and image, in and out)
| Role | Default | Where | Footprint (doc) |
|---|---|---|---|
| Voice out | Kokoro-82M ONNX fp16 (Piper low as fallback) | CPU, always resident | ~280 MB RAM |
| Speaker split | pyannote community-1, embedding_batch_size=4, short chunks | CPU, on demand | ~0.5–1 GiB (GPU number; CPU RAM unknown) |
| Translation | NLLB-600M ct2 int8 (non-commercial only); TranslateGemma-4B Q4 if a commercial-clean license is needed | CPU, on demand | ~0.6 GB / ~3.5 GB |
| Vision in | Moondream 0.5B int4 or SmolVLM-256M/500M GGUF | GPU if VRAM ≥1.5 GB, else CPU | 0.8–1.2 GB |
| Image out | SD1.5 Q4/Q8 via stable-diffusion.cpp with --offload-to-cpu --max-vram -1 | GPU, swap-in only | weights ~0.5–1 GB + VAE ~1.7 GB (Q8 measured) |
Run these under the llama.cpp router (models-max 1 on GPU) plus a systemd unit per CPU service. Total always-resident: about 0.3 GB. Peak with one swap-in: about 3 GB. The pentest node keeps priority through cgroups.

**Unknowns to measure (PGO hints):** WhisperX, Demucs and SepFormer memory; pyannote RAM on CPU; F5-TTS; MADLAD-3B; SD-Turbo and LCM; real RSS of each model on qodesh, miryam and the phones.
