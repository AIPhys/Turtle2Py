"""Tracking core: exact ports of EMIT_MY, SCATT_MY, RAYRUN and the main loop.

Convention (Watcom x87): intermediates in float64, rounded to float32 at
every Fortran variable assignment.  Fortran 1-based arrays map to the padded
numpy arrays in Context (index 0 unused).  RNG order is preserved exactly.
"""

import numpy as np

from . import elements as el
from . import x87 as X
from .random import G900

F32 = np.float32

# Checkpoint/resume support: env T2P_CKPT=path enables saving the loop state
# (ctx + nct, which is complete at label 690) every T2P_CKPT_EVERY rays.
_CKPT = __import__("os").environ.get("T2P_CKPT")
_CKPT_EVERY = int(__import__("os").environ.get("T2P_CKPT_EVERY", "100000"))


def _save_ckpt(ctx, nct, path, out=None):
    import pickle
    import time

    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        pickle.dump((nct, ctx, None if out is None else bytes(out.buf)), fh, protocol=4)
    __import__("os").replace(tmp, path)
    print("ckpt nct=%d t=%.0fs" % (nct, time.time()), flush=True)


def load_ckpt(path):
    import pickle

    with open(path, "rb") as fh:
        rec = pickle.load(fh)
    if len(rec) == 3:
        return rec
    return rec[0], rec[1], None


def _f(v):
    return float(v)


def _c(v):
    """Fortran REAL*4 literal: value rounded to float32, as Watcom stores it."""
    return float(np.float32(v))


PI = _c(6.2831853)
PI2 = _c(6.283185308)
Z_TEMP = _c(11.037)
YY_MAX = _c(_c(0.001) * 13.8745)
Y1_MAX = _c(_c(0.001) * 2.1622)


def _log(r):
    """ALOG with the Fortran fatal-on-zero guarded: return -inf so the
    caller's rejection test (abs > max) resamples, as in the reference."""
    if r <= 0.0:
        return -np.inf
    return np.log(r)


_key = 0
_xpr = np.zeros(51, np.float32)
_fun = np.zeros(51, np.float32)

# Ground-truth dump hook: mirrors FORMAT 9705/9702/9708 of probe/turtlep2.f.
# Enabled by tracking.DUMP = True; collects the first 4 rays only.
DUMP = False
RUNS = []
RAYS = []
EMS = []
ELS = []
SCS = []
SES = []
BAS = []
BBS = []
DUMP_RAYS = [4]

# probe28 mirror: per-element state dump for ray 2 (env MOMDUMP=1).
_MOMDUMP = __import__("os").environ.get("MOMDUMP") == "1"
# probe32 mirror: emitted-ray dump after EMIT_MY (env EMITDUMP=1).
_EMITDUMP = __import__("os").environ.get("EMITDUMP") == "1"
# probe33 mirror: label-40 attempt dump (env YDUMP=1).
_YDUMP = __import__("os").environ.get("YDUMP") == "1"
# probe36 mirror: per-element state dump at label 200 (env SDUMP=1).
_SDUMP = __import__("os").environ.get("SDUMP") == "1"
# probe37 mirror: label-220 internals for ray 1 (env QDUMP=1).
_QDUMP = __import__("os").environ.get("QDUMP") == "1"
_ycnt = 0
_DBG = []


