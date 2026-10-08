"""Bounded equivalence test for the _trunc_ext np.float32-operand fix.

python probe/trunc_fix_test.py  ->  prints case count and mismatch count.
"""

import sys, time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turtle2py import x87 as X
from turtle2py.hist import _trunc_ext, _LIT100001

X.mp.mp.prec = 64


def old(x, a, d, lit):
    q = float(np.float32(x - a))
    t = q / d + lit
    n = int(t)
    if abs(t - n) > 1e-9 and abs(t - (n + 1)) > 1e-9:
        return n
    return int(X.mp.mpf(float(q)) / X.mp.mpf(float(d)) + X.mp.mpf(float(lit)))


rng = np.random.default_rng(7)
bad = mp = 0
t0 = time.time()
N = 300
for i in range(N):
    a = rng.uniform(-5, 5)
    d = rng.uniform(1e-4, 2.0)
    x = a + d * rng.uniform(-0.5, 40.5)
    if i % 2 == 0:  # force near-boundary values
        k = int(rng.integers(0, 40))
        x = a + d * (k - 1.00001 + rng.uniform(-1e-7, 1e-7))
    x32, a32, d32 = np.float32(x), np.float32(a), np.float32(d)
    for darg in (d32, float(d32)):
        try:
            r_old = old(x32, a32, darg, _LIT100001)
        except TypeError:
            mp += 1  # old code crashed on np.float32 operand
            continue
        r_new = _trunc_ext(x32, a32, darg, _LIT100001)
        if r_old != r_new:
            bad += 1
            if bad < 5:
                print("DIFF", x32, a32, darg, r_old, r_new)
print(
    "cases:",
    2 * N,
    "old-crash(np.float32):",
    mp,
    "mismatches:",
    bad,
    "time: %.1f s" % (time.time() - t0),
)
print(
    "d=0 ->", _trunc_ext(np.float32(1.0), np.float32(0.0), np.float32(0.0), _LIT100001)
)
sys.exit(1 if bad else 0)
