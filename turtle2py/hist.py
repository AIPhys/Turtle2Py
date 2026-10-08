"""Histogram entry: exact ports of HISTO, ENTMAT, EHIST
(turtle.f:644-667, 446-493, 373-444).

Watcom implicit typing: I,J,K,L,M,N,O are INTEGER, so L, IA, ID, MM, NAT,
NDT, NOV, NRET, NAA, NTT, MTT, MATR are INTEGER (truncation toward zero on
assignment from a REAL expression).  Intermediates float64, rounded to
float32 at each REAL assignment.
"""

import numpy as np

from . import x87 as X
from . import formats as F

_MOMDUMP = __import__("os").environ.get("MOMDUMP") == "1"

F32 = np.float32


def _f(v):
    return float(v)


def _c(v):
    return float(np.float32(v))


def _i(v):
    """INTEGER assignment from a REAL expression (truncate toward zero)."""
    v = float(np.float32(v))
    if not np.isfinite(v):
        return 2147483647
    t = int(np.trunc(v))
    return max(-2147483648, min(2147483647, t))


def _trunc_ext(x, a, d, lit):
    """INTEGER assignment L = (X-A)/D + lit as Watcom F77 computes it.

    Exact model (verified 2026-10-07 against probe43s.res: 0 mismatches on
    all 8861886 near-boundary HISTO lines; probe43.res is bit-identical to
    test_ref.res, so the dump does not perturb the run):

      1. the subtraction (X-A) is stored ROUNDED TO REAL*4 (f32),
      2. the division by D runs in x87 extended (64-bit mantissa),
      3. the REAL*4 literal is added in x87 extended,
      4. the INTEGER assignment truncates the EXTENDED value (no f32 store).

    Earlier models (float64 division, no f32 rounding of the difference,
    truncation of an f32-rounded L) each flip a bin when the value lands
    within ~1 ULP of an integer: 56 bin-boundary trades in the 5M run.
    Fast path: with the f32-rounded numerator, float64 and extended division
    differ by < 1e-14 at these magnitudes, so trunc(float64) is exact
    whenever the value is > 1e-9 from an integer; the mp path runs only
    near boundaries.

    Operands arrive as numpy float32 (ctx.step/ctx.da arrays); mpmath
    mpf() accepts only Python floats, so cast them (crash of 2026-10-07,
    ray ~134k: TypeError: cannot create mpf from np.float32(0.001)).
    """
    q = float(np.float32(x - a))
    d = float(d)
    if d == 0.0:
        # x87 division by zero yields +/-inf (masked); the REAL->INTEGER
        # conversion (FIST) returns integer-indeterminate 0x80000000.
        return -2147483648
    t = q / d + lit
    if not np.isfinite(t):
        return -2147483648
    n = int(t)
    if abs(t - n) > 1e-9 and abs(t - (n + 1)) > 1e-9:
        return n
    return int(X.mp.mpf(q) / X.mp.mpf(d) + X.mp.mpf(lit))


_LIT100001 = float(np.float32(1.00001))  # 1.0000100135803223


def histo(ctx, x, nhst, m, a, b, dx):
    """HISTO(X, NHST, M, A, B, DX) (turtle.f:644-667)."""
    t = ctx.mtable
    n = nhst - 1
    t[n + m + 3] = F32(_f(t[n + m + 3]) + 1.0)
    if x - b >= 0.0:
        # 102
        t[n + m + 1] = F32(_f(t[n + m + 1]) + 1.0)
        return
    # 104
    if x - a < 0.0:
        t[n + m + 2] = F32(_f(t[n + m + 2]) + 1.0)
        return
    # 108
    l = _trunc_ext(x, a, dx, _LIT100001)
    t[n + l] = F32(_f(t[n + l]) + 1.0)


def entmat(ctx, a, d, matrix, amin, amax, na, da, dmin, dmax, nd, dd):
    """ENTMAT(A,D,MATRIX,AMIN,AMAX,NA,DA,DMIN,DMAX,ND,DD) (turtle.f:446-493)."""
    t = ctx.mtable
    matr = _i(matrix - 1.0)
    naa = na + 1
    ntt = naa * (nd + 1)
    mtt = ntt + 5
    nret = 0
    if a - amin < 0.0:
        nret = 1
    elif a - amax > 0.0:
        nret = 2
    elif d - dmin < 0.0:
        nret = 3
    elif d - dmax > 0.0:
        nret = 4
    if nret:
        # 35/36
        nov = ntt + nret
        t[matr + nov] = F32(_f(t[matr + nov]) + 1.0)
        t[matr + mtt] = F32(_f(t[matr + mtt]) + 1.0)
        return
    # 40
    ia = _trunc_ext(a, amin, da, 1.0)
    id_ = _trunc_ext(d, dmin, dd, 1.0)
    mm = (id_ - 1) * naa + ia
    nat = id_ * naa
    ndt = nd * naa + ia
    t[matr + mm] = F32(_f(t[matr + mm]) + 1.0)
    t[matr + ntt] = F32(_f(t[matr + ntt]) + 1.0)
    t[matr + nat] = F32(_f(t[matr + nat]) + 1.0)
    t[matr + ndt] = F32(_f(t[matr + ndt]) + 1.0)
    t[matr + mtt] = F32(_f(t[matr + mtt]) + 1.0)


