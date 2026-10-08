"""Element tracking: exact ports of BEND, QUAD, SEXT, SOLO, MULTI, FOCUS,
RESET, REPEAT, BSTOP, QSTOP, NU, HSTUN, HSTVAL, HEDING, HISCAP, APLIM.

Convention (Watcom x87, verified 2026-10-03 vs probe13.res QD dump): REAL*4
variables hold float32; every arithmetic operation and transcendental call is
evaluated in x87 extended precision (64-bit mantissa, turtle2py/x87.py);
transcendental library calls receive their argument rounded to float32 (the
library takes REAL*4 by value); rounding to float32 happens only at each
Fortran variable store.  Fortran 1-based arrays map to the padded numpy
arrays in Context (index 0 unused).
"""

import numpy as np

from . import x87 as X

F32 = np.float32

E = X.E  # load float32 -> extended mpf
S = X.S  # store extended -> float32 (Python float)
V = X.V  # x87 extended register (operator overloading)
K = X.K  # REAL*4 literal constant as extended register
P = X.P  # integer power, unrolled extended multiplication


def _f(v):
    return float(v)


def nu(ctx, typ):
    """INTEGER FUNCTION NU(TYPE) (turtle.f:1995-2029)."""
    NO1 = [9, 9, 2, 6, 4, 5, 7, 0, 2, 0, 0, 0, 0, 8, 0, 5, 0, 3, 3, 3, 2]
    NO2 = [1, 1, 1, 2]
    if ctx.sec and typ == 4:
        return 41
    if typ == 14 and ctx.idata[ctx.i + 8] == 0:
        return 30
    if typ >= 50:
        typ1 = typ - 49
        return NO2[typ1 - 1] if typ1 <= 4 else 0
    return NO1[abs(typ) - 1]


def reset(ctx, a, b):
    """RESET(A,B) (turtle.f:2543-2553): copy B(1..4) -> A(1..4)."""
    ctx.__dict__[a][1:5] = ctx.__dict__[b][1:5]


def repeat(ctx):
    """REPEAT (turtle.f:2521-2542)."""
    idata = ctx.idata
    i = ctx.i
    if idata[i + 1] != 0:
        ctx.ip += 1
        ctx.ic[ctx.ip] = idata[i + 1]
        ctx.is_[ctx.ip] = i
        return
    ctx.ic[ctx.ip] -= 1
    if ctx.ic[ctx.ip] != 0:
        ctx.i = ctx.is_[ctx.ip]
        return
    ctx.ip -= 1


def focus(k2, l, r):
    """FOCUS(K2, L, K, KL, R) (turtle.f:1909-1935).  Returns (K, KL, R[1..4]).

    x87 model (verified vs probe13.res QD): K, KL, R(i) are REAL*4 stores;
    each expression is evaluated in extended precision from the stored
    float32 operands; transcendental library calls take the float32 value.
    """
    k = S(X.sqrt(abs(float(k2))))
    kl = S(E(k) * E(l))
    if k2 > 0.0:
        r1 = S(X.cos(kl))
        r3 = S(-E(k) * X.sin(kl))
        r4 = r1
        if abs(kl) < 0.01:
            r2 = S(E(l) * (1.0 - E(k2) * E(l) * E(l) / 6.0))
            return k, kl, (r1, r2, r3, r4)
        r2 = S(-E(r3) / E(k2))
        return k, kl, (r1, r2, r3, r4)
    if k2 < 0.0:
        expkl = S(X.exp(kl))
        exikl = S(1.0 / E(expkl))
        r1 = S(0.5 * (E(expkl) + E(exikl)))
        r3 = S(0.5 * (E(expkl) - E(exikl)) * E(k))
        r4 = r1
        if abs(kl) < 0.01:
            r2 = S(E(l) * (1.0 - E(k2) * E(l) * E(l) / 6.0))
            return k, kl, (r1, r2, r3, r4)
        r2 = S(-E(r3) / E(k2))
        return k, kl, (r1, r2, r3, r4)
    # k2 == 0: label 10 with K=0, KL=0 -> ABS(KL)<0.01 -> label 30
    r1 = S(X.cos(0.0))
    r3 = S(-E(k) * X.sin(0.0))
    r4 = r1
    r2 = S(E(l) * (1.0 - E(k2) * E(l) * E(l) / 6.0))
    return k, kl, (r1, r2, r3, r4)


