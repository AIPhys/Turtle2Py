"""Verify the port's _trunc_ext model against probe43s.res ground truth.
HISTO lines:  '0' + X,   AMIN(=A), DX,   L   (E16.9 x3, I6)
ENTMAT lines: '1' + A, AMIN, DA, IA  and  '1' + D, DMIN, DD, ID
Operands printed as E16.9: parse then round to float32 (the true REAL*4 value).
"""

import sys, numpy as np, mpmath as mp

mp.mp.prec = 64
sys.path.insert(0, ".")
from turtle2py.hist import _trunc_ext, _LIT100001

f32 = np.float32

histo, entmat = [], []
for line in sys.stdin:
    if len(line) < 55:
        continue
    if line[0] == "0":
        histo.append(line)
    elif line[0] == "1":
        entmat.append(line)


def run(rows, lit, label):
    n = near = 0
    ex = []
    for line in rows:
        v = float(f32(float(line[1:17])))
        a = float(f32(float(line[17:33])))
        d = float(f32(float(line[33:49])))
        L = int(line[49:55])
        n += 1
        t64 = float(f32(v - a)) / d + lit
        dist = t64 - np.floor(t64)
        if not (dist < 1e-4 or dist > 1.0 - 1e-4):
            continue
        near += 1
        p = _trunc_ext(v, a, d, lit)
        if p != L:
            ex.append((line.strip(), p, L))
    print(f"{label}: lines={n} near-boundary={near} mismatches={len(ex)}")
    for e in ex[:8]:
        print("   ", e)


run(histo, _LIT100001, "HISTO")
run(entmat, 1.0, "ENTMAT")
