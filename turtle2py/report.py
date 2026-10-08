"""Output routines: exact ports of PRINT1, HEDING, HISCAP, RDSKIP messages,
DIGITAL, BCDWR, LOADX, TRHIST, OUTMAT, OHIST, APLIM (turtle.f).

All WRITE(NOUT,fmt) go through formats.render with the literal FORMAT string.
Watcom convention: intermediates float64, rounded to float32 at assignment.
"""

import numpy as np

from . import formats as F
from . import elements as el
from . import x87 as X

F32 = np.float32

_MOMDUMP = __import__("os").environ.get("MOMDUMP") == "1"


def _c(v):
    return float(np.float32(v))


# /BLOC42/ h-constants as 4-byte little-endian words
def _w(s):
    return (
        int(s.encode("latin-1").ljust(4)[:4], 0)
        if False
        else int.from_bytes(s.encode("latin-1"), "little")
    )


TABLE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SEMI4 = _w("&")
BLANKW = _w("    ")
FORW = _w("FOR ")
RAYS = _w("RAYS")


def digital(int_, ir):
    """DIGITAL (turtle.f:1889-1907) -> single character."""
    if int_ > 9999:
        int_ = 9999
    model = 10 ** (4 - ir)
    mite = int_ // model
    iten = mite % 10
    if iten > 0:
        return TABLE[iten]
    if ir == 4 or mite >= 10:
        return TABLE[0]
    return " "


def bcdwr(intger):
    """BCDWR (turtle.f:1675-1692) -> single character."""
    if intger <= 0:
        return " "
    if intger <= 35:
        return TABLE[intger]
    return "&"


def loadx(num):
    """LOADX (turtle.f:730-746) -> list of 100 chars."""
    na = min(int(num), 100)
    xss = ["X"] * 100
    if na < 100:
        for j in range(na, 100):
            xss[j] = " "
    return xss


def print1(ctx, label, nword, datum, vary):
    """PRINT1 (turtle.f:2030-2074)."""
    NV = [6, 1, 1, 3, 2, 0, 0, 6, 0, 1, 0, 0, 0, 6, 0, 2, 0, 2, 2, 1, 1]
    ntype = float(datum[0])
    ktype = abs(int(ntype))
    char = [" "] * 12
    if ktype != 15:
        if ntype > 0:
            kv = 1
            if ntype <= 21:
                kv = NV[int(ntype) - 1]
            if kv != 0:
                lv = 0
                for jv in range(1, kv + 1):
                    vark = int(vary[jv])  # VARY(JV+1), 0-based here
                    k = abs(vark)
                    if vark >= 0:
                        lv += 1
                    else:
                        lv += 1
                        char[lv - 1] = "-"
                        lv += 1
                    char[lv - 1] = TABLE[k]
        if nword <= 1:
            return F.render("1H0,I4,1H.,12A1,2H ',A4,3H' ;", [ntype, char, label])
        args = [ntype, char, label]
        for j in range(2, int(nword) + 1):
            args.append(" ")
            args.append(float(datum[j - 1]))
        args.append(";")
        return F.render(
            "1H0,I4,1H.,12A1,2H ',A4,2H' ,A1,8(F11.5,A1)/(27X,8(F11.5,A1))", args
        )
    return F.render(
        "1H0,I4,1H.,13X,1H',A4,2H' ,F12.5,4H   ',A4,4H'   ,F12.5,2H ;",
        [ntype, label, float(datum[1]), float(datum[2]), float(datum[3])],
    )


LABEL = [
    ["DIST", "RIBU", "TION", " OF "],
    ["HORI", "ZONT", "AL A", "XIS "],
    ["VERT", "ICAL", " AXI", "S    "],
]


def hiscap(ctx, out, iopt, nun, kfl, zh, nfl):
    """HISCAP (turtle.f:591-642)."""
    if nun <= 11:
        n1 = ctx.nom[nun - 1]
        n2 = ctx.name[nun - 1]
    else:
        j = nun - 20
        n1 = ctx.nom1[j - 1]
        n2 = ctx.name[j - 1]
        if j > 2:
            n2 = ctx.name[6]
    part = ["    ", "    "]
    if ctx.dkflag:
        part[0] = "FOR "
        part[1] = ctx.kpart[kfl - 1]
    if iopt > 3:
        j = iopt - 3
        out.write(
            F.render(
                "1X,5A4,' IN ',A4,5X,2A4,5X,F12.3,1X,A4, ' FROM THE TARGET'",
                LABEL[j - 1] + [n1, n2],
            )
        )
        return
    j = iopt
    if nfl == 0:
        out.write(
            F.render(
                "1X,5A4,' IN ',A4,5X,2A4,5X,F12.3,1X,A4, ' FROM THE TARGET'",
                LABEL[j - 1] + [n1, n2] + part + [zh, ctx.name[7]],
            )
        )
        return
    zfl = _c(float(ctx.zflag[nfl]) / float(ctx.unit[7]))
    out.write(
        F.render(
            "1X,5A4,' IN ',A4,5X,2A4,5X,F12.3,1X,A4,"
            " ' FROM THE TARGET, FLAG AT ',F12.3,1X,A4",
            LABEL[j - 1] + [n1, n2] + part + [zh, ctx.name[7], zfl, ctx.name[7]],
        )
    )


