"""Compare emitted-ray E-lines: probe32.res (Fortran) vs py_emit.txt (Python).

Fortran line: 0E + I4 + 6*G22.15 (NCT, RAY1..RAY6)  [P truncated by format]
Python  line: same fields.

Usage: python probe/ecmp.py [fortran] [python]
"""

import sys

fa = sys.argv[1] if len(sys.argv) > 1 else "probe32.res"
pa = sys.argv[2] if len(sys.argv) > 2 else "py_emit.txt"

fort = []
for line in open(fa, "rb").read().split(b"\r\n"):
    if line.startswith(b"0E"):
        # I4 + 5 G22.15 fields (RAY1..RAY5); Fortran's 6th G field is stack garbage
        fort.append(line.decode()[2:116])
py = []
for line in open(pa, "rb").read().split(b"\n"):
    line = line.rstrip(b"\r")
    if line.startswith(b"0E"):
        py.append(line.decode()[2:116])

print("fortran E lines:", len(fort), " python E lines:", len(py))
n = min(len(fort), len(py))
bad = 0
first = []
for i in range(n):
    if fort[i] != py[i]:
        bad += 1
        if len(first) < 8:
            first.append((i + 1, fort[i], py[i]))
print("mismatched E lines:", bad)
for n, a, b in first:
    print("ray", n)
    print("  fortran:", repr(a))
    print("  python :", repr(b))
sys.exit(1 if bad or len(fort) != len(py) else 0)
