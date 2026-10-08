"""Run the Python port on mid_in.dat (100k rays) and diff against mid_ref.res."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from turtle2py.fields import turtle

outp = ROOT / "mid_py.res"
turtle(str(ROOT / "mid_in.dat"), str(outp))

ref = (ROOT / "mid_ref.res").read_bytes().split(b"\r\n")
py = outp.read_bytes().split(b"\r\n")
n = max(len(ref), len(py))
bad = 0
first = []
for i in range(n):
    a = ref[i] if i < len(ref) else b"<missing>"
    b = py[i] if i < len(py) else b"<missing>"
    if a != b:
        bad += 1
        if len(first) < 10:
            first.append((i + 1, a, b))
print(
    "ref recs:", len(ref) - 1, "py recs:", len(py) - 1, "mismatches:", bad, flush=True
)
for i, a, b in first:
    print("MISMATCH rec", i)
    print("  ref", a[:120])
    print("  py ", b[:120])
sys.exit(1 if bad else 0)
