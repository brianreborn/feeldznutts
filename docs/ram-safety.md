# RAM safety (provisional guidance)

After miryam OOM'd and hard-hung (2026-10-09 PT) while coder (~3 GiB),
embed, and a long compaction self-test ran together, we do **not** aim for
high RAM utilization.

> **Status (2026-10-10):** the numbers below (`reserve_ram_mib`, the ~2 GiB
> small-host floor, the 3 / 3.5 GiB free targets used in benchmark guards) are
> **provisional, fuzzy guidance, not hard lines.** Reason: nobody has
> characterized idle memory load on our hosts yet (registry records of kind
> `idle-ram` are the first attempt), and no system-level protection (earlyoom,
> systemd-oomd, cgroup limits, zram) is deployed. Until both exist, the margins
> are a judgment call, and they should be revisited when the data and protections land.
> Under-using RAM is preferred to idle CPU/iGPU only up to the point of risk;
> brushing a target (e.g. 3.43 GiB vs 3.5) is within guidance.

## Guidance

1. **Reserve for the OS and companions.** On miryam (`ram_mib: 7270`),
   `reserve_ram_mib` is **3072** (provisional) so the OS, hermes-agent,
   browser and SSH keep headroom.
2. **Aim for ~2 GiB free after estimated node use on hosts under 8 GiB**
   (weights + KV + 256 MiB overhead + `cache_ram_mib` + draft weights).
3. **Prefer one heavy server at a time on miryam.**
4. **Validate against the target host's measured `ram_mib`.**

## What the validator does

| Check | Result |
|---|---|
| `estimated_used > ram_mib` | **ERROR**: clear overcommit, fails. |
| `estimated_used + reserve_ram_mib > ram_mib` | WARNING (provisional margin). |
| `ram_mib < 8192` and `ram_mib - estimated_used < 2048` | WARNING (provisional small-host floor). |

## Baseline numbers (miryam)

| Placement | Est. use | Free after est. | With reserve 3072 |
|---|---|---|---|
| coder 64k alone | ~2928 MiB | ~4342 MiB | no warning |
| coder + embed | ~3479 MiB | ~3791 MiB | no warning (tight) |

## Draft system-level protections (NOT deployed: each needs the user's OK)

All need root on miryam. Nothing below has been run. Proposed in order of value.

### 1. earlyoom (kill the biggest *model* process before the desktop freezes)
```
sudo apt install earlyoom
sudo tee /etc/default/earlyoom >/dev/null <<'EOF'
EARLYOOM_ARGS="-m 8,4 -s 10,5 -r 60 --prefer '(^|/)(llama-server|llama-bench|llama-cli)$' --avoid '(^|/)(gnome-shell|Xwayland|sshd|systemd|grok-bot)$' -n"
EOF
sudo systemctl enable --now earlyoom
```
(`-m 8,4`: SIGTERM at <8% available, SIGKILL at <4%; only the preferred regex is targeted first.)

### 2. Alternative: systemd-oomd (Ubuntu ships it; do not run both with earlyoom)
```
sudo mkdir -p /etc/systemd/oomd.conf.d
sudo tee /etc/systemd/oomd.conf.d/familia.conf >/dev/null <<'EOF'
[OOM]
SwapUsedLimit=90%
DefaultMemoryPressureLimit=60%
DefaultMemoryPressureDurationSec=20s
EOF
sudo systemctl restart systemd-oomd
```
It only acts on cgroups with `ManagedOOMMemoryPressure=kill`, which the wrapper below sets.

### 3. cgroup wrapper for llama-server (no root needed once user lingering/delegation works)
```
systemd-run --user --scope -p MemoryHigh=2200M -p MemoryMax=2600M -p MemorySwapMax=0 \
  -p ManagedOOMMemoryPressure=kill -p OOMScoreAdjust=800 \
  -- llama-server <args from: python3 scripts/validate_graph.py --args coder>
```
`MemoryHigh` throttles and reclaims, and `MemoryMax` kills only this server. Size it from the node estimate plus about 15%.
Note: page cache from mmapped weights counts toward the cgroup. Test once before relying on it.

### 4. OOM score for model processes (fallback, no root needed to raise your own)
```
echo 800 > /proc/<llama-server pid>/oom_score_adj     # makes the kernel pick it first
```

### 5. zram swap (cushion for spikes; miryam has only a 15 MiB swap)
```
sudo apt install zram-tools
echo -e "ALGO=zstd\nPERCENT=25\nPRIORITY=100" | sudo tee /etc/default/zramswap
sudo systemctl restart zramswap
cat /proc/swaps
```