def heding(ctx, out):
    """HEDING (turtle.f:495-589)."""
    out.write(
        F.render(
            "1H1/'0THE FOLLOWING HISTOGRAMS REFER TO',I8,"
            " ' RAYS PASSING THROUGH THE ABOVE BEAM LINE'",
            [ctx.norays],
        )
    )
    out.write(F.render("1X,82(1H=)", []))
    kh = 0
    na = za = kfla = nfla = None
    for k in range(1, ctx.nhists + 1):
        nav = int(ctx.mtype[k])
        if nav == 1:
            kh += 1
            n = int(ctx.ncoor[k])
            z = _c(float(ctx.zhist[k]) / float(ctx.unit[7]))
            kfl = int(ctx.kflag[k]) + 1
            nfl = int(ctx.nflag[k])
            out.write(F.render("'0HISTOGRAM NO',I3", [kh]))
            hiscap(ctx, out, 1, n, kfl, z, nfl)
        elif nav == 2:
            na = int(ctx.ncoor[k])
            za = _c(float(ctx.zhist[k]) / float(ctx.unit[7]))
            kfla = int(ctx.kflag[k]) + 1
            nfla = int(ctx.nflag[k])
        else:
            kh += 1
            nd = int(ctx.ncoor[k])
            zd = _c(float(ctx.zhist[k]) / float(ctx.unit[7]))
            kfld = int(ctx.kflag[k]) + 1
            nfld = int(ctx.nflag[k])
            out.write(F.render("'0HISTOGRAM NO',I3", [kh]))
            hiscap(ctx, out, 2, na, kfla, za, nfla)
            hiscap(ctx, out, 3, nd, kfld, zd, nfld)
    if ctx.loss != 0:
        for k in range(1, ctx.loss + 1):
            kh += 1
            kfl = int(ctx.kflg[k]) + 1
            out.write(
                F.render(
                    "'0HISTOGRAM NO',I3,' OF ',A4,' LOST'", [kh, ctx.kpart[kfl - 1]]
                )
            )
            n = int(ctx.nunx[k])
            na = int(ctx.nuny[k])
            if na == 0:
                hiscap(ctx, out, 4, n, 0, 0.0, 0)
                continue
            hiscap(ctx, out, 5, n, 0, 0.0, 0)
            hiscap(ctx, out, 6, na, 0, 0.0, 0)
    if not ctx.dkflag or ctx.zmax == 0.0:
        return
    zmaxx = _c(float(ctx.zmax) / float(ctx.unit[7]))
    fac = _c(
        1.0 / (1.0 - np.exp(-float(ctx.zmax) / (float(ctx.fld) * float(ctx.pbeam))))
    )
    out.write(
        F.render(
            "1H0,84(1H*)/43H * ALL PARENT PARTICLES ARE FORCED TO DECAY,"
            "8H WITHIN ,F10.3,1X,A4,19H FROM THE TARGET. */"
            "56H * THE NUMBER OF DECAYS WILL BE ENHANCED BY A FACTOR OF,"
            "F8.3,21H (AVERAGE VALUE)    */1X,84(1H*))",
            [zmaxx, ctx.name[7], fac],
        )
    )


def _i(v):
    """Fortran REAL -> INTEGER conversion (Watcom x87 cvttss32): truncate
    toward zero, saturate to 2**31-1 when non-finite/out of range."""
    v = float(np.float32(v))
    if not np.isfinite(v):
        return 2147483647
    t = int(np.trunc(v))
    if t > 2147483647:
        return 2147483647
    if t < -2147483648:
        return -2147483648
    return t


