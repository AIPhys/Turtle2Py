"""Compare Fortran (probe25.res) vs Python (py_mom.txt) internal moments."""

import re, sys


def load(path, tag):
    out = {}
    for line in open(path):
        p = line.split()
        if p and p[0] == tag:
            k = int(p[1])
            out.setdefault(k, []).append([float(v) for v in p[2:]])
    return out


for tag in ("M1", "M2"):
    f = load("probe25.res", "0" + tag)
    p = load(sys.argv[1] if len(sys.argv) > 1 else "py_val.txt", "0" + tag)
    for k in sorted(set(f) | set(p)):
        fa = f.get(k, [])
        pa = p.get(k, [])
        if len(fa) != len(pa):
            print(tag, k, "COUNT", len(fa), len(pa))
            continue
        for i, (fv, pv) in enumerate(zip(fa, pa)):
            for j, (a, b) in enumerate(zip(fv, pv)):
                d = (b - a) / max(abs(a), 1e-30)
                if abs(d) > 1e-9:
                    print(f"{tag} k={k} i={i} j={j} for={a!r} py={b!r} rel={d:.3e}")
print("done")
