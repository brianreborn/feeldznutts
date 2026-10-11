# REQUIREMENTS.md

> **Status note (2026-10-10):** trimmed from earlier session notes; each item says whether it is **implemented**, **in progress**, or **planned**. Owner: the familia maintainer.

## Overview
High-level requirements for the familia topology coordinator: the Linux orchestrator, Android (Termux) nodes, Windows nodes, and a future SSH proxy nexus.

## Core
- **Nodes:** Linux orchestrator (implemented), Android/Termux node over SSH port 8022 (in progress: #14, #18), Windows node (in progress: #17; `scripts/windows/start.bat` on main).
- **Specialist roles (pentest):** declared in the graph under `pentests` (implemented on `main`; see `docs/graph-types.md`, `docs/pentest-models.md`). **Launch-tested only.** Automation may only validate → start → healthcheck → stop. Never fully exercise attack tools, live scans, exploits, or network probes in tests or PoCs.
  - **Tools double-disabled for launch-tests (required):** every automated pentest launch-test MUST disable tools in **two independent ways** before any process starts. Acceptable pairs today: (1) empty `tools.allow: []` in both `graph.yaml` `pentests.*` and `scripts/pentest-role.json`, and (2) `launch_test_only: true` so `with-fleet.sh` refuses to start tool-capable paths (and the hermes agent / toolsets are not started). Empty `scope.allow: []` is additional hard deny, not a substitute for the second tools disable. Never remove either disable for CI or smoke tests.
- **Commands:** `/local` and `/remote` routing (implemented in the pinned code-bootstraps-llama.cpp agent, not in this repo).
- **Declarative configuration:** models, runtimes and agents declared in `graph.yaml` and checked by `scripts/validate_graph.py` (implemented; see `docs/configuration-graph.md`).
- **RAM safety:** keep a large reserve on small hosts; `reserve_ram_mib: 3072` on miryam (implemented; provisional guidance — see `docs/ram-safety.md`).
- **Tests:** Python unit tests for the graph and registry (implemented); shell syntax CI (`sh -n` / shellcheck) planned (#14).

## Android node
- Launch via `android_start.sh` with host, port and user from the graph / environment and key-based SSH (#18). Fleet helpers `with-fleet.sh` and `scripts/pentest-role.json` are on `main` (fixes #15); pentest role remains launch-test only.
- `watchdog_android.sh` monitoring: planned cleanup (password variable name, cwd-relative path, log location).

## SSH proxy nexus (planned)
- Goal: let nodes behind NAT talk via an edge host using `ssh -R` / `-L`.
- Key-only auth, password auth disabled.
- Declarative config in the graph (`hosts` / `transports`). A proof of concept is on the unmerged `feat/transport-poc` branch.

## Removed (stale)
- `scripts/github_issue.sh`, `rebuild_top_level_scripts.sh`, `*.ps1` regeneration, `proxy-nexus-config.json`, and a "99.9 % uptime" target: none existed or were measurable.
