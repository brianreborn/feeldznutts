# Heavyweight-model escalation (semi-automatic)

The light node (e.g. `qodesh-smol-cpu`, SmolLM2) handles everything by default.
When a session looks stuck, the router can swap in a heavier model, then swap back.

## Graph fields (per node, optional)

```yaml
escalates_to: [coder, qodesh-resident]   # ordered fallback list; may be on other hosts
escalation:
  mode: suggest        # off | suggest (default) | auto
  triggers:            # all optional; defaults shown
    repeat_outputs: 3  # N (near-)identical consecutive outputs
    similarity: 0.9    # token-set Jaccard counted as near-identical
    failure_retries: 3 # failed tool calls / tests
    phrases: ["try harder", "escalate", "use the big model", "heavier model"]
    tags: ["hard", "multi-file"]
    time_budget_s: 600
```

Validation (`scripts/graph_types.py` -> `escalation.check_node_escalation`): targets
must exist, no self/duplicate targets, no cycles, known mode/trigger keys, and
suggest/auto need at least one target. Cross-host targets are allowed and are
reported as `crosses_host: true`.

## Decision (`scripts/escalation.py`)

`decide(graph, node, signals, registry_records, consent, reachable)` returns
`none`, `suggest` or `auto`:

- Signals: `outputs`, `failures`, `user_messages`, `tags`, `elapsed_s`, `reply_tokens`.
- Targets are ranked by best measured tg t/s from `registry/records.jsonl` for that
  model on that host (e.g. miryam `coder` 17.4 t/s beats `qodesh-resident` 0.91 t/s);
  unmeasured targets go last; unreachable hosts are dropped. ETA = reply_tokens / t/s.
- The system may suggest an edge but never opens one unasked. `auto` only applies
  when the node's mode is `auto` AND (same host OR consent recorded for that
  node -> target). Otherwise it is a `suggest` with a ready prompt for the user.
- Consent: `.cache/familia/escalation-consent.json`, written by
  `scripts/escalate.py consent --node X --target Y` after the user's first yes.

## Handoff and swap back

`handoff(turns, problem)` builds a compact payload (open problem + last 6 turns,
each clipped to 600 chars) so a slow heavy model does not spend minutes reading
the full history. The decision carries `swap_back_to`: route back to the light
node once the heavy reply lands.

## CLI

```
python scripts/escalate.py decide --node qodesh-smol-cpu --signals s.json [--reachable qodesh,miryam]
python scripts/escalate.py consent --node qodesh-smol-cpu --target coder
python scripts/escalate.py handoff --signals s.json
```

## Hook point (not wired yet)

The router (green-roomz route node / hermes harness) should, after each light
reply, build the signals dict, call `decide`, show `prompt` on `suggest`, and on
yes/auto send `handoff(...)` to the target alias, then return to `swap_back_to`.
This wiring into green-roomz is still TODO; the CLI is the integration surface.