def ehist(ctx):
    """EHIST (turtle.f:373-444)."""
    scalx = False
    for nh in range(1, ctx.nhists + 1):
        nfl = ctx.nflag[nh]
        kfl = ctx.kflag[nh] + 1
        navel = ctx.mtype[nh]
        if navel == 1:
            # 100: one dimensional histogram
            if nfl > 0 and not ctx.iflag[kfl - 1, nfl - 1]:
                continue
            if not ctx.set_[nh]:
                continue
            val = _f(ctx.value[nh])
            if _MOMDUMP:
                print(
                    F.render(
                        "1H0,'V',I3,1X,7G22.15",
                        [nh, val]
                        + [_f(ctx.ray[k]) for k in (1, 2, 3, 4)]
                        + [_f(ctx.p), _f(ctx.z)],
                    ).decode("latin-1")[:-2]
                )
            m = ctx.nentry[nh]
            n = ctx.intvls[nh]
            histo(ctx, val, m, n, ctx.begin[nh], ctx.end[nh], ctx.step[nh])
            # Watcom evaluates the moment updates in x87 extended
            # (64-bit mantissa), rounding at the XMOM/XMOM2 stores --
            # EXCEPT that the Fortran `**` operator returns REAL*4, so
            # (VAL-XM)**2 and SM**2 are f32-rounded temporaries.  Verified
            # 2026-10-05 bit-exactly against probe25.res moments replayed
            # from the Fortran VAL stream (probe/xm2_var2.py, k=7,8,19,21,
            # 23,25); the all-extended chain drifts the RMS half width by
            # 1 ULP at F10.5 on mid_ref.res (100k rays).
            sm = X.R(ctx.mtable[m + n + 2])
            xm = X.R(ctx.xmom[nh])
            ctx.xmom[nh] = X.S(((sm - 1.0) * xm + X.R(val)) / sm)
            d2 = X.S(X.P(X.R(val) - xm, 2))
            s2 = X.S(sm * sm)
            ctx.xmom2[nh] = X.S(
                (sm - 1.0) * (sm * X.R(ctx.xmom2[nh]) + X.R(d2)) / X.R(s2)
            )
        elif navel == 2:
            # 200: X coordinate of 2D histogram
            scalx = False
            if nfl > 0 and not ctx.iflag[kfl - 1, nfl - 1]:
                continue
            if not ctx.set_[nh]:
                continue
            scalx = True
            a = _f(ctx.value[nh])
            if _MOMDUMP:
                print(F.render("1H0,'V',I3,1X,G22.15", [nh, a]).decode("latin-1")[:-2])
            na = ctx.intvls[nh]
            amin = _f(ctx.begin[nh])
            amax = _f(ctx.end[nh])
            da = _f(ctx.step[nh])
        elif navel == 3:
            # 300: Y coordinate of 2D histogram
            if nfl > 0 and not ctx.iflag[kfl - 1, nfl - 1]:
                continue
            if not (ctx.set_[nh] and scalx):
                continue
            d = _f(ctx.value[nh])
            if _MOMDUMP:
                print(F.render("1H0,'V',I3,1X,G22.15", [nh, d]).decode("latin-1")[:-2])
            m = ctx.nentry[nh]
            nd = ctx.intvls[nh]
            dmin = _f(ctx.begin[nh])
            dd = _f(ctx.step[nh])
            entmat(
                ctx,
                a,
                d,
                m,
                amin,
                amax,
                na,
                da,
                dmin,
                _f(ctx.end[nh]),
                nd,
                dd,
            )
            # Watcom accumulates in x87 extended and rounds only at each
            # store; the float64 chain double-rounds (53-bit then 24-bit)
            # and drifts the running sums.  Verified 2026-10-05 against
            # mid_ref.res (100k rays): 11 RMS HALF WIDTH lines off by 1 ULP.
            ctx.xmom[nh] = X.S(X.R(ctx.xmom[nh]) + X.R(a))
            ctx.xmom2[nh] = X.S(X.R(ctx.xmom2[nh]) + X.R(a) * X.R(a))
            ctx.ymom[nh] = X.S(X.R(ctx.ymom[nh]) + X.R(d))
            ctx.ymom2[nh] = X.S(X.R(ctx.ymom2[nh]) + X.R(d) * X.R(d))
            ctx.corr[nh] = X.S(X.R(ctx.corr[nh]) + X.R(a) * X.R(d))
