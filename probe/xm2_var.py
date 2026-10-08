"""Battery of XMOM2 rounding-order variants on k=19 (76798 steps).

xm matches Fortran bit-exactly in the extended model, so VAL/XM/SM inputs
are right; xm2 drifts as a random walk of f32 store roundings, so the
exact Watcom instruction sequence decides the final bits.
"""

import sys

sys.path.insert(0, ".")
import numpy as np
import mpmath as mp

mp.mp.prec = 64
from turtle2py import x87 as X

K = int(sys.argv[1]) if len(sys.argv) > 1 else 19
vals = []
for line in open("probe26.res", "rb").read().split(b"\r\n"):
    if line.startswith(b"0V") and int(line[2:5]) == K:
        vals.append(np.float32(float(line[6:28])))
fort = None
for line in open("probe25.res"):
    p = line.split()
    if p and p[0] == "0M1" and int(p[1]) == K:
        fort = (float(p[2]), float(p[3]))
print("fortran xm2:", fort[1], "n:", len(vals))


def run(name, step):
    xm = mp.mpf(0.0)
    xm2 = mp.mpf(0.0)
    for i, v in enumerate(vals):
        xm, xm2 = step(xm, xm2, i + 1, v)
    a, b = X.S(xm), X.S(xm2)
    ok = np.float32(fort[1]) == b
    print(
        f"{name:4s} xm {'OK' if np.float32(fort[0]) == a else 'NO'} "
        f"xm2 {'OK' if ok else 'NO'} rel={(b - fort[1]) / fort[1]:.3e}"
    )


def xm_new(s, xmf, v):
    return X.S(((s - 1.0) * X.R(xmf) + X.R(v)) / s)


def A(xm, xm2, n, v):  # all extended, single store
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    xm2 = X.S((s - 1.0) * (s * X.R(xm2) + X.P(X.R(v) - X.R(xmf), 2)) / X.P(s, 2))
    return xm, xm2


def E(xm, xm2, n, v):  # inner sum rounded to f32
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    inner = X.R(X.S(s * X.R(xm2) + X.P(X.R(v) - X.R(xmf), 2)))
    xm2 = X.S((s - 1.0) * inner / X.P(s, 2))
    return xm, xm2


def I(xm, xm2, n, v):  # numerator (s-1)*inner rounded to f32
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    num = X.R(X.S((s - 1.0) * (s * X.R(xm2) + X.P(X.R(v) - X.R(xmf), 2))))
    xm2 = X.S(num / X.P(s, 2))
    return xm, xm2


def L(xm, xm2, n, v):  # (s-1)*(xm2 + d^2/s)/s
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    d2 = X.P(X.R(v) - X.R(xmf), 2)
    xm2 = X.S((s - 1.0) * (X.R(xm2) + d2 / s) / s)
    return xm, xm2


def M(xm, xm2, n, v):  # xm2*(s-1)/s + (s-1)*d^2/s^2
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    d2 = X.P(X.R(v) - X.R(xmf), 2)
    xm2 = X.S(X.R(xm2) * (s - 1.0) / s + (s - 1.0) * d2 / X.P(s, 2))
    return xm, xm2


def N(xm, xm2, n, v):  # (s*xm2 + d2*(s-1)/s)/s  : d2 scaled first
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    d2 = X.P(X.R(v) - X.R(xmf), 2)
    xm2 = X.S((s * X.R(xm2) + d2 * (s - 1.0) / s) / s)
    return xm, xm2


def O(xm, xm2, n, v):  # d rounded to f32, d2 rounded to f32, inner extended
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    d = X.R(X.S(X.R(v) - X.R(xmf)))
    d2 = X.R(X.S(d * d))
    xm2 = X.S((s - 1.0) * (s * X.R(xm2) + d2) / X.P(s, 2))
    return xm, xm2


def Q(xm, xm2, n, v):  # s*xm2 rounded to f32
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = X.R(X.S(s * X.R(xm2)))
    xm2 = X.S((s - 1.0) * (t2 + X.P(X.R(v) - X.R(xmf), 2)) / X.P(s, 2))
    return xm, xm2


for nm, fn in (
    ("A", A),
    ("E", E),
    ("I", I),
    ("L", L),
    ("M", M),
    ("N", N),
    ("O", O),
    ("Q", Q),
):
    run(nm, fn)
