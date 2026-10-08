"""KEY FIX: the E16.9 dump prints 9 significant digits; parsing them as a
double is NOT the exact REAL*4 operand. Round every parsed value to float32
first (that is the true f32 operand), then test the x87 models.
"""

import sys, numpy as np, mpmath as mp

mp.mp.prec = 64
lit = float(np.float32(1.00001))
f32 = np.float32
E = mp.mpf


def sub_ext(x, a):
    return E(x) - E(a)


def sub_f32(x, a):
    return E(float(f32(E(x) - E(a))))


def div_ext(n, d):
    return n / E(d)


def div_f32(n, d):
    return E(float(f32(n / E(d))))


def add_ext(q):
    return q + E(lit)


def add_f32(q):
    return E(float(f32(q + E(lit))))


def tr_ext(t):
    return int(t)


def tr_f32(t):
    return int(f32(float(t)))


M = {
    "A ext,ext,ext | tr_ext": lambda x, a, d: tr_ext(
        add_ext(div_ext(sub_ext(x, a), d))
    ),
    "E f32s,extd,exta| tr_ext": lambda x, a, d: tr_ext(
        add_ext(div_ext(sub_f32(x, a), d))
    ),
    "F ext,ext,ext | tr_f32": lambda x, a, d: tr_f32(
        add_ext(div_ext(sub_ext(x, a), d))
    ),
    "I f32,f32,f32 | tr_f32": lambda x, a, d: tr_f32(
        add_f32(div_f32(sub_f32(x, a), d))
    ),
    "C ext,f32,ext | tr_ext": lambda x, a, d: tr_ext(
        add_ext(div_f32(sub_ext(x, a), d))
    ),
}
cnt = {k: 0 for k in M}
ex = {k: [] for k in M}
n = 0
for line in sys.stdin:
    if line[0] != "0" or len(line) < 55:
        continue
    x = float(f32(float(line[1:17])))
    a = float(f32(float(line[17:33])))
    d = float(f32(float(line[33:49])))
    L = int(line[49:55])
    t64 = (x - a) / d + lit
    dist = t64 - np.floor(t64)
    if not (dist < 1e-4 or dist > 1.0 - 1e-4):
        continue
    n += 1
    for k, fn in M.items():
        p = fn(x, a, d)
        if p != L:
            cnt[k] += 1
            if len(ex[k]) < 6:
                ex[k].append((line.strip(), p, L))
print("near-boundary lines:", n)
for k in sorted(M, key=lambda k: cnt[k]):
    print(k, "mismatches:", cnt[k])
    for e in ex[k]:
        print("   ", e)