def quad(ctx):
    """QUAD (turtle.f:2076-2103).  Uses ctx.i, ctx.ll, ctx.p, ctx.ray.

    x87 model: KH2/KV2 stores round once; FOCUS results are float32; the
    RAY2(1..4) products are evaluated in extended precision from the stored
    operands and rounded once at the RAY2 store.
    """
    d = ctx.data
    kh2 = S(E(d[ctx.i + 2]) / E(ctx.p))
    kv2 = S(-E(kh2))
    kh, khl, rh = focus(kh2, ctx.ll, None)
    kv, kvl, rv = focus(kv2, ctx.ll, None)
    ctx.kh, ctx.khl, ctx.rh[:] = kh, khl, rh
    ctx.kv, ctx.kvl, ctx.rv[:] = kv, kvl, rv
    ray = ctx.ray
    r2 = ctx.ray2
    r2[1] = S(E(rh[0]) * E(ray[1]) + E(rh[1]) * E(ray[2]))
    r2[2] = S(E(rh[2]) * E(ray[1]) + E(rh[3]) * E(ray[2]))
    r2[3] = S(E(rv[0]) * E(ray[3]) + E(rv[1]) * E(ray[4]))
    r2[4] = S(E(rv[2]) * E(ray[3]) + E(rv[3]) * E(ray[4]))
    reset(ctx, "ray", "ray2")


def qstop(ctx, lflag):
    """QSTOP(LFLAG) (turtle.f:2104-2133)."""
    ray = ctx.ray
    if not ctx.cap[lflag]:
        return False
    if ctx.ellips:
        if (ray[1] / ctx.qap[1]) ** 2 + (ray[3] / ctx.qap[2]) ** 2 > 1.0:
            return True
        if not ctx.hyper:
            return False
    elif ctx.hyper:
        if abs(ray[1] * ray[3]) > ctx.qap[3]:
            return True
        return False
    else:
        if ray[1] ** 2 + ray[3] ** 2 > ctx.data[ctx.i + 3]:
            return True
        return False


def bstop(ctx, lflag):
    """BSTOP(LFLAG) (turtle.f:1865-1888)."""
    ray = ctx.ray
    if not ctx.cap[lflag]:
        return False
    if ctx.apb[1] != 0.0:
        if abs(ray[1]) > ctx.apb[1]:
            return True
    if ctx.apb[2] != 0.0:
        if abs(ray[3]) > ctx.apb[2]:
            return True
    return False


def sext(ctx):
    """SEXT (turtle.f:3058-3094)."""
    d = ctx.data
    ll = _f(ctx.ll)
    ray = ctx.ray
    r2 = ctx.ray2
    r2[1] = S(V(ray[1]) + ll * V(ray[2]))
    r2[2] = ray[2]
    r2[3] = S(V(ray[3]) + ll * V(ray[4]))
    r2[4] = ray[4]
    if ctx.sec:
        c = S(ll * V(d[ctx.i + 2]) / V(ctx.p))
        u = S(P(V(ray[1]), 2) - P(V(ray[3]), 2))
        up = S(ll * (V(ray[1]) * V(ray[2]) - V(ray[3]) * V(ray[4])))
        upp = S(P(ll, 2) * (P(V(ray[2]), 2) - P(V(ray[4]), 2)))
        r2[1] = S(V(r2[1]) - c * (K(0.5) * V(u) + V(up) / 3.0 + V(upp) / 12.0) * ll)
        r2[2] = S(V(r2[2]) - c * (V(u) + V(up) + V(upp) / 3.0))
        u = S(V(ray[1]) * V(ray[3]))
        up = S(ll * (V(ray[1]) * V(ray[4]) + V(ray[2]) * V(ray[3])))
        upp = S(P(ll, 2) * V(ray[2]) * V(ray[4]))
        r2[3] = S(V(r2[3]) + c * (V(u) + V(up) / 3.0 + V(upp) / 6.0) * ll)
        r2[4] = S(V(r2[4]) + c * (V(u) + V(u) + V(up) + V(upp) / 1.5))
    reset(ctx, "ray", "ray2")