def trhst(ctx, out, nhst, m, a, d, nhtyp):
    """TRHIST (turtle.f:1583-1645)."""
    mt = ctx.mtable
    nhsi = nhst - 1
    nsum = mt[nhsi + m + 3]
    more = m + 1
    lim = m + 2
    aa = np.float32(a)
    if nsum == 0.0:
        out.write(F.render("//,'0HISTOGRAM IS EMPTY'", []))
        return
    if nhtyp == 21:
        r1 = np.float32(a)
        for i in range(1, m + 1):
            r2 = _c(r1 + d)
            sss = _c(float(np.float32(3.14159265)) * (float(r2) + float(r1)) * float(d))
            mt[nhsi + i] = F32(float(mt[nhsi + i]) / float(sss))
            r1 = r2
    nscale = np.float32(0.0)
    for i in range(1, m + 1):
        if mt[nhsi + i] > nscale:
            nscale = mt[nhsi + i]
    out.write(
        F.render(
            "1H0/11X,'INTERVAL',30X,'SCALE FACTOR.. 100 X\"S EQUAL',I6,' ENTRIES'",
            [nscale],
        )
    )
    out.write(F.render("10X,' UNDERFLOW',2X,I5,1X,1HI,/1X,28(1H=)", [mt[nhsi + lim]]))
    for i in range(1, m + 1):
        ab = _c(aa + d)
        num = _i(float(mt[nhsi + i]) * 100.0 / float(nscale))
        out.write(
            F.render(
                "1H ,F8.3,' TO ',F8.3,1X,I5,1X,1HI,1X,100A1",
                [aa, ab, mt[nhsi + i], loadx(num)],
            )
        )
        aa = ab
    out.write(F.render("1X,28(1H=),/10X,' OVERFLOW ',2X,I5,1X,1HI", [mt[nhsi + more]]))
    out.write(
        F.render(
            "1H0,10X,'TOTAL NUMBER OF ENTRIES =',I8,"
            "' INCLUDING UNDERFLOW AND OVERFLOW'/",
            [nsum],
        )
    )


def outmat(ctx, out, iplot, amin, na, da, dmin, nd, dd):
    """OUTMAT (turtle.f:871-1012)."""
    mt = ctx.mtable
    iploi = iplot - 1
    mtt = (na + 1) * (nd + 1) + 5
    if mt[iploi + mtt] <= 0.0:
        out.write(F.render("//,'0HISTOGRAM IS EMPTY'", []))
        return
    nla = na // 10 + 1
    alabel = [np.float32(amin)]
    for n in range(2, nla + 1):
        alabel.append(_c(alabel[n - 2] + 10.0 * da))
    out.write(F.render("1H0/16X,11F10.3", alabel))
    nall = na + 4
    iarow = [" "] * 111
    tot = "TOTALS"
    for n in range(1, 7):
        iarow[nall + n - 1] = tot[n - 1]
    out.write(F.render("1H+,22X,110A1", iarow[0 : nall + 6]))
    # upper X axis
    ict = 1
    nam = na + 1
    for i in range(1, nam + 1):
        iarow[i - 1] = "*" if ict in (1, 5) else "-"
        ict += 1
        if ict == 6:
            ict = 1
    iarow[na + 1] = "I"
    nap = na + 10
    for i in range(na + 3, nap + 1):
        iarow[i - 1] = "-"
    out.write(F.render("1H ,20X,'I*',110A1", iarow[0:nap]))
    # body
    mm = 0
    nap = na + 9
    dlow = np.float32(dmin)
    dhigh = _c(dmin + dd)
    for n in range(1, nd + 1):
        for k in range(1, nap + 1):
            iarow[k - 1] = " "
        for k in range(1, na + 1):
            mm += 1
            iarow[k - 1] = bcdwr(_i(mt[iploi + mm]))
        iarow[na] = " "
        iarow[na + 1] = "I"
        mm += 1
        nn = _i(mt[iploi + mm])
        for k in range(1, 5):
            iarow[na + k + 4] = digital(nn, k)
        out.write(
            F.render("1H ,F8.3,' TO',F8.3,' I ',110A1", [dlow, dhigh, iarow[0:nap]])
        )
        dlow = _c(dlow + dd)
        dhigh = _c(dlow + dd)
    # lower X axis
    ict = 1
    for i in range(1, na + 2):
        iarow[i - 1] = "*" if ict in (1, 5) else "-"
        ict += 1
        if ict == 6:
            ict = 1
    iarow[na + 1] = "I"
    nap = na + 10
    for i in range(na + 3, nap + 1):
        iarow[i - 1] = "-"
    out.write(F.render("1H ,20X,'I*',110A1", iarow[0:nap]))
    # sums of columns
    nam = na + 2
    for k in range(1, nap + 1):
        iarow[k - 1] = " "
    iarow[nam - 1] = "I"
    out.write(F.render("1H ,20X,'I ',110A1", iarow[0:nap]))
    for ir in range(1, 5):
        for k in range(1, na + 1):
            mm += 1
            iarow[k - 1] = digital(_i(mt[iploi + mm]), ir)
        mm += 1
        if ir == 4:
            nn = _i(mt[iploi + mm])
            for k in range(1, 5):
                iarow[na + k + 4] = digital(nn, k)
            out.write(F.render("1H ,12X,'TOTALS',2X,'I ',110A1", iarow[0:nap]))
        else:
            out.write(F.render("1H ,20X,'I ',110A1", iarow[0:nap]))
            mm -= na + 1
    # summary
    iarow[0] = _i(mt[iploi + mtt])
    for i in range(1, 5):
        iarow[i] = _i(mt[iploi + mm + i])
    out.write(
        F.render(
            "1H0,10X,'TOTAL NUMBER OF ENTRIES =',I8,"
            "' INCLUDING UNDERFLOW AND OVERFLOW AS FOLLOWS'"
            "/1H0,32X,'UNDERFLOW',7X,'OVERFLOW',"
            "/20X,'ACROSS',2(5X,I10)/20X,'DOWN  ',2(5X,I10)/",
            iarow[0:5],
        )
    )


