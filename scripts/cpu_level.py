#!/usr/bin/env python3
"""Report this CPU's x86-64 microarchitecture level (v1..v4), or n/a off x86,
and the numpy requirement that follows from it. Stdlib only.

Why: NumPy >= 2.4.0 builds its x86 wheels with cpu-baseline=min = X86_V2
(SSE SSE2 SSE3 SSSE3 SSE4_1 SSE4_2 POPCNT CX16 LAHF), so on older CPUs such as
the Athlon II X2 they crash with an illegal instruction (Windows 0xc000001d).
Sources: https://numpy.org/doc/stable/release/2.4.0-notes.html and
https://numpy.org/doc/stable/reference/simd/build-options.html
NumPy 2.0-2.3 used an SSE3 baseline, so "numpy<2.4" is the newest release that loads on these CPUs.

The numpy choice depends ONLY on the level: x86 below v2 gets numpy<2.4, everything else gets plain numpy.
Usage: cpu_level.py [--json] [--numpy-spec] [--cpuinfo FILE] [--machine ARCH]
"""
import json, os, platform, sys

# Linux /proc/cpuinfo flag names for each x86-64 psABI level.
LEVELS = [
    ("v1", {"lm", "cmov", "cx8", "fpu", "fxsr", "mmx", "syscall", "sse", "sse2"}),
    ("v2", {"cx16", "lahf_lm", "popcnt", "pni", "sse4_1", "sse4_2", "ssse3"}),
    ("v3", {"avx", "avx2", "bmi1", "bmi2", "f16c", "fma", "abm", "movbe", "xsave"}),
    ("v4", {"avx512f", "avx512bw", "avx512cd", "avx512dq", "avx512vl"}),
]
NUMPY_OLD_X86 = "numpy<2.4"
NUMPY_DEFAULT = "numpy"

def is_x86(machine=None):
    m = (machine or platform.machine()).lower()
    return m in ("x86_64", "amd64", "x64", "i386", "i486", "i586", "i686", "x86")

def level_from_flags(flags):
    """Highest level whose flags, and all lower levels' flags, are present. v0 if not even v1."""
    flags = set(flags); got = "v0"
    for name, need in LEVELS:
        if not need <= flags:
            break
        got = name
    return got

def flags_from_cpuinfo(text):
    for line in text.splitlines():
        k, _, v = line.partition(":")
        if k.strip() == "flags":
            return set(v.split())
    return set()

def _cpuid_windows():
    """Run CPUID through a tiny x64 stub (Windows calling convention) and return flags named as in cpuinfo."""
    import ctypes
    code = bytes([0x53, 0x89, 0xC8, 0x89, 0xD1, 0x0F, 0xA2, 0x41, 0x89, 0x00, 0x41, 0x89, 0x58, 0x04,
                  0x41, 0x89, 0x48, 0x08, 0x41, 0x89, 0x50, 0x0C, 0x5B, 0xC3])
    k32 = ctypes.windll.kernel32
    k32.VirtualAlloc.restype = ctypes.c_void_p
    k32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]
    k32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong]
    mem = k32.VirtualAlloc(None, 4096, 0x3000, 0x40)
    if not mem:
        raise OSError("VirtualAlloc failed")
    try:
        ctypes.memmove(mem, code, len(code))
        fn = ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32 * 4))(mem)
        def q(leaf, sub=0):
            r = (ctypes.c_uint32 * 4)(); fn(leaf, sub, ctypes.byref(r)); return list(r)
        mx = q(0)[0]; ext = q(0x80000000)[0]
        _, _, c1, d1 = q(1)
        b7 = q(7)[1] if mx >= 7 else 0
        ce, de = (q(0x80000001)[2:4] if ext >= 0x80000001 else (0, 0))
    finally:
        k32.VirtualFree(mem, 0, 0x8000)
    f = set()
    for name, r, n in [("fpu", d1, 0), ("cx8", d1, 8), ("cmov", d1, 15), ("mmx", d1, 23), ("fxsr", d1, 24),
                       ("sse", d1, 25), ("sse2", d1, 26), ("pni", c1, 0), ("ssse3", c1, 9), ("fma", c1, 12),
                       ("cx16", c1, 13), ("sse4_1", c1, 19), ("sse4_2", c1, 20), ("movbe", c1, 22),
                       ("popcnt", c1, 23), ("xsave", c1, 26), ("avx", c1, 28), ("f16c", c1, 29),
                       ("bmi1", b7, 3), ("avx2", b7, 5), ("bmi2", b7, 8), ("avx512f", b7, 16),
                       ("avx512dq", b7, 17), ("avx512cd", b7, 28), ("avx512bw", b7, 30), ("avx512vl", b7, 31),
                       ("lahf_lm", ce, 0), ("abm", ce, 5), ("syscall", de, 11), ("lm", de, 29)]:
        if (r >> n) & 1:
            f.add(name)
    return f

def _flags_macos():
    import subprocess
    out = ""
    for key in ("machdep.cpu.features", "machdep.cpu.leaf7_features", "machdep.cpu.extfeatures"):
        try:
            out += " " + subprocess.check_output(["sysctl", "-n", key], text=True)
        except Exception:
            pass
    ren = {"sse3": "pni", "sse4.1": "sse4_1", "sse4.2": "sse4_2", "lahf": "lahf_lm", "lzcnt": "abm", "em64t": "lm"}
    return {ren.get(t.lower(), t.lower()) for t in out.split()}

def numpy_spec(level):
    return NUMPY_OLD_X86 if level in ("v0", "v1") else NUMPY_DEFAULT

def detect(cpuinfo_path=None, machine=None):
    arch = machine or platform.machine()
    if not is_x86(arch):
        return {"arch": arch, "level": "n/a", "source": "arch", "numpy": NUMPY_DEFAULT}
    flags, src = None, None
    if cpuinfo_path or os.path.exists("/proc/cpuinfo"):
        src = cpuinfo_path or "/proc/cpuinfo"
        with open(src, encoding="utf-8", errors="replace") as fh:
            flags = flags_from_cpuinfo(fh.read())
    elif sys.platform == "win32":
        flags, src = _cpuid_windows(), "cpuid"
    elif sys.platform == "darwin":
        flags, src = _flags_macos(), "sysctl"
    if not flags:
        return {"arch": arch, "level": "unknown", "source": src, "numpy": NUMPY_DEFAULT}
    lvl = level_from_flags(flags)
    return {"arch": arch, "level": lvl, "source": src, "numpy": numpy_spec(lvl)}

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="x86-64 level -> numpy spec")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--numpy-spec", action="store_true")
    ap.add_argument("--cpuinfo", help="read flags from this cpuinfo file (tests)")
    ap.add_argument("--machine", help="override platform.machine() (tests)")
    a = ap.parse_args(argv)
    r = detect(a.cpuinfo, a.machine)
    if a.numpy_spec: print(r["numpy"])
    elif a.json: print(json.dumps(r))
    else: print("x86-64 level: %s (arch %s, from %s) -> %s" % (r["level"], r["arch"], r["source"], r["numpy"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