def solo(ctx):
    """SOLO (turtle.f:3095-3129)."""
    d = ctx.data
    ll = _f(ctx.ll)
    ray = ctx.ray
    r2 = ctx.ray2
    kh = S(V(d[ctx.i + 2]) / V(ctx.p))
    khl = S(ll * V(kh))
    c = S(X.cos(khl))
    s = S(X.sin(khl))
    if khl >= 0.01:
        sok = S(V(s) / V(kh))
    else:
        sok = S(ll * (1.0 - P(V(kh) * ll, 2) / 6.0))
    sk = S(V(s) * V(kh))
    r2[1] = S(V(c) * V(ray[1]) + V(sok) * V(ray[2]))
    r2[2] = S(-V(sk) * V(ray[1]) + V(c) * V(ray[2]))
    r2[3] = S(V(c) * V(ray[3]) + V(sok) * V(ray[4]))
    r2[4] = S(-V(sk) * V(ray[3]) + V(c) * V(ray[4]))
    ray[1] = S(V(c) * V(r2[1]) + V(s) * V(r2[3]))
    ray[3] = S(-V(s) * V(r2[1]) + V(c) * V(r2[3]))
    ray[2] = S(V(c) * V(r2[2]) + V(s) * V(r2[4]))
    ray[4] = S(-V(s) * V(r2[2]) + V(c) * V(r2[4]))


def multi(ctx):
    """MULTI (turtle.f:1967-1994)."""
    db, cosm, sinm = ctx.db, ctx.cosm, ctx.sinm
    dbx = V(0.0)
    dby = V(0.0)
    dbc = V(0.0)
    dbs = V(1.0)
    x = V(ctx.ray[1])
    y = V(ctx.ray[3])
    for nm in range(1, ctx.mmax + 1):
        if db[nm] != 0.0:
            dbx = dbx + V(db[nm]) * (dbc * V(cosm[nm]) - dbs * V(sinm[nm]))
            dby = dby + V(db[nm]) * (dbc * V(sinm[nm]) + dbs * V(cosm[nm]))
        dbt = dbc * x + dbs * y
        dbs = dbs * x - dbc * y
        dbc = dbt
    ctx.ray[2] = S(V(ctx.ray[2]) - V(ctx.gtop) * dby)
    ctx.ray[4] = S(V(ctx.ray[4]) + V(ctx.gtop) * dbx)


def hstun(ctx, nco):
    """HSTUN(NCO, FACT, LEGAL) (turtle.f:669-698).  Returns (fact, legal)."""
    if 0 < nco <= 6:
        if nco == 5:
            return None, False
        return ctx.unit[nco - 1], True
    if nco == 8 or nco == 11:
        return ctx.unit[nco - 1], True
    if nco > 20 and nco <= 24:
        j = nco - 20
        return (ctx.unit[j - 1] if j <= 2 else ctx.unit[6]), True
    return None, False


def hstval(ctx, nco):
    """HSTVAL(NCO) (turtle.f:699-729)."""
    ray = ctx.ray
    if nco <= 6:
        return ray[nco]
    if nco == 8:
        return ctx.z
    if nco == 11:
        return ctx.p
    if nco > 20:
        if nco > 22:
            j = nco - 22
            val = F32(0.0)
            if ray[j + 2] != 0.0 or ray[j] != 0.0:
                # Watcom evaluates ATAN2 in x87 extended (64-bit mantissa)
                # and rounds only at the HSTVAL result store.
                val = X.S(X.atan2(X.R(ray[j + 2]), X.R(ray[j])))
            return val
        j = nco - 20
        # Watcom evaluates RAY**2, the sum and SQRT in x87 extended and
        # rounds only at the HSTVAL result store.
        return X.S(X.sqrt(X.P(X.R(ray[j]), 2) + X.P(X.R(ray[j + 2]), 2)))
    return F32(0.0)


