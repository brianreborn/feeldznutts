# SM11 quant + batch launch measurements (qodesh, GeForce 8600 GT)

Shape: n=288, d=768 (stories15M FFN-ish). Timing: QueryPerformanceCounter, 100 iters after warmup.
Weights registered resident for F32 path (no per-call W H2D).

## Correctness (max abs err vs CPU F32; y in [-16.7, 18.9])
| op | max_abs_err |
|---|---:|
| gpu F32 | 6e-6 |
| gpu Q4_0 (GGML nibble layout) | 0.491 (~2.6% of peak) |
| gpu Q8_0 | 0.035 |
| gpu batch3 | 6e-6 |

## Throughput / latency
| op | ms/call |
|---|---:|
| cpu F32 | 0.346 |
| gpu F32 resident | 0.495 |
| gpu Q4_0 (H2D quant W each call) | 3.463 |
| gpu Q8_0 (H2D quant W each call) | 3.935 |
| gpu batch3 (pipelined, 1 sync) | 1.236 |
| gpu 3x single (3 syncs) | 1.530 |
| batch3 speedup | **1.24x** (save 0.29 ms) |

Batch = persistent pool + pipelined `matvec_d` launches + single `cuCtxSynchronize`.
Q4/Q8 PTX: `k_q4_matvec`, `k_q8_matvec` (GGML block layout). API: `sm11_q4_matmul` / `sm11_q8_matmul`.
batch6_ms	2.237
3x2_single_ms	3.037
speedup6	1.357x
batch8_ms	2.959
8x_single_ms	4.115
speedup8	1.391x
