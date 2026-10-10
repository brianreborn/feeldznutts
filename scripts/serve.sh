#!/bin/sh
# Launch a graph node's llama-server: sh scripts/serve.sh <node> [extra llama-server args]
# Memory cap (docs/ram-safety.md): FAMILIA_MEMCAP=1 wraps the server in a
# `systemd-run --user --scope` with MemoryHigh/MemoryMax and sets oom_score_adj 800,
# so on memory pressure the model dies, not the desktop. Default: on for miryam, off elsewhere.
# Override the limits with FAMILIA_MEMHIGH / FAMILIA_MEMMAX (systemd sizes, e.g. 2200M).
set -eu
node="${1:?usage: serve.sh <node> [args]}"; shift
here="$(cd "$(dirname "$0")/.." && pwd)"
args="$(python3 "$here/scripts/validate_graph.py" --graph "$here/graph.yaml" --args "$node")"
if [ -z "${FAMILIA_MEMCAP:-}" ]; then
  case "$(hostname)" in miryam*) FAMILIA_MEMCAP=1 ;; *) FAMILIA_MEMCAP=0 ;; esac
fi
# shellcheck disable=SC2086
if [ "$FAMILIA_MEMCAP" = 1 ] && command -v systemd-run >/dev/null 2>&1; then
  exec systemd-run --user --scope --quiet --unit="familia-$node-$$" \
    -p MemoryHigh="${FAMILIA_MEMHIGH:-2200M}" -p MemoryMax="${FAMILIA_MEMMAX:-2600M}" -p MemorySwapMax=0 \
    -- sh -c 'echo 800 > /proc/self/oom_score_adj; exec "$@"' sh $args "$@"
fi
exec $args "$@"