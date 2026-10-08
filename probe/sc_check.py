"""Compare SCATT_MY internals (Python) against the Fortran SC dump (probe17.res).

SC fields (FORMAT 9722): I, sig, phi, del_x1, del_y1, del_xx, del_yy,
                         sig_r1, sig_rr, dz_elem, ray(1), ray(2), ray(3)
"""

import sys

import numpy as np

sys.path.insert(0, ".")
from turtle2py import tracking
from turtle2py.fields import turtle

f32 = np.float32
tracking.DUMP = True
turtle("turtle_small.dat", "small_py6.res")

NAMES = [
    "sig",
    "phi",
    "del_x1",
    "del_y1",
    "del_xx",
    "del_yy",
    "sig_r1",
    "sig_rr",
    "dz_elem",
    "ray1",
    "ray2",
    "ray3",
]


def ulp(a, b):
    ia = int(np.frombuffer(np.float32(a).tobytes(), np.int32)[0])
    ib = int(np.frombuffer(np.float32(b).tobytes(), np.int32)[0])
    if ia < 0:
        ia = -ia - 0x80000000
    if ib < 0:
        ib = -ib - 0x80000000
    return abs(ia - ib)


ref = []
for ln in open("probe17.res", "rb"):
    s = ln.decode("latin-1")
    if s.startswith("SC"):
        p = s.split()
        ref.append((int(p[1]), [float(v) for v in p[2:]]))

py = tracking.SCS
print("ref SC lines:", len(ref), " py:", len(py))
n = min(len(ref), len(py))
bad = 0
first = None
per = {nm: 0 for nm in NAMES}
for k in range(n):
    ir, vr = ref[k]
    ip, vp = py[k][0], list(py[k][1:])
    if ir != ip:
        print("ALIGNMENT BREAK k=%d ref i=%d py i=%d" % (k, ir, ip))
        break
    diffs = [(j, ulp(vr[j], vp[j])) for j in range(12) if f32(vr[j]) != f32(vp[j])]
    if diffs:
        bad += 1
        for j, u in diffs:
            per[NAMES[j]] += 1
        if first is None:
            first = (k, ir, diffs)
print("mismatches:", bad, "of", n)
if first:
    k, ir, diffs = first
    print("first k=%d i=%d" % (k, ir))
    print("  ref", ["%.17g" % v for v in vr])
    print("  py ", ["%.17g" % v for v in vp])
    for j, u in diffs:
        print("   %-8s ref %.17g  py %.17g  ulp %d" % (NAMES[j], vr[j], vp[j], u))
print("per-field mismatch counts:", {k: v for k, v in per.items() if v})
sys.exit(1 if bad else 0)