def emit_my(ctx, rng):
    """EMIT_MY (turtle.f:251-371)."""
    global _key
    raymax = ctx.raymax
    ray = ctx.ray
    if _key == 0:
        xa = _f(raymax[1])
        dx = F32(xa / 50.0)
        ssum = 0.0
        for i in range(1, 51):
            x = _f(dx) * i - 0.5 * _f(dx)
            _xpr[i] = F32((1.0 - (x / xa) ** 0.25) ** 3.0)
            ssum = ssum + _f(_xpr[i])
        s = 0.0
        for i in range(1, 51):
            s = s + _f(_xpr[i])
            _fun[i] = F32(s / ssum)
        _key = 1
    dx = F32(_f(raymax[1]) / 50.0)
    fi = rng.ranf()
    _ = F32(PI * _f(rng.ranf()))  # XR6_temp (discarded)
    fif = _f(fi)
    i = 50
    for j in range(1, 51):
        if fif < _f(_fun[j]):
            i = j
            break
    ray[1] = F32(_f(dx) * (i - _f(rng.ranf())))
    ray[2] = F32(0.0)
    # label 38: horizontal scattering
    xr1 = F32(np.sqrt(-_c(2.0) * _log(_f(rng.ranf()))))
    xr2 = F32(PI * _f(rng.ranf()))
    del_x1 = F32(_f(raymax[2]) * _f(xr1) * np.sin(_f(xr2)))
    ray[2] = F32(_f(ray[2]) + _f(del_x1))
    # label 40: vertical Maximov
    yy_max = F32(YY_MAX)
    y1_max = F32(Y1_MAX)
    sig_yy = F32(_f(yy_max) / _c(3.0))
    sig_y1 = F32(_f(y1_max) / _c(3.0))
    yyf, y1f, syf, s1f = _f(yy_max), _f(y1_max), _f(sig_yy), _f(sig_y1)
    r3max = _f(raymax[3])
    while True:
        xr3 = F32(np.sqrt(-_c(2.0) * _log(_f(rng.ranf()))))
        xr4 = F32(PI * _f(rng.ranf()))
        xr3f, xr4f = _f(xr3), _f(xr4)
        del_yy = F32(syf * xr3f * np.cos(xr4f))
        # Watcom computes DEL_Y1 = SIG_Y1*XR3*SIN(XR4) entirely in x87
        # extended: the SIN result stays a 64-bit extended register and the
        # products round at 64-bit mantissa.  V.__mul__ with a plain operand
        # goes through float64, which truncates the SIN result; multiply in
        # mpf at prec 64 and round to REAL*4 directly (round32).
        # Verified 2026-10-05 vs probe34s.res W dump (100 rays).
        del_y1 = X.round32(X.M(s1f) * X.M(xr3f) * X.sin(xr4f))
        if _YDUMP:
            _DBG.append((s1f, xr3f, xr4f, del_y1))
        if _YDUMP:
            global _ycnt
            _ycnt += 1
            if _ycnt <= 100:
                from . import formats as _F

                print(
                    _F.render(
                        "1H0,'Y',I4" + ",G22.15" * 4,
                        [_ycnt, xr3f, xr4f, _f(del_yy), _f(del_y1)],
                    ).decode("latin-1")[:-2]
                )
                if _ycnt == 23:
                    print(
                        "DEBUG23",
                        s1f.hex(),
                        xr3f.hex(),
                        xr4f.hex(),
                        float(del_y1).hex(),
                        float((X.V(s1f) * X.V(xr3f) * X.sin(xr4f)).m).hex(),
                    )
        if abs(_f(del_yy)) > yyf or abs(_f(del_y1)) > y1f:
            continue
        ray[3] = X.S(X.V(del_yy) + X.V(del_y1) * X.V(Z_TEMP))
        ray[4] = F32(del_y1)
        if abs(_f(ray[3])) <= r3max:
            if _YDUMP and _ycnt <= 100:
                from . import formats as _F

                print(
                    _F.render(
                        "1H0,'W',I4" + ",G22.15" * 2,
                        [_ycnt, _f(ray[3]), _f(ray[4])],
                    ).decode("latin-1")[:-2]
                )
            break
    # label 41: vertical scattering
    xr3 = F32(np.sqrt(-_c(2.0) * _log(_f(rng.ranf()))))
    xr4 = F32(PI * _f(rng.ranf()))
    # Watcom x87: del_y1 stays in the extended register; the add to RAY(4)
    # rounds once (ground truth probe7.res L41, ray 4).
    del_y1 = _f(raymax[4]) * _f(xr3) * np.sin(_f(xr4))
    ray[4] = F32(_f(ray[4]) + del_y1)
    ray[5] = F32(_f(raymax[5]) * (_c(2.0) * _f(rng.ranf()) - _c(1.0)))
    # label 50
    while True:
        xr5 = F32(np.sqrt(-_c(2.0) * _log(_f(rng.ranf()))))
        xr6 = F32(PI * _f(rng.ranf()))
        ray[6] = F32(_f(raymax[6]) * _f(xr5) * np.cos(_f(xr6)))
        if abs(_f(ray[6])) <= _c(2.0) * _f(raymax[6]):
            break
    ctx.p = F32(_f(ctx.pbeam) * (1.0 + _f(ray[6])))
    if DUMP:
        global _np1
        _np1 += 1
        if _np1 <= 4:
            RAYS.append(
                (
                    _np1,
                    [float(ray[j]) for j in range(1, 7)] + [float(ctx.p)],
                    rng.g900gt(),
                )
            )


_np1 = 0