def ohist(ctx, out):
    """OHIST (turtle.f:748-869)."""
    nh = 0
    nuna = za = amin = da = kfla = nfla = facta = None
    for k in range(1, ctx.nhists + 1):
        m = int(ctx.nentry[k])
        n = int(ctx.intvls[k])
        nunit = int(ctx.ncoor[k])
        fact, legal = el.hstun(ctx, nunit)
        if not legal:
            out.write(
                F.render(
                    "'0THE COORDINATE SPECIFICATION ON THE "
                    "HISTOGRAM CARD ABOVE HAS NO MEANING TO "
                    "TURTLE. HISTOGRAM IGNORED.'",
                    [],
                )
            )
            continue
        xbeg = _c(float(ctx.begin[k]) / float(fact))
        dx = _c(float(ctx.step[k]) / float(fact))
        zc = _c(float(ctx.zhist[k]) / float(ctx.unit[7]))
        kfl = int(ctx.kflag[k]) + 1
        nfl = int(ctx.nflag[k])
        nav = int(ctx.mtype[k])
        if nav == 1:
            nh += 1
            out.write(F.render("1H1/'0HISTOGRAM NO',I3", [nh]))
            hiscap(ctx, out, 1, nunit, kfl, zc, nfl)
            trhst(ctx, out, m, n, xbeg, dx, nunit)
            s = float(ctx.mtable[m + n + 2])
            if s == 0.0:
                continue
            if _MOMDUMP:
                print(
                    F.render(
                        "1H0,'M1',I3,1X,G22.15,1X,G22.15",
                        [k, float(ctx.xmom[k]), float(ctx.xmom2[k])],
                    ).decode("latin-1")[:-2]
                )
            xm = X.S(X.R(ctx.xmom[k]) / X.R(fact))
            xm2 = X.S(X.sqrt(X.R(ctx.xmom2[k])) / X.R(fact))
            out.write(
                F.render("11X,'CENTER =',F10.5,3X,'RMS HALF WIDTH =',F10.5", [xm, xm2])
            )
        elif nav == 2:
            nuna = nunit
            za = zc
            amin = xbeg
            da = dx
            kfla = kfl
            nfla = nfl
            facta = fact
        else:
            nh += 1
            out.write(F.render("1H1/'0HISTOGRAM NO',I3", [nh]))
            hiscap(ctx, out, 2, nuna, kfla, za, nfla)
            hiscap(ctx, out, 3, nunit, kfl, zc, nfl)
            outmat(ctx, out, m, amin, n, da, xbeg, n, dx)
            mtt = m + (n + 1) * (n + 1) + 4
            s = float(ctx.mtable[mtt])
            if s == 0.0:
                continue
            if _MOMDUMP:
                print(
                    F.render(
                        "1H0,'M2',I3,1X,G22.15,1X,G22.15,1X,G22.15,1X,G22.15,1X,G22.15",
                        [
                            k,
                            *[
                                float(v)
                                for v in (
                                    ctx.xmom[k],
                                    ctx.xmom2[k],
                                    ctx.ymom[k],
                                    ctx.ymom2[k],
                                    ctx.corr[k],
                                )
                            ],
                        ],
                    ).decode("latin-1")[:-2]
                )
            # Watcom evaluates the whole summary expression in x87
            # extended, rounding only at the XM/XM2/YM/YM2/COR stores;
            # XM is reloaded as REAL*4 for the cancellation terms.
            # Verified 2026-10-05 against mid_ref.res (100k rays): the
            # float64 chain drifts RMS HALF WIDTH by 1 ULP at F10.5.
            fa = X.R(facta)
            fy = X.R(fact)
            xm = X.S(X.R(ctx.xmom[k]) / (X.R(s) * fa))
            xm2 = X.S(
                X.sqrt(X.R(ctx.xmom2[k]) / (X.R(s) * X.P(fa, 2)) - X.P(X.R(xm), 2))
            )
            ym = X.S(X.R(ctx.ymom[k]) / (X.R(s) * fy))
            ym2 = X.S(
                X.sqrt(X.R(ctx.ymom2[k]) / (X.R(s) * X.P(fy, 2)) - X.P(X.R(ym), 2))
            )
            cor = X.S(X.R(ctx.corr[k]) / (X.R(s) * fa * fy) - X.R(xm) * X.R(ym))
            cor = X.S(X.R(cor) / (X.R(xm2) * X.R(ym2)))
            out.write(
                F.render("11X,'CENTER =',F10.5,3X,'RMS HALF WIDTH =',F10.5", [xm, xm2])
            )
            out.write(
                F.render("11X,'CENTER =',F10.5,3X,'RMS HALF WIDTH =',F10.5", [ym, ym2])
            )
            out.write(F.render("11X,'CORRELATION =',F10.5", [cor]))
    if ctx.loss == 0:
        return
    for k in range(1, ctx.loss + 1):
        nh += 1
        kfl = int(ctx.kflg[k]) + 1
        out.write(
            F.render(
                "1H1/'0HISTOGRAM NO',I3,' OF ',A4,' LOST'", [nh, ctx.kpart[kfl - 1]]
            )
        )
        m = int(ctx.nblk[k])
        n = int(ctx.lthx[k])
        nunit = int(ctx.nunx[k])
        fact, legal = el.hstun(ctx, nunit)
        xbeg = _c(float(ctx.xstrt[k]) / float(fact))
        dx = _c(float(ctx.xbin[k]) / float(fact))
        nund = int(ctx.nuny[k])
        if nund == 0:
            hiscap(ctx, out, 4, nunit, 0, 0.0, 0)
            trhst(ctx, out, m, n, xbeg, dx, nunit)
            continue
        nd = int(ctx.lthy[k])
        fact, legal = el.hstun(ctx, nund)
        dmin = _c(float(ctx.ystrt[k]) / float(fact))
        dd = _c(float(ctx.ybin[k]) / float(fact))
        hiscap(ctx, out, 5, nunit, 0, 0.0, 0)
        hiscap(ctx, out, 6, nund, 0, 0.0, 0)
        outmat(ctx, out, m, xbeg, n, dx, dmin, nd, dd)


