"""Compare per-element ray state (ray 4) against Fortran probe6 dump."""

import sys

import numpy as np

sys.path.insert(0, ".")
from turtle2py import tracking
from turtle2py.fields import turtle

f32 = np.float32
tracking.DUMP = True
turtle("turtle_small.dat", "small_py4.res")

ref = []
for ln in open("probe6.res", "rb"):
    s = ln.decode("latin-1")
    if s.startswith("EL"):
        p = s.split()
        ref.append((int(p[1]), float(p[2]), int(p[3]), [float(v) for v in p[4:]]))

py = tracking.ELS
print("ref EL lines:", len(ref), " py:", len(py))
n = min(len(ref), len(py))
bad = 0
for k in range(n):
    _, zr, ir, vr = ref[k]
    _, zp, ip, vp = py[k]
    ok = ir == ip and all(f32(a) == f32(b) for a, b in zip(vr, vp))
    if not ok:
        bad += 1
        print("EL k=%d i=%d MISMATCH" % (k, ir))
        print("  ref z=%.8g i=%d" % (zr, ir), ["%.9g" % v for v in vr])
        print("  py  z=%.8g i=%d" % (zp, ip), ["%.9g" % v for v in vp])
        for j, (a, b) in enumerate(zip(vr, vp), 1):
            if f32(a) != f32(b):
                print(
                    "   ray[%d]: ref %.9g  py %.9g  (ulp %d)"
                    % (
                        j,
                        a,
                        b,
                        abs(
                            np.frombuffer(np.float32(a).tobytes(), np.int32)[0]
                            - np.frombuffer(np.float32(b).tobytes(), np.int32)[0]
                        ),
                    )
                )
        if bad >= 3:
            break
print("mismatches:", bad)
sys.exit(1 if bad else 0)
