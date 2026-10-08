"""Compare probe26.res V-lines (NH,VAL) vs Python MOMDUMP py_val.txt VAL field.

Fortran probe26 line: 0V + I3 + 1X + G22.15  (NH, VAL only)
Python 1D dump line:   0V + I3 + 1X + 7*G22.15 (NH, VAL, RAY1-4, P, Z)
Python 2D dump lines are filtered out (their NH is not in the Fortran set).

Usage: python probe/vcmp.py [fortran] [python]
"""

import sys

fa = sys.argv[1] if len(sys.argv) > 1 else "probe26.res"
pa = sys.argv[2] if len(sys.argv) > 2 else "py_val.txt"

fort = []
for line in open(fa, "rb").read().split(b"\r\n"):
    if line.startswith(b"0V"):
        fort.append(line.decode()[2:28])  # I3 + 1X + G22.15
nh1d = {l[:3] for l in fort}

py = []
for line in open(pa, "rb").read().split(b"\n"):
    line = line.rstrip(b"\r")
    if line.startswith(b"0V") and line.decode()[2:5] in nh1d:
        py.append(line.decode()[2:28])

print("fortran V lines:", len(fort), " python V lines:", len(py))
n = min(len(fort), len(py))
bad = 0
first = []
for i in range(n):
    if fort[i] != py[i]:
        bad += 1
        if len(first) < 12:
            first.append((i, fort[i], py[i]))
print("mismatched V lines:", bad)
for i, a, b in first:
    print("  line", i)
    print("    fortran:", repr(a))
    print("    python :", repr(b))
sys.exit(1 if bad or len(fort) != len(py) else 0)