def bend(ctx):
    """BEND(KSTOP) (turtle.f:1694-1864).  Returns kstop (0/1)."""
    d = ctx.data
    ll = _f(ctx.ll)
    ray = ctx.ray
    r2 = ctx.ray2
    kstop = 0
    h = F32(d[ctx.i + 2])
    n = F32(d[ctx.i + 3])
    bdb = F32(d[ctx.i + 5])
    ctx.h, ctx.n, ctx.bdb = h, n, bdb
    hf, nf, bdbf = _f(h), _f(n), _f(bdb)
    if __import__("os").environ.get("BDUMP") == "1":
        bend._n = getattr(bend, "_n", 0) + 1
    if n == 0.0 and bdb == 0.0:
        return _bend_sector(ctx, ll, hf, d, ray, r2, kstop)
    kh2 = S(P(V(h), 2) * (1.0 - V(n)))
    kv2 = S(P(V(h), 2) * V(n))
    kh, khl, rh = focus(kh2, ll, None)
    kv, kvl, rv = focus(kv2, ll, None)
    ctx.kh2, ctx.kv2, ctx.kh, ctx.khl, ctx.rh[:] = kh2, kv2, kh, khl, rh
    ctx.kv, ctx.kvl, ctx.rv[:] = kv, kvl, rv
    if __import__("os").environ.get("BDUMP") == "1":
        if bend._n == 2:
            from . import formats as _F

            def _r(fmt, vals):
                print(_F.render(fmt, vals).decode("latin-1")[:-2])

            _r("1H0,'KH',5G22.15", [float(x) for x in (kh2, kv2, kh, khl, kv)])
            _r("1H0,'RR',4G22.15", [float(x) for x in (kvl, rh[0], rh[1], rh[2])])
            _r("1H0,'RR',4G22.15", [float(x) for x in (rh[3], rv[0], rv[1], rv[2])])
            _r("1H0,'RR',4G22.15", [float(x) for x in (rv[3], 0.0, 0.0, 0.0)])
    # CX/SX/CY/SY, X10..Y446, A1..C2, T116..T446, DH, D, SKL are BEND LOCAL
    # REAL variables: Watcom keeps them in x87 registers, so they stay in
    # extended precision and are NEVER rounded to float32.  Only COMMON-block
    # arrays (KH2, KV2, RH, RV, RAY2) are stored as REAL*4.
    cx, sx, cy, sy = V(rh[0]), V(rh[1]), V(rv[0]), V(rv[1])
    kh2v, kv2v, khlv, kvlv = V(kh2), V(kv2), V(khl), V(kvl)
    if abs(khlv) >= 0.01:
        x10 = S((1.0 - cx) / kh2v)
        q1 = S((ll - sx) / kh2v)
        q2 = S((3.0 * V(q1) - sx * V(x10)) / kh2v)
    else:
        skl = S(khlv * khlv)
        x10 = S(P(ll, 2) * (0.5 - V(skl) / 24.0))
        q1 = S(P(ll, 3) * (1.0 / 6.0 - V(skl) / 120.0))
        q2 = S(P(ll, 5) * (0.1 - V(skl) / 84.0))
    if abs(kvlv) >= 0.01:
        y34 = S(0.5 * (sy - ll * cy) / kv2v)
    else:
        y34 = S(P(ll, 3) * (1.0 / 6.0 - kv2v * P(ll, 2) / 60.0))
    x11 = S(0.5 * ll * sx)
    x12 = S(0.5 * (ll * V(x10) - V(q1)))
    x16 = S(0.5 * (V(x10) * V(x10) - sx * V(q1)))
    x21 = S(0.5 * (sx + ll * cx))
    x22 = V(x11)
    x26 = V(x12)
    y33 = S(0.5 * ll * sy)
    y43 = S(0.5 * (sy + ll * cy))
    y44 = V(y33)
    dv = S(kh2v - 4.0 * kv2v)
    if abs(V(dv) * P(ll, 2)) >= 1.0e-6:
        x144 = S((sy * sy - 2.0 * V(x10)) / V(dv))
        x244 = S(2.0 * (sy * cy - sx) / V(dv))
        y324 = S((2.0 * cy * V(x10) - sx * sy) / V(dv))
        y424 = S((sx * cy - cx * sy + 2.0 * V(rv[2]) * V(x10)) / V(dv))
    else:
        x144 = S(2.0 * V(x16))
        x244 = S(2.0 * V(x12))
        y324 = S(0.5 * sy * V(q1))
        y424 = S(0.5 * (sy * V(x10) + cy * V(q1)))
    x112 = S(sx * V(x10) / 3.0)
    x116 = S(0.5 * sx * V(q1) - V(x10) * V(x10) / 6.0)
    x122 = S(V(x10) * V(x10) / 3.0)
    x126 = S((sx * V(x10) * V(x10) - cx * V(q2)) / 6.0)
    x166 = S((P(V(x10), 3) - sx * V(q2)) / 3.0)
    x212 = S((2.0 * sx * sx - V(x10)) / 3.0)
    x216 = S(2.0 * V(x112) - 0.5 * (ll * V(x10) - V(q1)))
    x222 = S(2.0 * V(x112))
    x226 = S(sx * V(q1) - V(x116))
    x266 = S(2.0 * V(x126))
    y323 = S(sy * V(x10) - V(y424))
    y423 = S(cy * V(x10) + kv2v * V(y324))
    y336 = S(0.5 * (sy * V(q1) - V(y324)))
    y436 = S(0.5 * (cy * V(q1) + V(y323)))
    y346 = S(
        (V(y34) + sy * V(x10) - 2.0 * V(y424)) / kh2v
        if abs(kh2) >= 0.0001
        else 0.5 * (sy * V(x10) - cy * V(q1) - V(y424)) / kv2v
    )
    y446 = S(0.5 * (sy * V(q1) + V(y324)))
    hv, nv, bdv = V(h), V(n), V(bdb)
    a1 = S(P(hv, 3) * (nv + nv - bdv - 1.0) * 2.0)
    a2 = S(hv * (2.0 - nv))
    c1 = S(P(hv, 3) * (bdv - nv) * 2.0)
    c2 = S(hv * nv)
    rh1, rh2, rh3, rh4 = V(rh[0]), V(rh[1]), V(rh[2]), V(rh[3])
    rv1, rv2, rv3, rv4 = V(rv[0]), V(rv[1]), V(rv[2]), V(rv[3])
    t116 = S(V(a1) * V(x116) - kh2v * hv * V(x122) + V(a2) * V(x11))
    t216 = S(V(a1) * V(x216) - kh2v * hv * V(x222) + V(a2) * V(x21) - hv * (rh1 * sx + rh3 * V(x10)))
    t126 = S(V(a1) * V(x126) + hv * V(x112) + V(a2) * V(x12))
    t226 = S(V(a1) * V(x226) + hv * V(x212) + V(a2) * x22 - hv * (rh2 * sx + rh4 * V(x10)))
    t166 = S(0.5 * (V(a1) * V(x166) + hv * V(x122)) + V(a2) * V(x16))
    t266 = S(0.5 * (V(a1) * V(x266) + hv * V(x222)) + V(a2) * x26 - hv * V(x10) * sx)
    t336 = S(V(c1) * V(y336) - kv2v * hv * V(y324) + V(c2) * V(y33))
    t436 = S(V(c1) * V(y436) - kv2v * hv * V(y424) + V(c2) * V(y43) - hv * V(x10) * rv3)
    t346 = S(V(c1) * V(y346) + hv * V(y323) + V(c2) * V(y34))
    t446 = S(V(c1) * V(y446) + hv * V(y423) + V(c2) * y44 - hv * V(x10) * rv4)
    dh = S(hv * (V(ctx.p) - V(ctx.p0)) / V(ctx.p))
    r1, r2v, r3, r4 = V(ray[1]), V(ray[2]), V(ray[3]), V(ray[4])
    r2[1] = S((rh1 + V(dh) * V(t116)) * r1 + (rh2 + V(dh) * V(t126)) * r2v + (V(x10) + V(dh) * V(t166)) * V(dh))
    r2[2] = S((rh3 + V(dh) * V(t216)) * r1 + (rh4 + V(dh) * V(t226)) * r2v + (sx + V(dh) * V(t266)) * V(dh))
    r2[3] = S((rv1 + V(dh) * V(t336)) * r3 + (rv2 + V(dh) * V(t346)) * r4)
    r2[4] = S((rv3 + V(dh) * V(t436)) * r3 + (rv4 + V(dh) * V(t446)) * r4)
    if __import__("os").environ.get("BDUMP") == "1" and bend._n == 2:
        from . import formats as _F

        print(
            _F.render(
                "1H0,'R2',4G22.15",
                [float(r2[j]) for j in (1, 2, 3, 4)],
            ).decode("latin-1")[:-2]
        )
    if ctx.sec:
        kstop = _bend_sec_terms(
            ctx,
            ll,
            hv,
            nv,
            bdv,
            kh2v,
            kv2v,
            rh,
            rv,
            sx,
            sy,
            cx,
            cy,
            V(x10),
            V(x112),
            V(x122),
            V(x212),
            V(x222),
            V(x144),
            V(x244),
            V(y324),
            V(y424),
            V(y323),
            V(y423),
            V(a1),
            V(c1),
            r2,
        )
    reset(ctx, "ray", "ray2")
    return kstop