def aplim(ctx, out):
    """APLIM (turtle.f:116-166)."""
    last = 3 if ctx.dkflag else 1
    out.write(
        F.render(
            "1H1/'0SUMMARY OF PARTICLES STOPPED BY APERTURES'"
            "/1X,41(1H=)/1H0,10X,7HPOSITON,8X,4HTYPE,3(8X,A4)",
            ctx.kpart[:last],
        )
    )
    kstop = [0, 0, 0]
    iap = 0
    i = 1
    zc = np.float32(0.0)
    fz = _c(1.0 / float(ctx.unit[7]))
    type_ = ["BEND", "QUAD", "SLIT"]
    disp = {3: 50, 4: 30, 5: 30, 6: 30, 9: 60, 11: 50, 18: 50, 19: 50}
    while True:
        ntype = int(ctx.idata[i])
        if ntype <= 0 or ntype > 21:
            tgt = 90
        else:
            tgt = disp.get(ntype, 90)
        if tgt == 30:
            iap += 1
            if (
                int(ctx.istop[0][iap]) + int(ctx.istop[1][iap]) + int(ctx.istop[2][iap])
                == 0
            ):
                tgt = 50
            else:
                for j in range(1, last + 1):
                    kstop[j - 1] += int(ctx.istop[j - 1][iap])
                ctx.z = F32(float(zc) * float(fz))
                out.write(
                    F.render(
                        "1X,F15.3,1X,A4,5X,A4,3I12",
                        [ctx.z, ctx.name[7], type_[ntype - 4]]
                        + [int(ctx.istop[j - 1][iap]) for j in range(1, last + 1)],
                    )
                )
                tgt = 50
        if tgt == 50:
            if ntype != 6:
                zc = _c(float(zc) + float(ctx.data[i + 1]))
        elif tgt == 60:
            el.repeat(ctx)
        i += el.nu(ctx, ntype)
        if i > ctx.i1:
            break
    out.write(F.render("' TOTAL',24X,3I12", kstop[:last]))
