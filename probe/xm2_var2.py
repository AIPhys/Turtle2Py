"""Battery of XMOM2 spill patterns (Watcom -opt=0 stores subexpressions to
REAL*4 temporaries) on histogram K. xm matches the faithful extended chain,
so VAL/SM/XM inputs are bit-exact; only the xm2 spill pattern is unknown.

Usage: python probe/xm2_var2.py [K ...]
"""

import sys

sys.path.insert(0, ".")
import numpy as np
import mpmath as mp

mp.mp.prec = 64
from turtle2py import x87 as X


def load(k):
    vals = []
    for line in open("probe26.res", "rb").read().split(b"\r\n"):
        if line.startswith(b"0V") and int(line[2:5]) == k:
            vals.append(np.float32(float(line[6:28])))
    fort = None
    for line in open("probe25.res"):
        p = line.split()
        if p and p[0] == "0M1" and int(p[1]) == k:
            fort = (float(p[2]), float(p[3]))
    return vals, fort


def f(x):  # store to REAL*4
    return X.S(x)


def r(x):  # load REAL*4 into extended
    return X.R(np.float32(x))


def xm_new(s, xmf, v):
    return f(((s - 1.0) * X.R(xmf) + X.R(v)) / s)


def Q(xm, xm2, n, v):  # t2=f32(s*xm2); rest extended
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = r(f(s * X.R(xm2)))
    xm2 = f((s - 1.0) * (t2 + X.P(X.R(v) - X.R(xmf), 2)) / X.P(s, 2))
    return xm, xm2


def Qs2(xm, xm2, n, v):  # + s2=f32(s*s)
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = r(f(s * X.R(xm2)))
    s2 = r(f(s * s))
    xm2 = f((s - 1.0) * (t2 + X.P(X.R(v) - X.R(xmf), 2)) / s2)
    return xm, xm2


def Qd(xm, xm2, n, v):  # + d2=f32((val-xm)^2)
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = r(f(s * X.R(xm2)))
    d2 = r(f(X.P(X.R(v) - X.R(xmf), 2)))
    xm2 = f((s - 1.0) * (t2 + d2) / X.P(s, 2))
    return xm, xm2


def Q5(xm, xm2, n, v):  # + t5=f32(t2+d2)
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = r(f(s * X.R(xm2)))
    d2 = r(f(X.P(X.R(v) - X.R(xmf), 2)))
    t5 = r(f(t2 + d2))
    xm2 = f((s - 1.0) * t5 / X.P(s, 2))
    return xm, xm2


def Q6(xm, xm2, n, v):  # + t6=f32((s-1)*t5)
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = r(f(s * X.R(xm2)))
    d2 = r(f(X.P(X.R(v) - X.R(xmf), 2)))
    t5 = r(f(t2 + d2))
    t6 = r(f((s - 1.0) * t5))
    xm2 = f(t6 / X.P(s, 2))
    return xm, xm2


def Qall(xm, xm2, n, v):  # every subexpression stored to f32
    s = X.R(np.float32(n))
    xmf = X.S(xm)
    xm = xm_new(s, xmf, v)
    t2 = r(f(s * X.R(xm2)))
    d = r(f(X.R(v) - X.R(xmf)))
    d2 = r(f(d * d))
    t5 = r(f(t2 + d2))
    t6 = r(f((s - 1.0) * t5))
    s2 = r(f(s * s))
    xm2 = f(t6 / s2)
    return xm, xm2


MODELS = (("Q", Q), ("Qs2", Qs2), ("Qd", Qd), ("Q5", Q5), ("Q6", Q6), ("Qall", Qall))

ks = [int(a) for a in sys.argv[1:]] or [19]
for k in ks:
    vals, fort = load(k)
    print(f"=== k={k} n={len(vals)} fortran xm2={fort[1]!r}")
    for name, step in MODELS:
        xm = mp.mpf(0.0)
        xm2 = mp.mpf(0.0)
        for i, v in enumerate(vals):
            xm, xm2 = step(xm, xm2, i + 1, v)
        a, b = X.S(xm), X.S(xm2)
        okx = np.float32(fort[0]) == a
        ok2 = np.float32(fort[1]) == b
        print(
            f"  {name:5s} xm {'OK' if okx else 'NO'} xm2 {'OK' if ok2 else 'NO'} "
            f"rel={(b - fort[1]) / fort[1]:.3e}"
        )
