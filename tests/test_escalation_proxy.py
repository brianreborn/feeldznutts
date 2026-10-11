import json, os, sys, threading, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import escalation_proxy as EP

def mock(name, seen):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            b = json.loads(self.rfile.read(int(self.headers["Content-Length"]))); seen.append((name, b))
            out = json.dumps({"choices": [{"message": {"role": "assistant", "content": "same answer"}}]}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(out)
    s = ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s.server_address[1]

def graph(pl, ph, mode):
    return {"hosts": {"h": {}}, "aliases": {},
            "nodes": {"light": {"host": "h", "port": pl, "model": "smollm2", "escalates_to": ["heavy"], "escalation": {"mode": mode}},
                      "heavy": {"host": "h", "port": ph, "model": "qwen35-2b"}}}

def post(port, msgs):
    r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps({"model": "x", "messages": msgs}).encode(), headers={"Content-Type": "application/json"}))
    return json.load(r)["choices"][0]["message"]["content"]

def test_auto_swap_handoff_and_swap_back(monkeypatch, tmp_path):
    monkeypatch.setattr(EP, "STATE", str(tmp_path)); monkeypatch.setattr(EP, "PENDING", str(tmp_path / "p.json"))
    seen = []; g = graph(mock("light", seen), mock("heavy", seen), "auto")
    recs = [{"host": "h", "kind": "bench", "model": {"repo": "qwen3.5-2b"}, "metrics": {"tg_tps": {"max": 10}}}]
    esc = EP.Escalator(g, "light", recs, "h", consent={}); srv = EP.serve(esc); p = srv.server_address[1]
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "fix it"}]
    post(p, msgs); post(p, msgs); out = post(p, msgs)       # 3 identical outputs -> auto
    assert "escalated to heavy" in out
    post(p, msgs + [{"role": "user", "content": "go"}])
    assert seen[-1][0] == "heavy" and json.loads(seen[-1][1]["messages"][-1]["content"])["open_problem"] == "go"
    post(p, msgs)
    assert seen[-1][0] == "light"                            # swapped back
    srv.shutdown()

def test_suggest_then_accept(monkeypatch, tmp_path):
    for k, f in (("STATE", ""), ("PENDING", "p.json"), ("ACCEPT", "a.json")): monkeypatch.setattr(EP, k, str(tmp_path / f))
    seen = []; g = graph(mock("light", seen), mock("heavy", seen), "suggest")
    esc = EP.Escalator(g, "light", [], "h", consent={}); srv = EP.serve(esc); p = srv.server_address[1]
    msgs = [{"role": "user", "content": "please try harder"}]
    out = post(p, msgs)
    assert "escalate.py accept" in out and os.path.exists(EP.PENDING)
    json.dump({"target": "heavy"}, open(EP.ACCEPT, "w"))
    post(p, msgs); assert seen[-1][0] == "heavy"
    srv.shutdown()

def test_signals_count_tool_failures():
    s = EP.Signals()
    s.observe_request({"messages": [{"role": "user", "content": "x"}, {"role": "tool", "content": "Traceback: boom"},
                                    {"role": "tool", "content": "ok"}, {"role": "tool", "content": "exit code 2"}]})
    assert s.failures == 2

def test_remote_loopback_node_unreachable():
    g = {"hosts": {"a": {}, "b": {"addr": "10.0.0.2"}}, "nodes": {"x": {"host": "b", "port": 1, "bind": "127.0.0.1"}}}
    assert EP.node_url(g, "x", "a") is None
