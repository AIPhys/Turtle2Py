"""Replay EHIST 1-D moment accumulation using the Fortran VAL stream
(probe26.res: 0V + I3 + 1X + G22.15, VAL values that entered HISTO) and
compare final XMOM/XMOM2 against Fortran (probe25.res 0M1 lines).

Isolates the accumulation model from tracking: same VALs, same counts.

Usage: python probe/ehist_replay.py
"""

import sys

sys.path.insert(0, ".")
import numpy as np
import mpmath as mp

mp.mp.prec = 64
from turtle2py import x87 as X

# --- load Fortran VAL stream, grouped by NH (stream order preserved) ---
vals = {}
for line in open("probe26.res", "rb").read().split(b"\r\n"):
    if line.startswith(b"0V"):
        nh = int(line[2:5])
        v = float(line[6:28])
        vals.setdefault(nh, []).append(np.float32(v))

# --- histogram lower bounds (HISTO: x < BEGIN -> overflow bin M+N+2 = SM) ---
sys.path.insert(0, ".")
from turtle2py.state import Context
from turtle2py.io import CardReader, ElementReader
from turtle2py import fields
from turtle2py.random import G900

lines = open("mid_in.dat", "rb").read().decode("latin-1").split("\n")
reader = CardReader(lines)
er = ElementReader(reader)
out = fields.Out()
ctx = Context()
ctx.rng = G900()
fields.initze(ctx)
fields.setup(ctx, reader, er, out)
begin = {k: np.float32(float(ctx.begin[k])) for k in range(1, ctx.nhists + 1)}

# --- Fortran final moments ---
fort = {}
for line in open("probe25.res"):
    p = line.split()
    if p and p[0] == "0M1":
        fort[int(p[1])] = (float(p[2]), float(p[3]))


def _div(a, b):
    """Watcom masked-FPU division: x/0 -> signed Inf, 0/0 -> NaN."""
    if b == 0:
        if a == 0:
            return mp.nan
        return mp.inf if a > 0 else mp.ninf
    return a / b


def replay_ext(vs, bg):
    """Current model: x87 extended chain, store f32 at each assignment.
    SM = MTABLE(M+N+2) = running count of VALs below BEGIN (HISTO underflow)."""
    xm = mp.mpf(0.0)
    xm2 = mp.mpf(0.0)
    sm = 0
    for v in vs:
        sm += 1
        s = X.R(np.float32(sm))
        xmf = X.S(xm)
        xm = X.S(_div((s - 1.0) * X.R(xmf) + X.R(v), s.m))
        xm2 = X.S(
            _div((s - 1.0) * (s * X.R(xm2) + X.P(X.R(v) - X.R(xmf), 2)), X.P(s, 2).m)
        )
    return X.S(xm), X.S(xm2)


def replay_f64(vs, bg):
    xm = xm2 = 0.0
    sm = 0
    inf = float("inf")
    nan = float("nan")
    for v in vs:
        sm += 1
        s = np.float32(sm)
        xmf = np.float32(xm)
        num = (s - 1.0) * xmf + float(v)
        xm = (
            float(np.float32(num / s))
            if s
            else (nan if num == 0 else inf * (1 if num > 0 else -1))
        )
        n2 = (s - 1.0) * (s * xm2 + (float(v) - xmf) ** 2)
        d2 = s * s
        xm2 = (
            float(np.float32(n2 / d2))
            if d2
            else (nan if n2 == 0 else inf * (1 if n2 > 0 else -1))
        )
    return xm, xm2


def replay_ext_nostore(vs, bg):
    """Extended chain with NO intermediate stores (xm/xm2 kept extended)."""
    xm = mp.mpf(0.0)
    xm2 = mp.mpf(0.0)
    sm = 0
    for v in vs:
        sm += 1
        s = X.R(np.float32(sm))
        xmf = xm  # extended, not stored
        xm = _div((s - 1.0) * xmf + X.R(v), s.m)
        xm2 = _div((s - 1.0) * (s * xm2 + X.P(X.R(v) - xmf, 2)), X.P(s, 2).m)
    return X.S(xm), X.S(xm2)


def replay_f64(vs, bg):
    xm = xm2 = 0.0
    sm = 0
    for v in vs:
        sm += 1
        s = np.float32(sm)
        xmf = np.float32(xm)
        xm = float(np.float32(((s - 1.0) * xmf + float(v)) / s))
        xm2 = float(np.float32((s - 1.0) * (s * xm2 + (float(v) - xmf) ** 2) / (s * s)))
    return xm, xm2


def replay_ext_nostore(vs, bg):
    """Extended chain with NO intermediate stores (xm/xm2 kept extended)."""
    xm = mp.mpf(0.0)
    xm2 = mp.mpf(0.0)
    sm = 0
    for v in vs:
        sm += 1
        s = X.R(np.float32(sm))
        xmf = xm  # extended, not stored
        xm = ((s - 1.0) * xmf + X.R(v)) / s
        xm2 = (s - 1.0) * (s * xm2 + X.P(X.R(v) - xmf, 2)) / X.P(s, 2)
    return X.S(xm), X.S(xm2)


bad = 0
for k in sorted(fort):
    vs = vals.get(k, [])
    bg = begin[k]
    fa, fb = fort[k]
    for name, fn in (
        ("ext", replay_ext),
        ("f64", replay_f64),
        ("extNS", replay_ext_nostore),
    ):
        a, b = fn(vs, bg)
        ok = (a == fa) and (b == fb)
        if not ok:
            bad += 1
            print(
                f"k={k} n={len(vs)} model={name} xm f={fa!r} p={a!r} xm2 f={fb!r} p={b!r}"
            )
print("done, model mismatches:", bad)
