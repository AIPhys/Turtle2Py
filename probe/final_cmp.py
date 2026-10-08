"""Final byte-diff of the full 5M Python run against the Watcom reference.

python probe/final_cmp.py [pyfile]   (default full_py.res vs test_ref.res)

Prints record counts, mismatch count, and the first 10 mismatching records.
Exit code 0 iff the two files are byte-identical.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pyfile = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "full_py.res")
reffile = ROOT / "test_ref.res"

ref = reffile.read_bytes().split(b"\r\n")
py = pyfile.read_bytes().split(b"\r\n")
bad = 0
first = []
for i in range(max(len(ref), len(py))):
    a = ref[i] if i < len(ref) else b"<missing>"
    b = py[i] if i < len(py) else b"<missing>"
    if a != b:
        bad += 1
        if len(first) < 10:
            first.append((i + 1, a, b))
print("ref recs:", len(ref) - 1, "py recs:", len(py) - 1, "mismatches:", bad)
for i, a, b in first:
    print("MISMATCH rec", i)
    print("  ref", a[:120])
    print("  py ", b[:120])
sys.exit(1 if bad else 0)
