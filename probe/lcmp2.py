"""Compare Fortran HISTO/ENTMAT L (probe42s.res, fixed-width E16.9) vs models.

9996: 1H0,3E16.9,I6 -> cols [1:17],[17:33],[33:49],[49:55] = X,A,DX,L
9997: 1H1,2E16.9,I6 -> cols [1:17],[17:33],[33:39] = A,DA,IA
"""
import sys, numpy as np, mpmath as mp
mp.mp.prec = 64
lit = float(np.float32(1.00001))
def m_old(x, a, d, l):
    return int(np.trunc(np.float32((x - a) / d + l)))
def m_new(x, a, d, l):
    return int((mp.mpf(x) - mp.mpf(a)) / mp.mpf(d) + mp.mpf(l))
n = ob = nb = 0
ex = []
for line in sys.stdin:
    if line[0] == '0' and len(line) >= 55:
        x, a, d, L = float(line[1:17]), float(line[17:33]), float(line[33:49]), int(line[49:55])
        l = lit
    elif line[0] == '1' and len(line) >= 39:
        x, a, d, L = float(line[1:17]), float(line[17:33]), 1.0, int(line[33:39])
        # ENTMAT: A, DA, IA  ->  (A - 0)/DA + 1.0
        a, d, l = 0.0, float(line[17:33]), 1.0
        x = float(line[1:17])
    else:
        continue
    n += 1
    o = m_old(x, a, d, l)
    w = m_new(x, a, d, l)
    if o != L:
        ob += 1
        if len(ex) < 6: ex.append(('old', line.strip(), o))
    if w != L:
        nb += 1
        if len(ex) < 12: ex.append(('new', line.strip(), w))
print("lines:", n, "old mismatches:", ob, "new mismatches:", nb)
for e in ex: print(e)