def scatt_my(ctx):
    """SCATT_MY (turtle.f:1014-1123).  Active path: label 30 (angles+coords).

    x87 model (verified 2026-10-05 vs probe16.res SC dump, ray 4): every
    Fortran variable (rn_sig, dz_elem, theta_0, sig_rr, sig_r1, sig, phi,
    del_x1, del_y1, del_xx, del_yy) is an implicit-REAL store, i.e. rounded
    to float32; the expression that produces it is evaluated in x87 extended
    from the stored float32 operands.  The rejection test compares extended
    sqrt(del**2+del**2) against the extended product sig_r1*rn_sig.
    """
    d = ctx.data
    ray = ctx.ray
    rn_sig = X.S(X.K(6.0))
    dz_elem = X.S(X.V(d[ctx.i + 1]) * X.K(100.0))
    theta_0 = X.S(X.V(d[ctx.i + 2]))
    sig_rr = X.S(X.V(theta_0) * X.V(dz_elem) / X.sqrt(X.K(12.0)))
    sig_r1 = X.S(X.V(theta_0))
    if DUMP:
        SES.append(
            (int(ctx.i), ray[1], ray[2], ray[3], ray[4], sig_r1, sig_rr, dz_elem)
        )

    rng = ctx.rng
    while True:
        sig = X.S(X.sqrt(-X.K(2.0) * X.log(_f(rng.ranf()))))
        phi = X.S(X.V(PI2) * X.V(_f(rng.ranf())))
        a1 = X.S(X.V(sig_r1) * X.V(sig))
        del_x1 = X.S(a1 * X.cos(X.V(phi)))
        del_y1 = X.S(a1 * X.S(X.sin(X.V(phi))))
        sig = X.S(X.sqrt(-X.K(2.0) * X.log(_f(rng.ranf()))))
        phi = X.S(X.V(PI2) * X.V(_f(rng.ranf())))
        a2 = X.S(X.V(sig_rr) * X.V(sig))
        del_xx = X.S(a2 * X.cos(X.V(phi)))
        del_yy = X.S(a2 * X.S(X.sin(X.V(phi))))

        if X.sqrt(X.V(del_x1) * X.V(del_x1) + X.V(del_y1) * X.V(del_y1)) <= (
            X.V(sig_r1) * X.V(rn_sig)
        ) and X.sqrt(X.V(del_xx) * X.V(del_xx) + X.V(del_yy) * X.V(del_yy)) <= (
            X.V(sig_rr) * X.V(rn_sig)
        ):
            break
    ray[1] = X.S(X.V(ray[1]) + X.V(del_xx) + X.V(del_x1) * X.V(dz_elem) * X.K(0.5))
    ray[3] = X.S(X.V(ray[3]) + X.V(del_yy) + X.V(del_y1) * X.V(dz_elem) * X.K(0.5))
    ray[2] = X.S(X.V(ray[2]) + X.V(del_x1))
    ray[4] = X.S(X.V(ray[4]) + X.V(del_y1))
    if DUMP:
        SCS.append(
            (
                int(ctx.i),
                sig,
                phi,
                del_x1,
                del_y1,
                del_xx,
                del_yy,
                sig_r1,
                sig_rr,
                dz_elem,
                ray[1],
                ray[2],
                ray[3],
            )
        )


def decay(ctx, rng):
    """DECAY (turtle.f:168-207)."""
    cost = _c(2.0 * _f(rng.ranf()) - 1.0)
    sint = F32(np.sqrt(_c(1.0) - cost * cost))
    pf, mf = _f(ctx.p), _f(ctx.mass)
    fpc = F32(pf * (cost + _f(ctx.fc)) / mf)
    fpn = F32(pf * (cost + _f(ctx.fn)) / mf)
    thetan = F32(sint / _f(fpn))
    ctx.pn = F32(_f(ctx.pstar) * _f(fpn))
    ec = F32(_f(ctx.pstar) * (_f(ctx.fc) * np.sqrt(pf * pf + mf * mf) + pf * cost) / mf)
    ctx.pc = F32(np.sqrt(_f(ec) * _f(ec) - _f(ctx.massc) ** 2))
    thetac = F32(sint * _f(ctx.pstar) / _f(ctx.pc))
    phi = F32(PI * _f(rng.ranf()))
    cosphi = F32(np.cos(_f(phi)))
    sinphi = F32(np.sin(_f(phi)))
    ray = ctx.ray
    rayc, rayn = ctx.rayc, ctx.rayn
    p0f = _f(ctx.p0)
    rayc[1] = ray[1]
    rayc[2] = F32(_f(ray[2]) + _f(cosphi) * _f(thetac))
    rayc[3] = ray[3]
    rayc[4] = F32(_f(ray[4]) + _f(sinphi) * _f(thetac))
    rayc[5] = ray[5]
    rayc[6] = F32((_f(ctx.pc) - p0f) / p0f)
    rayn[1] = ray[1]
    rayn[2] = F32(_f(ray[2]) - _f(cosphi) * _f(thetan))
    rayn[3] = ray[3]
    rayn[4] = F32(_f(ray[4]) - _f(sinphi) * _f(thetan))
    rayn[5] = ray[5]
    rayn[6] = F32((_f(ctx.pn) - p0f) / p0f)