def _bend_sector(ctx, ll, hf, d, ray, r2, kstop):
    """BEND labels 300-310 (sector magnet, N=BDB=0)."""
    alfa = S(ll * V(hf))
    rho0 = S(d[ctx.i + 4])
    rho = S(V(rho0) * V(ctx.p) / V(ctx.p0))
    af, rho0f, rhof = _f(alfa), _f(rho0), _f(rho)
    theta1 = S(X.atan(ray[2]))
    cost1 = S(X.cos(theta1))
    t1f = _f(theta1)
    sint2 = S(X.sin_ext(V(t1f) + V(af)) - X.sin_ext(V(af)) * (V(ray[1]) + V(rho0f)) / V(rhof))
    if abs(_f(sint2)) >= 1.0:
        return 1
    cost2 = S(X.sqrt(1.0 - P(V(sint2), 2)))
    cosal = S(X.cos(af))
    c2f, c1f = _f(cost2), _f(cost1)
    # COS(THETA1+ALFA) in this expression takes the argument spilled to
    # REAL*4 (verified 288/288 vs probe16.res); the SIN() in SINT2 above
    # takes the unrounded extended argument.  See x87.cos32.
    r2[1] = S(
        V(ray[1]) * V(cosal)
        + V(rhof) * (V(c2f) - X.cos32(V(t1f) + V(af)))
        - V(rho0f) * (1.0 - V(cosal))
    )
    r2[2] = S(V(sint2) / V(c2f))
    # (ALFA+THETA1) is spilled to REAL*4 inside this expression (verified
    # 288/288 vs probe16.res, probe/sector_r3c.py tree search); ASIN keeps
    # the extended value and the products stay extended.
    r2[3] = S(
        V(ray[3]) + V(ray[4]) * V(rhof) * V(c1f) * (S(V(af) + V(t1f)) - X.asin(sint2))
    )
    if __import__("os").environ.get("SDUMP2") == "1" and getattr(bend, "_n", 0) == 7:
        import mpmath as _mp

        def _g(v):
            m = v.m if isinstance(v, X.V) else _mp.mpf(float(v))
            return _mp.nstr(m, 19)

        xx = [alfa, rho0, rho, theta1, cost1, sint2, cost2, cosal]
        for k in range(0, len(xx), 2):
            print("0X** %s %s" % (_g(xx[k]), _g(xx[k + 1])))
        yy = [ray[1], ray[2], ray[3], ray[4], r2[1], r2[2], r2[3], r2[4],
              ctx.ll, h]
        for k in range(0, len(yy), 2):
            print("0Y** %s %s" % (_g(yy[k]), _g(yy[k + 1])))
    r2[4] = S(V(ray[4]) * V(c1f) / V(c2f))
    reset(ctx, "ray", "ray2")
    return 0


