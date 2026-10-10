"""cpu_level: x86-64 level from fake cpuinfo flags -> numpy spec (depends only on level)."""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import cpu_level as cl

V1 = "fpu cx8 cmov mmx fxsr sse sse2 syscall lm"
ATHLON2 = V1 + " pni cx16 lahf_lm popcnt abm sse4a 3dnow"   # K10: no ssse3/sse4_1/sse4_2
V2 = V1 + " pni ssse3 cx16 sse4_1 sse4_2 popcnt lahf_lm"
V3 = V2 + " avx avx2 bmi1 bmi2 f16c fma abm movbe xsave"
V4 = V3 + " avx512f avx512bw avx512cd avx512dq avx512vl"

def _info(tmp_path, flags):
    p = tmp_path / "cpuinfo"
    p.write_text("processor\t: 0\nmodel name\t: fake\nflags\t\t: %s\n\n" % flags)
    return str(p)

def test_levels(tmp_path):
    for flags, lvl, np_ in [(ATHLON2, "v1", "numpy<2.4"), (V1, "v1", "numpy<2.4"), (V2, "v2", "numpy"),
                            (V3, "v3", "numpy"), (V4, "v4", "numpy"), ("sse sse2", "v0", "numpy<2.4")]:
        r = cl.detect(_info(tmp_path, flags), machine="x86_64")
        assert (r["level"], r["numpy"]) == (lvl, np_), flags

def test_missing_one_v2_flag_is_v1(tmp_path):
    assert cl.detect(_info(tmp_path, V2.replace(" sse4_2", "")), machine="x86_64")["level"] == "v1"

def test_non_x86_is_na():
    for m in ("aarch64", "armv7l", "arm64", "riscv64"):
        r = cl.detect(None, machine=m)
        assert (r["level"], r["numpy"]) == ("n/a", "numpy")

def test_only_level_matters(tmp_path):
    p = _info(tmp_path, ATHLON2)
    assert {cl.detect(p, machine=m)["numpy"] for m in ("x86_64", "AMD64", "i686")} == {"numpy<2.4"}

def test_cli_numpy_spec(tmp_path):
    out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "cpu_level.py"), "--numpy-spec",
                          "--cpuinfo", _info(tmp_path, V3), "--machine", "x86_64"],
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "numpy"

def test_this_machine_runs():
    assert cl.detect()["level"] in ("v0", "v1", "v2", "v3", "v4", "n/a", "unknown")

def test_candidates_old_x86_prefers_our_wheel():
    c = cl.numpy_candidates("v1", tag="win_amd64-cp312")
    assert c[0].endswith("numpy-2.5.3-cp312-cp312-win_amd64.whl") and c[-1] == "numpy<2.4"
    assert cl.numpy_candidates("v0", tag="linux_x86_64-cp311") == ["numpy<2.4"]
    for lvl in ("v2", "v3", "v4", "n/a", "unknown"):
        assert cl.numpy_candidates(lvl, tag="win_amd64-cp312") == ["numpy"]