# ---CHUNK-B2---

DISPATCH = {
    1: 210,
    2: 220,
    3: 230,
    4: 240,
    5: 250,
    6: 260,
    7: 270,
    8: 600,
    9: 290,
    10: 600,
    11: 600,
    12: 600,
    13: 600,
    14: 340,
    15: 600,
    16: 360,
    17: 600,
    18: 380,
    19: 390,
    20: 400,
    21: 410,
}
# label 720 dispatch (charged daughter continues inside the same element)
DISPATCH_D = {
    1: 600,
    2: 600,
    3: 235,
    4: 244,
    5: 254,
    6: 600,
    7: 600,
    8: 600,
    9: 600,
    10: 600,
    11: 600,
    12: 600,
    13: 600,
    14: 600,
    15: 600,
    16: 600,
    17: 600,
    18: 384,
    19: 394,
    20: 600,
    21: 600,
}


def rayrun(ctx, nct=0, out=None):
    """RAYRUN (turtle.f:1125-1581).  Label 610 is `GO TO 690`, so the
    neutral-daughter block 620-640 is dead code in the reference build.

    nct > 0 resumes from a checkpoint (see _ckpt): the loop-carried state
    at label 690 is exactly (nct, ctx, out.buf) -- every ray starts fresh
    at 100, and RAYRUN interleaves output records, so the output buffer
    must be checkpointed too."""
    from . import hist, fields

    rng = ctx.rng
    d = ctx.data
    idata = ctx.idata
    ray = ctx.ray
    r2 = ctx.ray2
    ckpt = _CKPT
    ckpt_every = _CKPT_EVERY
    while True:
        # ---- 100 ----
        nct += 1
        ctx.p0 = ctx.pbeam
        emit_my(ctx, rng)
        if _EMITDUMP:
            from . import formats as _F

            print(
                _F.render(
                    "1H0,'E',I4" + ",G22.15" * 5,
                    [nct] + [float(ray[j]) for j in range(1, 6)],
                ).decode("latin-1")[:-2]
            )
        ctx.z = F32(0.0)
        lflag = 0
        zd = F32(0.0)
        if ctx.dkflag:
            zd = fields.decayz(ctx, rng)
        iap = 0
        ctx.nhist = 0
        ctx.ip = 0
        ctx.ellips = False
        ctx.hyper = False
        ctx.apb[1] = F32(0.0)
        ctx.apb[2] = F32(0.0)
        ctx.mmax = 0
        inext = -10
        if ctx.mpa:
            for im in range(1, 21):
                ctx.db[im] = F32(0.0)
        # ---- 130 ----
        ctx.i = 1
        for kfl in range(3):
            for ifl in range(9):
                ctx.iflag[kfl, ifl] = False
        for nh in range(1, ctx.nhists + 1):
            ctx.set_[nh] = False
        goto = 200
        # ---- element loop ----
        while True:
            i = ctx.i
            if goto == 200:
                ntype = idata[i]
                last_ntype = int(ntype)
                if _SDUMP:
                    from . import formats as _F

                    print(
                        _F.render(
                            "1H0,'S',I5,I5,I4,1X,6G22.15",
                            [nct, i, int(ntype)]
                            + [float(ray[j]) for j in (1, 2, 3, 4)]
                            + [float(ctx.p), float(ctx.z)],
                        ).decode("latin-1")[:-2]
                    )
                if _MOMDUMP and nct == 2:
                    from . import formats as _F

                    print(
                        _F.render(
                            "1H0,'E',I5,I4,1X,6G22.15",
                            [i, int(ntype)]
                            + [float(ray[j]) for j in (1, 2, 3, 4)]
                            + [float(ctx.p), float(ctx.z)],
                        ).decode("latin-1")[:-2]
                    )
                    print(
                        _F.render(
                            "1H0,'D',I5,1X,8G22.15,1X,L1",
                            [i]
                            + [float(d[j]) for j in range(i + 1, i + 9)]
                            + [ctx.sec],
                        ).decode("latin-1")[:-2]
                    )
                if ntype == 53:
                    goto = 530
                    continue
                if ntype >= 50:
                    goto = 500
                    continue
                goto = DISPATCH[ntype]
                continue
            if goto == 210:
                if idata[i + 8] != lflag:
                    goto = 600
                    continue
                scatt_my(ctx)
                ctx.p = F32(_f(ctx.p) + _f(d[i + 7]))
                goto = 600
                continue
            if goto == 211:
                valx = [0.0] * 5
                rayadd = [0.0] * 5
                while True:
                    for ir in range(1, 5):
                        valx[ir] = _c(2.0 * _f(rng.ranf()) - 1.0)
                        rayadd[ir] = F32(_f(d[i + ir]) * valx[ir])
                    rn1 = valx[1] ** 2 + valx[3] ** 2
                    rn2 = valx[2] ** 2 + valx[4] ** 2
                    if rn1 <= 1.0 and rn2 <= 1.0:
                        break
                for ir in range(1, 5):
                    ray[ir] = F32(_f(ray[ir]) + rayadd[ir])
                v1 = _c(2.0 * _f(rng.ranf()) - 1.0)
                ctx.p = F32(_f(ctx.p) + _f(ctx.p0) * _f(d[i + 6]) * v1 + _f(d[i + 7]))
                goto = 600
                continue
            if goto == 218:
                xi1 = F32(np.sqrt(_c(-2.0) * _log(_f(rng.ranf()))))
                xi2 = F32(PI2 * _f(rng.ranf()))
                xr2 = F32(_f(xi1) * np.sin(_f(xi2)))
                ray[2] = F32(_f(ray[2]) + _f(xr2) * _f(d[i + 2]))
                yi1 = F32(np.sqrt(_c(-2.0) * _log(_f(rng.ranf()))))
                yi2 = F32(PI2 * _f(rng.ranf()))
                yr2 = F32(_f(yi1) * np.sin(_f(yi2)))
                ray[4] = F32(_f(ray[4]) + _f(yr2) * _f(d[i + 4]))
                goto = 600
                continue
            if goto == 220:
                if lflag == 2:
                    goto = 600
                    continue
                h = X.S(X.V(d[i + 1]) / X.V(ctx.p))
                tanb = X.S(X.V(d[i + 2]))
                tancor = X.S(X.V(tanb) - X.V(h) * X.V(d[i + 5]))
                r2[1] = X.S(X.V(ray[1]))
                r2[2] = X.S(X.V(ray[2]) + X.V(h) * X.V(ray[1]) * X.V(tanb))
                r2[3] = X.S(X.V(ray[3]))
                r2[4] = X.S(X.V(ray[4]) - X.V(h) * X.V(ray[3]) * X.V(tancor))
                if _QDUMP and nct == 1:
                    from . import formats as _F

                    print(
                        _F.render(
                            "1H0,'Q',I5,1X,3G22.15",
                            [i, float(h), float(tanb), float(tancor)],
                        ).decode("latin-1")[:-2]
                    )
                    print(
                        _F.render(
                            "1H0,'R',I5,1X,4G22.15",
                            [i] + [float(r2[j]) for j in (1, 2, 3, 4)],
                        ).decode("latin-1")[:-2]
                    )
                if ctx.sec:
                    secb = X.S(X.V(d[i + 3]))
                    sex = X.S(X.V(d[i + 4]))
                    r2[1] = X.S(
                        X.V(ray[1])
                        + X.K(0.5)
                        * X.V(h)
                        * (
                            X.P(X.V(secb) * X.V(ray[3]), 2)
                            - X.P(X.V(tanb) * X.V(ray[1]), 2)
                        )
                    )
                    r2[2] = X.S(
                        X.V(r2[2])
                        + X.V(h)
                        * (
                            X.P(X.V(tanb), 2)
                            * (X.V(ray[1]) * X.V(ray[2]) - X.V(ray[3]) * X.V(ray[4]))
                            + (X.V(h) * X.V(d[i + 6]) + X.V(sex)) * X.P(X.V(ray[1]), 2)
                            + (X.V(h) * X.V(d[i + 7]) - X.V(sex)) * X.P(X.V(ray[3]), 2)
                        )
                    )
                    r2[3] = X.S(
                        X.V(ray[3])
                        + X.V(h) * X.V(tanb) * X.V(tancor) * X.V(ray[1]) * X.V(ray[3])
                    )
                    r2[4] = X.S(
                        X.V(r2[4])
                        - X.V(h)
                        * (
                            X.V(tancor) * X.V(tanb) * X.V(ray[1]) * X.V(ray[4])
                            + (X.V(h) * X.V(d[i + 8]) + X.K(2.0) * X.V(sex))
                            * X.V(ray[1])
                            * X.V(ray[3])
                            + X.P(X.V(secb), 2) * X.V(ray[2]) * X.V(ray[3])
                        )
                    )
                el.reset(ctx, "ray", "ray2")
                goto = 600
                continue
            if goto == 230:
                ctx.ll = F32(d[i + 1])
                ll = _f(ctx.ll)
                if ctx.dkflag and lflag == 0 and _f(ctx.z) + ll >= _f(zd):
                    ctx.ll = F32(_f(zd) - _f(ctx.z))
                    ll = _f(ctx.ll)
                    ray[1] = X.S(X.R(ray[1]) + X.R(ll) * X.R(ray[2]))
                    ray[3] = X.S(X.R(ray[3]) + X.R(ll) * X.R(ray[4]))
                    goto = 700
                    continue
                ray[1] = X.S(X.R(ray[1]) + X.R(ll) * X.R(ray[2]))
                ray[3] = X.S(X.R(ray[3]) + X.R(ll) * X.R(ray[4]))
                goto = 590
                continue
            if goto == 240:
                iap += 1
                if el.bstop(ctx, lflag + 1):
                    goto = 650
                    continue
                ctx.ll = F32(d[i + 1])
                ll = _f(ctx.ll)
                if not ctx.dkflag:
                    goto = 244
                    continue
                if lflag - 1 < 0:
                    goto = 241
                    continue
                if lflag - 1 == 0:
                    goto = 244
                    continue
                goto = 245
                continue
            if goto == 241:
                if _f(ctx.z) + _f(ctx.ll) < _f(zd):
                    goto = 244
                    continue
                ctx.ll = F32(_f(zd) - _f(ctx.z))
                if el.bend(ctx):
                    goto = 650
                    continue
                goto = 700
                continue
            if goto == 244:
                if DUMP and nct <= 4:
                    BAS.append((int(i), nct, [float(ray[j]) for j in range(1, 5)]))
                if el.bend(ctx):
                    if DUMP and nct <= 4:
                        BBS.append(
                            (
                                int(i),
                                nct,
                                [float(ray[j]) for j in range(1, 5)]
                                + [float(ctx.ray2[j]) for j in range(1, 5)],
                            )
                        )
                    goto = 650
                    continue
                if DUMP and nct <= 4:
                    BBS.append(
                        (
                            int(i),
                            nct,
                            [float(ray[j]) for j in range(1, 5)]
                            + [float(ctx.ray2[j]) for j in range(1, 5)],
                        )
                    )
                goto = 249
                continue
            if goto == 245:
                ll = _f(ctx.ll)
                if _f(d[i + 4]) == 0.0:
                    goto = 247
                    continue
                theta = F32(ll * _f(d[i + 2]))
                tanth = F32(np.tan(_f(theta)))
                the2 = F32(
                    (_f(ray[2]) + _f(tanth)) / (_c(1.0) - _f(ray[2]) * _f(tanth))
                )
                f = F32(
                    np.sqrt((_c(1.0) + _f(the2) ** 2) / (_c(1.0) + _f(ray[2]) ** 2))
                )
                d4 = _f(d[i + 4])
                ray[1] = F32(_f(f) * (_f(ray[1]) + d4) - d4)
                ray[2] = the2
                ray[3] = F32(
                    _f(ray[3]) + (d4 + _f(ray[1])) * np.sin(_f(theta)) * _f(ray[4])
                )
                ray[4] = F32(_f(f) * _f(ray[4]))
                goto = 249
                continue
            if goto == 247:
                ll = _f(ctx.ll)
                ray[1] = F32(_f(ray[1]) + ll * _f(ray[2]))
                ray[3] = F32(_f(ray[3]) + ll * _f(ray[4]))
                goto = 249
                continue
            if goto == 249:
                if el.bstop(ctx, lflag + 1):
                    goto = 650
                    continue
                goto = 590
                continue
            if goto == 250:
                iap += 1
                if el.qstop(ctx, lflag + 1):
                    goto = 650
                    continue
                ctx.ll = F32(d[i + 1])
                ll = _f(ctx.ll)
                if lflag == 2:
                    goto = 255
                    continue
                ctx.gtop = F32(_c(0.5) * _f(d[i + 1]) * _f(d[i + 2]) / _f(ctx.p))
                if ctx.mmax != 0:
                    el.multi(ctx)
                if ctx.dkflag and lflag == 0 and _f(ctx.z) + ll >= _f(zd):
                    ctx.ll = F32(_f(zd) - _f(ctx.z))
                    el.quad(ctx)
                    goto = 700
                    continue
                goto = 254
                continue
            if goto == 254:
                el.quad(ctx)
                if ctx.mmax != 0:
                    el.multi(ctx)
                goto = 259
                continue
            if goto == 255:
                ll = _f(ctx.ll)
                ray[1] = F32(_f(ray[1]) + ll * _f(ray[2]))
                ray[3] = F32(_f(ray[3]) + ll * _f(ray[4]))
                goto = 259
                continue
            if goto == 259:
                if el.qstop(ctx, lflag + 1):
                    goto = 650
                    continue
                goto = 590
                continue
            if goto == 260:
                iap += 1
                ifp = idata[i + 1] // 100
                iff = idata[i + 1] - 100 * ifp
                if ifp != lflag:
                    goto = 267
                    continue
                ifg = idata[i + 3]
                pos = _f(d[i + 2]) >= 0.0
                if ifg != 0:
                    rad2 = (_f(ray[iff]) / _f(d[i + 2])) ** 2 + (
                        _f(ray[ifg]) / _f(d[i + 4])
                    ) ** 2
                    if (pos and rad2 < 1.0) or (not pos and rad2 > 1.0):
                        goto = 267
                        continue
                    goto = 266
                    continue
                if (pos and abs(_f(ray[iff])) < _f(d[i + 2])) or (
                    not pos and abs(_f(ray[iff])) > abs(_f(d[i + 2]))
                ):
                    goto = 267
                    continue
                goto = 266
                continue
            if goto == 266:
                ctx.i = i + el.nu(ctx, 6)
                ntype = idata[ctx.i]
                if ntype == 1 and idata[ctx.i + 8] == lflag:
                    goto = 211
                    continue
                goto = 650
                continue
            if goto == 267:
                ctx.i = i + el.nu(ctx, 6)
                if ctx.i > ctx.i1:
                    goto = 690
                    continue
                ntype = idata[ctx.i]
                if ntype == 1 and idata[ctx.i + 8] == lflag:
                    goto = 600
                    continue
                goto = 200
                continue
            if goto == 270:
                for j in range(1, 7):
                    ray[j] = F32(_f(ray[j]) + _f(d[i + j]))
                ctx.p = F32(_f(ctx.p) + _f(d[i + 6]) * _f(ctx.p0))
                goto = 600
                continue
            if goto == 290:
                el.repeat(ctx)
                goto = 600
                continue
            if goto == 340:
                nrow = idata[i + 7]
                if i != inext:
                    el.reset(ctx, "ray2", "ray")
                acc = 0.0
                for ir in range(1, 7):
                    acc = acc + _f(ray[ir]) * _f(d[i + ir])
                r2[nrow] = F32(acc)
                if ctx.sec and idata[i + 8] == 0:
                    ipl = i + 8
                    for ib in range(1, 7):
                        for jc in range(ib, 7):
                            ipl += 1
                            r2[nrow] = F32(
                                _f(r2[nrow]) + _f(ray[ib]) * _f(ray[jc]) * _f(d[ipl])
                            )
                inext = i + el.nu(ctx, 14)
                if idata[inext] != 14:
                    el.reset(ctx, "ray", "ray2")
                goto = 600
                continue
            if goto == 360:
                nm = idata[i + 1]
                if nm > 0:
                    goto = 362
                    continue
                if lflag == 2:
                    goto = 600
                    continue
                nm = -nm
                ctx.db[nm] = F32(d[i + 2])
                ctx.cosm[nm] = F32(d[i + 3])
                ctx.sinm[nm] = F32(d[i + 4])
                maxx = max(nm, ctx.mmax)
                ctx.mmax = 0
                for im in range(1, maxx + 1):
                    if _f(ctx.db[im]) != 0.0:
                        ctx.mmax = im
                goto = 600
                continue
            if goto == 362:
                if nm == 4 or nm == 5:
                    ctx.apb[nm - 3] = F32(d[i + 2])
                    goto = 600
                    continue
                if nm == 11:
                    ctx.p0 = F32(d[i + 2])
                    ray[6] = F32((_f(ctx.p) - _f(ctx.p0)) / _f(ctx.p0))
                    goto = 600
                    continue
                if nm == 100:
                    ctx.ellips = True
                    ctx.qap[1] = F32(d[i + 2])
                    ctx.qap[2] = F32(d[i + 3])
                    goto = 600
                    continue
                if nm == 101:
                    ctx.hyper = True
                    ctx.qap[3] = F32(d[i + 2])
                    goto = 600
                    continue
                goto = 600
                continue
            if goto == 380:
                ctx.ll = F32(d[i + 1])
                if not ctx.dkflag:
                    goto = 384
                    continue
                if lflag - 1 < 0:
                    goto = 381
                    continue
                if lflag - 1 == 0:
                    goto = 384
                    continue
                goto = 235
                continue
            if goto == 381:
                if _f(ctx.z) + _f(ctx.ll) < _f(zd):
                    goto = 384
                    continue
                ctx.ll = F32(_f(zd) - _f(ctx.z))
                el.sext(ctx)
                goto = 700
                continue
            if goto == 384:
                el.sext(ctx)
                goto = 590
                continue
            if goto == 390:
                ctx.ll = F32(d[i + 1])
                if not ctx.dkflag:
                    goto = 394
                    continue
                if lflag - 1 < 0:
                    goto = 391
                    continue
                if lflag - 1 == 0:
                    goto = 394
                    continue
                goto = 235
                continue
            if goto == 391:
                if _f(ctx.z) + _f(ctx.ll) < _f(zd):
                    goto = 394
                    continue
                ctx.ll = F32(_f(zd) - _f(ctx.z))
                el.solo(ctx)
                goto = 700
                continue
            if goto == 394:
                el.solo(ctx)
                goto = 590
                continue
            if goto == 400:
                cs = F32(d[i + 1])
                sn = F32(d[i + 2])
                csf, snf = _f(cs), _f(sn)
                r2[1] = F32(_f(ray[1]) * csf + _f(ray[3]) * snf)
                r2[3] = F32(-_f(ray[1]) * snf + _f(ray[3]) * csf)
                r2[2] = F32(_f(ray[2]) * csf + _f(ray[4]) * snf)
                r2[4] = F32(-_f(ray[2]) * snf + _f(ray[4]) * csf)
                el.reset(ctx, "ray", "ray2")
                goto = 600
                continue
            if goto == 410:
                th = _f(d[i + 1])
                xr1 = F32(np.sqrt(-_c(2.0) * _log(_f(rng.ranf()))))
                xr2 = F32(PI * _f(rng.ranf()))
                ray[2] = F32(_f(ray[2]) + th * _f(xr1) * np.sin(_f(xr2)))
                xr3 = F32(np.sqrt(-_c(2.0) * _log(_f(rng.ranf()))))
                xr4 = F32(PI * _f(rng.ranf()))
                ray[4] = F32(_f(ray[4]) + th * _f(xr3) * np.sin(_f(xr4)))
                goto = 600
                continue
            if goto == 500:
                ctx.nhist += 1
                if lflag != ctx.kflag[ctx.nhist]:
                    goto = 600
                    continue
                nco = int(ctx.ncoor[ctx.nhist])
                ctx.value[ctx.nhist] = el.hstval(ctx, nco)
                ctx.set_[ctx.nhist] = True
                goto = 600
                continue
            if goto == 530:
                ifl = idata[i + 1]
                ctx.iflag[lflag, ifl - 1] = True
                goto = 600
                continue
            if goto == 590:
                ctx.z = F32(_f(ctx.z) + _f(d[i + 1]))
                goto = 600
                continue
            if goto == 600:
                ctx.i = i
                i = i + el.nu(ctx, idata[i])
                ctx.i = i
                if DUMP and nct in DUMP_RAYS:
                    ELS.append(
                        (
                            nct,
                            float(ctx.z),
                            int(i),
                            [float(ray[j]) for j in range(1, 7)] + [float(ctx.p)],
                        )
                    )
                if i <= ctx.i1:
                    goto = 200
                    continue
                goto = 690
                continue
            if goto == 650:
                ctx.istop[lflag, iap] += 1
                for k in range(1, ctx.loss + 1):
                    if lflag != ctx.kflg[k]:
                        continue
                    m = int(ctx.nblk[k])
                    nx = int(ctx.lthx[k])
                    nux = int(ctx.nunx[k])
                    x = el.hstval(ctx, nux)
                    nuy = int(ctx.nuny[k])
                    if nuy == 0:
                        hist.histo(
                            ctx,
                            _f(x),
                            m,
                            nx,
                            _f(ctx.xstrt[k]),
                            _f(ctx.xend[k]),
                            _f(ctx.xbin[k]),
                        )
                        continue
                    ny = int(ctx.lthy[k])
                    y = el.hstval(ctx, nuy)
                    hist.entmat(
                        ctx,
                        _f(x),
                        _f(y),
                        m,
                        _f(ctx.xstrt[k]),
                        _f(ctx.xend[k]),
                        nx,
                        _f(ctx.xbin[k]),
                        _f(ctx.ystrt[k]),
                        _f(ctx.yend[k]),
                        ny,
                        _f(ctx.ybin[k]),
                    )
                goto = 690
                continue
            if goto == 690:
                hist.ehist(ctx)
                if DUMP and nct <= 4:
                    RUNS.append(
                        (
                            nct,
                            float(ctx.z),
                            int(ctx.i),
                            last_ntype,
                            int(ctx.ip),
                            float(ctx.p),
                        )
                    )
                if nct < ctx.norays:
                    if ckpt and nct % ckpt_every == 0:
                        _save_ckpt(ctx, nct, ckpt, out)
                    break
                return
            if goto == 700:
                decay(ctx, rng)
                ray[:] = ctx.rayc
                ctx.p = ctx.pc
                lflag = 1
                goto = DISPATCH_D[idata[i]]
                continue
            if goto == 235:
                ll = _f(ctx.ll)
                ray[1] = F32(_f(ray[1]) + ll * _f(ray[2]))
                ray[3] = F32(_f(ray[3]) + ll * _f(ray[4]))
                goto = 590
                continue
            raise AssertionError("bad label %d" % goto)