def _bend_sec_terms(
    ctx,
    ll,
    hv,
    nv,
    bdv,
    kh2v,
    kv2v,
    rh,
    rv,
    sx,
    sy,
    cx,
    cy,
    x10,
    x112,
    x122,
    x212,
    x222,
    x144,
    x244,
    y324,
    y424,
    y323,
    y423,
    a1,
    c1,
    r2,
):
    """BEND labels 400-390 (SEC second-order terms, turtle.f:1797-1845).

    X111..Y414 and T111..T424 are BEND LOCAL REAL variables: Watcom keeps
    them in x87 registers, so they stay in extended precision and are never
    rounded to float32.  Only RAY2 (COMMON) is stored as REAL*4.
    """
    rh1, rh2, rh3, rh4 = V(rh[0]), V(rh[1]), V(rh[2]), V(rh[3])
    rv1, rv2, rv3, rv4 = V(rv[0]), V(rv[1]), V(rv[2]), V(rv[3])
    x111 = S(x10 - kh2v * x122)
    x133 = S(x10 - kv2v * x144)
    x134 = S(0.5 * x244)
    x211 = S(sx - kh2v * x222)
    x233 = S(sx - kv2v * x244)
    x234 = S(V(x133) - kv2v * x144)
    y313 = S(0.5 * (sx * sy + kh2v * y324))
    y314 = S(2.0 * y424 - sy * x10)
    y413 = S(0.5 * (cx * sy + sx * cy + kh2v * y424))
    y414 = S(0.5 * (sx * sy - kh2v * y324))
    kh22 = kh2v * kh2v
    kv22 = kv2v * kv2v
    t111 = S(0.5 * (a1 * V(x111) + kh22 * hv * x122))
    t211 = S(0.5 * (a1 * V(x211) + kh22 * hv * x222) - hv * rh1 * rh3)
    t112 = S((a1 - kh2v * hv) * x112 + hv * rh2)
    t212 = S((a1 - kh2v * hv) * x212 + hv * (rh4 - rh1 * rh4 - rh3 * rh2))
    t122 = S(0.5 * (a1 * x122 + hv * V(x111)))
    t222 = S(0.5 * (a1 * x222 + hv * V(x211)) - hv * rh2 * rh4)
    b1 = S(P(hv, 3) * (bdv + bdv - nv))
    t133 = S(0.5 * (V(b1) * V(x133) - kv22 * hv * x144))
    t233 = S(0.5 * (V(b1) * V(x233) - kv22 * hv * x244))
    t134 = S((V(b1) + kv2v * hv) * V(x134))
    t234 = S((V(b1) + kv2v * hv) * V(x234))
    t144 = S(0.5 * (V(b1) * x144 - hv * V(x133)))
    t244 = S(0.5 * (V(b1) * x244 - hv * V(x233)))
    t313 = S(c1 * V(y313) + kh2v * kv2v * hv * y324)
    t413 = S(c1 * V(y413) + kh2v * kv2v * hv * y424 - hv * rh1 * rv3)
    t314 = S(c1 * V(y314) - kh2v * hv * y323 + hv * rv2)
    t414 = S(c1 * V(y414) - kh2v * hv * y423 + hv * (rv4 - rh1 * rv4))
    t323 = S(c1 * y323 - kv2v * hv * V(y314))
    t423 = S(c1 * y423 - kv2v * hv * V(y414) - hv * rh2 * rv3)
    t324 = S(c1 * y324 + hv * V(y313))
    t424 = S(c1 * y424 + hv * V(y413) - hv * rh2 * rv4)
    r1, r2v, r3, r4 = V(ctx.ray[1]), V(ctx.ray[2]), V(ctx.ray[3]), V(ctx.ray[4])
    r2[1] = S(
        V(r2[1])
        + V(t111) * P(V(r1), 2)
        + V(t112) * V(r1) * V(r2v)
        + V(t122) * P(V(r2v), 2)
        + V(t133) * P(V(r3), 2)
        + V(t134) * V(r3) * V(r4)
        + V(t144) * P(V(r4), 2)
    )
    r2[2] = S(
        V(r2[2])
        + V(t211) * P(V(r1), 2)
        + V(t212) * V(r1) * V(r2v)
        + V(t222) * P(V(r2v), 2)
        + V(t233) * P(V(r3), 2)
        + V(t234) * V(r3) * V(r4)
        + V(t244) * P(V(r4), 2)
    )
    r2[3] = S(
        V(r2[3])
        + (V(t313) * V(r3) + V(t314) * V(r4)) * V(r1)
        + (V(t323) * V(r3) + V(t324) * V(r4)) * V(r2v)
    )
    r2[4] = S(
        V(r2[4])
        + (V(t413) * V(r3) + V(t414) * V(r4)) * V(r1)
        + (V(t423) * V(r3) + V(t424) * V(r4)) * V(r2v)
    )
    return 0


# ---CHUNK-D---
