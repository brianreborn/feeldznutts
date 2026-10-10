"""Model + hardware registry (docs/model-registry.md)."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import registry as R  # noqa: E402
import pytest

def test_records_valid_and_labelled():
    recs = R.load()
    assert len(recs) >= 22
    for r in recs:
        R.normalize(r)
        for k, v in r["metrics"].items():
            if isinstance(v, dict) and "min" in v: assert v["measured"] in (True, False)
        assert r["power"]["measured"] is False or r["power"].get("method")

def test_add_rejects_unlabelled_metric():
    with pytest.raises(ValueError):
        R.normalize({"host": "x", "device": {}, "runtime": {}, "model": {}, "settings": {}, "timestamp": "t", "source": "s",
                     "metrics": {"tg_tps": {"min": 1}}})

def test_append_only():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "r.jsonl")
        for i in range(2):
            R.append({"i": i}, p)
        assert [json.loads(l)["i"] for l in open(p)] == [0, 1]

def test_suggest_miryam_decision_prefers_cpu_and_penalises_igpu():
    ranked = R.suggest("miryam", "decision", R.load())
    assert ranked[0]["backend"] == "cpu"
    ig = [c for c in ranked if c["backend"] == "vulkan"]
    # alone-only iGPU records (e.g. SmolLM2 2026-10-10) have no contention data -> factor 1.0
    assert min(c["contention_factor"] for c in ig) < 0.5
    assert ranked[0]["watts_label"].startswith("estimate")

def test_suggest_phone_vulkan_and_snippet():
    c = R.suggest("phone8", "decision", R.load())[0]
    assert c["backend"] == "vulkan"
    assert "status: planned" in R.node_snippet("phone8", "decision", c)

def test_match_a57_and_version_warning():
    m = {"cpu": "ARMv8 Cortex-A720", "board": "erd8865", "os": "android", "ram_mib": 7430, "runtime": "Termux llama-cpp 0.7.0"}
    score, pid, warn = R.match(m, R.profiles())[0]
    assert pid.startswith("samsung-a57")
    assert any("runtime" in w for w in warn)

def test_match_none_for_unknown():
    assert R.match({"cpu": "Zilog Z80", "os": "cpm"}, R.profiles()) == []

def test_profiles_have_no_private_data():
    assert R.private_leaks(R.profiles()) == []

def test_graph_warns_without_evidence():
    w = R.graph_warnings({"nodes": {"n": {"host": "nohost", "model": "m"}}}, [])
    assert w and "no model-registry evidence" in w[0]
