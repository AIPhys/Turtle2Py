"""System setup: exact ports of INITZE, ZERO, DECAYP, SETUP and the main
program driver of turtle.f (lines 1-114, 168-232, 1647-1671, 1936-1965,
2554-3056).

Watcom convention: REAL*4 variables; intermediates in float64, rounded to
float32 at every Fortran variable assignment (_c).  INTEGER assignment from a
REAL expression truncates toward zero (_i).  Fortran 1-based arrays map to the
padded numpy arrays in Context (index 0 unused).
"""

import sys

import numpy as np

from . import formats as F
from . import elements as el
from . import x87 as X
from . import report
from . import tracking
from .io import CardReader, ElementReader, StopInput, unpack
from .random import G900
from .state import Context

F32 = np.float32
V = X.V
S = X.S
K = X.K
P = X.P


def _c(v):
    """Assign a REAL expression to a REAL*4 variable."""
    return float(np.float32(v))


def _i(v):
    """Assign a REAL expression to an INTEGER variable (truncate, saturate)."""
    v = float(np.float32(v))
    if not np.isfinite(v):
        return 2147483647
    t = int(np.trunc(v))
    if t > 2147483647:
        return 2147483647
    if t < -2147483648:
        return -2147483648
    return t


class Out:
    """Unit NOUT: bytes accumulated in memory as CRLF records."""

    def __init__(self):
        self.buf = bytearray()

    def write(self, b):
        self.buf += b

    def save(self, path):
        with open(path, "wb") as fh:
            fh.write(self.buf)


def plain(s):
    """Render a message string built by io.py (carriage control embedded,
    '/' terminating records) as CRLF records."""
    out = bytearray()
    for rec in s.split("/"):
        out += rec.encode("latin-1")
        out += b"\r\n"
    return bytes(out)


def flush_msg(er, out):
    """Write the messages accumulated by RDELMT/RDSKIP, in order."""
    for m in er.msg:
        out.write(m if isinstance(m, (bytes, bytearray)) else plain(m))
    del er.msg[:]


# --------------------------------------------------------------------------
def initze(ctx):
    """INITZE (turtle.f:1936-1965)."""
    for j in range(1, 10):
        ctx.zflag[j] = F32(-1.0)
    ctx.sec = False
    ctx.cap[0] = ctx.cap[1] = ctx.cap[2] = False
    ctx.mpa = False
    ctx.bdb = F32(0.0)
    ctx.apb[1] = F32(0.0)
    ctx.apb[2] = F32(0.0)
    ctx.layl = F32(0.5)
    ctx.layx = F32(0.0)
    ctx.rab1 = F32(0.0)
    ctx.rab2 = F32(0.0)


def zero(ctx):
    """ZERO (turtle.f:1647-1671): clears histogram storage."""
    n = slice(1, ctx.nhists + 1)
    ctx.xmom[n] = 0.0
    ctx.xmom2[n] = 0.0
    ctx.ymom[n] = 0.0
    ctx.ymom2[n] = 0.0
    ctx.corr[n] = 0.0
    ctx.mtable[1 : ctx.limno + 1] = 0.0
    ctx.istop[:, 1:501] = 0


def decayp(ctx, datum):
    """DECAYP (turtle.f:208-232); DATUM is the current element's list."""
    u = ctx.unit
    ctx.mass = F32(_c(float(datum[1]) * float(u[10])))
    ctx.massc = F32(_c(float(datum[2]) * float(u[10])))
    ctx.massn = F32(_c(float(datum[3]) * float(u[10])))
    ctx.fld = F32(_c(0.299 * float(datum[4]) / float(ctx.mass)))
    m, mc, mn = float(ctx.mass), float(ctx.massc), float(ctx.massn)
    pstar = _c(
        np.sqrt(float((m + mc + mn) * (m + mc - mn) * (m - mc + mn) * (m - mc - mn)))
        / _c(2.0 * m)
    )
    ctx.pstar = F32(pstar)
    ctx.fc = F32(_c(np.sqrt(pstar**2 + mc**2) / pstar))
    ctx.fn = F32(_c(np.sqrt(pstar**2 + mn**2) / pstar))


def decayz(ctx, rng):
    """DECAYZ (turtle.f:234-249).  Returns ZD."""
    x = rng.ranf()
    ld = _c(float(ctx.fld) * float(ctx.p))
    if float(ctx.zmax) != 0.0:
        x = _c(1.0 - _c(x * _c(1.0 - _c(np.exp(-float(ctx.zmax) / ld)))))
    return F32(_c(-ld * _c(np.log(x))))


# --------------------------------------------------------------------------
_TYPE_LABEL = {t: t for t in range(1, 22)}


class _Setup:
    """SETUP (turtle.f:2554-3056) as a label-driven state machine.

    Locals mirror the Fortran locals; DATUM is the current element's list
    (WORK is EQUIVALENCE(DATUM)), NFL is EQUIVALENCE(VARY(2)).
    """

    def __init__(self, ctx, reader, er, out):
        self.ctx, self.reader, self.er, self.out = ctx, reader, er, out
        self.iface = -10
        self.inext = -10
        self.zc = 0.0
        self.tanb = self.secb = self.tcor = self.sb = 0.0
        self.na = self.da = self.astrt = self.aend = 0.0
        self.nuna = 0
        self.intvl = 0
        self.zl = [0.0] * 5
        self.m = 0
        self.label = 10

    def run(self):
        while True:
            h = _SETUP_LABELS.get(self.label)
            if h is None:
                raise KeyError("SETUP label %s" % (self.label,))
            h(self)
            if self.label == 0:
                return


def setup(ctx, reader, er, out):
    _Setup(ctx, reader, er, out).run()


def _skip(s):
    """RDSKIP messages: nothing is written when there are no comments."""
    msgs = s.reader.rdskip()
    if msgs:
        s.out.write(plain("/".join(msgs)))


def _l10(s):
    """10: READ TITLE."""
    ctx, out = s.ctx, s.out
    s.reader.rdnext(2)
    _skip(s)
    words, lw = s.reader.rdstrg(20)
    out.write(F.render("1H1//1X,20A4", words))
    _skip(s)
    ctx.norays, _iflg = s.reader.rdfix()
    s.reader.rdnext(-1)
    out.write(F.render("'0NUMBER OF RAYS',I8", [ctx.norays]))
    s.er.indic = 0
    s.label = 50


def _l50(s):
    """50: clear DATA and defaults."""
    ctx = s.ctx
    ctx.data[:] = 0.0
    ctx.i = 1
    ctx.nhists = 0
    ctx.limno = 0
    s.zc = 0.0
    ctx.dkflag = False
    ctx.loss = 0
    ctx.kpart = ["RAYS", "RAYS", "RAYS"]
    ctx.zmax = F32(0.0)
    ctx.ip = 0
    s.er.flush = False
    for j in range(11):
        ctx.name[j] = _NORIG[j]
        ctx.unit[j] = F32(_UORIG[j])
    s.label = 100


def _l100(s):
    """100: CALL RDELMT."""
    ctx, er, out = s.ctx, s.er, s.out
    nword, er.flush = er.rdelmt()
    flush_msg(er, out)
    nword = er.e.nword
    if nword == 0:
        s.label = 600
        return
    if er.flush:
        s.label = 100
        return
    i = ctx.i
    if i + el.nu(ctx, er.e.ntype) <= 3001:
        s.label = 200
        return
    out.write(F.render("21H0DATA OVERFLOW, NEL =,I4,6H   I =,I6", [0, i]))
    er.flush = True
    s.label = 100


def _l200(s):
    """200: dispatch on element type."""
    er = s.er
    if float(er.e.datum[0]) < 0.0:
        s.label = 100
        return
    t = er.e.ntype
    if t == 60:
        s.label = 550
    elif t == 53:
        s.label = 480
    elif t >= 50:
        s.label = 450
    elif 1 <= t <= 21:
        s.label = _TYPE_LABEL[t]
    else:
        s.label = 100


def _l500(s):
    """490/500: accumulate length and data pointer, list the element."""
    ctx = s.ctx
    ctx.i = ctx.i + el.nu(ctx, s.er.e.ntype)
    zzc = _c(s.zc / float(ctx.unit[7]))
    s.out.write(F.render("1H+,110X,F8.2,2X,I4", [zzc, ctx.i]))
    s.label = 100


def _l490(s):
    """490: ZC = ZC + L, then 500."""
    s.zc = _c(s.zc + float(s.ctx.l))
    _l500(s)


def _l210(s):
    """210: BEAM."""
    ctx, w = s.ctx, s.er.e.datum
    if s.er.e.nword >= 9:
        s.label = 212
        return
    ctx.pbeam = S(V(w[7]) * V(ctx.unit[10]))
    ctx.p0 = ctx.pbeam
    for ib in range(1, 7):
        ctx.raymax[ib] = S(V(w[ib]) * V(ctx.unit[ib - 1]))
    s.label = 100


def _l212(s):
    """212: BEAM stored in DATA."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 1
    for ib in range(1, 7):
        d[i + ib] = S(V(w[ib]) * V(ctx.unit[ib - 1]))
    d[i + 7] = S(V(w[7]) * V(ctx.unit[10]))
    idata[i + 8] = _i(float(w[8]) / 100.0 + 0.001)
    s.label = 500


def _l220(s):
    """220: MAGNET POLE FACE ROTATION."""
    ctx, idata, w, i = s.ctx, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 2
    # Watcom keeps the FACE product in the x87 register through the TAN/COS
    # calls: the library sees the UNROUNDED extended value, while FACE itself
    # is stored REAL*4.  Verified 2026-10-05 on probe31.res (SETUP label 220,
    # 6 unique face values / 20 occurrences): TAN(FACE) and 1/COS(FACE) match
    # bit-for-bit with the extended argument (0/6); the rounded argument is
    # off on 2/6 (face 0.048241887, 0.079811789).
    face_e = V(w[1]) * V(ctx.unit[6])
    face = S(face_e)
    tanb = S(X.tan(face_e))
    secb = S(V(1.0) / X.cos(face_e))
    tcor = S(V(2.0) * V(ctx.apb[2]) * V(ctx.layl))
    sb = S(V(secb) * (V(1.0) + V(2.0) * P(V(tanb), 2)))
    ctx.face = F32(face)
    s.tanb, s.secb, s.tcor, s.sb = tanb, secb, tcor, sb
    if i == s.inext:
        s.label = 221
        return
    s.iface = i
    s.label = 500


def _l221(s):
    """221: FRINGE FIELD AT MAGNET EXIT."""
    ctx, d, i = s.ctx, s.ctx.data, s.ctx.i
    tanb, secb, tcor, sb = V(s.tanb), V(s.secb), V(s.tcor), V(s.sb)
    hv, p0v, nv = V(ctx.h), V(ctx.p0), V(ctx.n)
    rab2, layx = V(ctx.rab2), V(ctx.layx)
    d[i + 1] = S(-hv * p0v)
    d[i + 2] = S(-tanb)
    d[i + 3] = S(secb)
    d[i + 4] = S(nv * hv * tanb - V(0.5) * rab2 * P(secb, 3))
    d[i + 5] = S(tcor * sb * (V(1.0) - hv * layx * tcor * tanb))
    d[i + 6] = S(-V(0.5) * P(tanb, 3))
    d[i + 7] = d[i + 6]
    d[i + 8] = S(-tanb * P(secb, 2))
    s.inext = -10
    s.label = 500


def _l230(s):
    """230: DRIFT SPACE."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 3
    ctx.l = S(V(w[1]) * V(ctx.unit[7]))
    d[i + 1] = ctx.l
    s.label = 490


def _l240(s):
    """240: BENDING MAGNET."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 4
    ctx.l = S(V(w[1]) * V(ctx.unit[7]))
    ctx.h = S(V(w[2]) * V(ctx.unit[8]) / (K(33.356) * V(ctx.p0)))
    ctx.n = S(w[3])
    d[i + 1] = ctx.l
    d[i + 2] = ctx.h
    d[i + 3] = ctx.n
    if i != s.iface + el.nu(ctx, 2):
        s.label = 245
        return
    tanb, secb, tcor, sb = V(s.tanb), V(s.secb), V(s.tcor), V(s.sb)
    hv, nv, rab1, layx = V(ctx.h), V(ctx.n), V(ctx.rab1), V(ctx.layx)
    d[s.iface + 1] = S(hv * V(ctx.p0))
    d[s.iface + 2] = S(tanb)
    d[s.iface + 3] = S(secb)
    d[s.iface + 4] = S(V(0.5) * rab1 * P(secb, 3) - nv * hv * tanb)
    d[s.iface + 5] = S(tcor * sb * (V(1.0) - hv * layx * tcor * tanb))
    d[s.iface + 6] = S(0.0)
    d[s.iface + 7] = S(tanb * (V(0.5) + P(tanb, 2)))
    d[s.iface + 8] = S(0.0)
    s.label = 245


def _l245(s):
    """245: bending magnet body."""
    ctx, d, i = s.ctx, s.ctx.data, s.ctx.i
    d[i + 1] = ctx.l
    d[i + 2] = ctx.h
    d[i + 3] = ctx.n
    d[i + 4] = 0.0
    d[i + 5] = 0.0
    s.inext = i + el.nu(ctx, 4)
    if float(d[i + 2]) == 0.0:
        s.label = 490
        return
    d[i + 4] = S(V(1.0) / V(d[i + 2]))
    if ctx.sec:
        d[i + 5] = S(V(ctx.bdb) * P(V(d[i + 4]), 2))
    s.label = 490


def _l250(s):
    """250: QUADRUPOLE."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 5
    ctx.l = S(V(w[1]) * V(ctx.unit[7]))
    d[i + 1] = ctx.l
    d[i + 2] = S(V(w[2]) * V(ctx.unit[8]) / (V(w[3]) * V(ctx.unit[0]) * K(33.356)))
    d[i + 3] = S(P(V(w[3]) * V(ctx.unit[0]), 2))
    s.label = 490


def _l260(s):
    """260: SLIT."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 6
    iff = _i(float(w[1]) + 0.001)
    idata[i + 1] = iff
    iun = iff % 100
    if iun <= 0 or iun > 6:
        s.label = 100
        return
    d[i + 2] = F32(_c(float(w[2]) * float(ctx.unit[iun - 1])))
    ifg = _i(float(w[3]) + 0.001)
    iun = ifg % 100
    if iun < 0 or iun > 6:
        s.label = 100
        return
    idata[i + 3] = iun
    d[i + 4] = F32(0.0)
    if iun != 0:
        d[i + 4] = F32(_c(float(w[4]) * float(ctx.unit[iun - 1])))
    s.label = 500


def _l270(s):
    """270: DISPLACEMENT OF RAY."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 7
    for ib in range(1, 7):
        d[i + ib] = F32(_c(float(w[ib]) * float(ctx.unit[ib - 1])))
    s.label = 500


def _l280(s):
    """280: MISALIGNMENTS - not supported, STOP."""
    s.out.write(F.render("'0THIS PROGRAM WILL NOT DO MISALIGNMENTS'", []))
    raise SystemExit(0)


def _l290(s):
    """290: REPEAT."""
    ctx, idata, w, i = s.ctx, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 9
    idata[i + 1] = _i(float(w[1]) + 0.001)
    if idata[i + 1] == 0:
        s.zc = _c(s.zc + float(ctx.ic[ctx.ip] - 1) * (s.zc - s.zl[ctx.ip]))
        ctx.ip = ctx.ip - 1
        s.label = 500
        return
    ctx.ip = ctx.ip + 1
    ctx.ic[ctx.ip] = idata[i + 1]
    s.zl[ctx.ip] = s.zc
    s.label = 500


def _l300(s):
    s.label = 100


def _l310(s):
    s.label = 100


def _l320(s):
    s.label = 100


def _l330(s):
    """330: INPUT OUTPUT OPTIONS."""
    kode = _i(float(s.er.e.datum[1]) + 0.001)
    kfl = kode // 100
    if kode - 100 * kfl != 10:
        s.label = 100
        return
    s.ctx.cap[kfl] = True
    s.label = 100


def _l340(s):
    """340: ARBITRARY MATRIX."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 14
    nrow = _i(float(w[7]) + 0.001)
    for ib in range(1, 7):
        d[i + ib] = F32(
            _c(float(w[ib]) * float(ctx.unit[nrow - 1]) / float(ctx.unit[ib - 1]))
        )
    idata[i + 7] = nrow
    if ctx.sec and s.er.e.nword > 8:
        idata[i + 8] = 0
        ipl = 9
        for ib in range(1, 7):
            for ic in range(ib, 7):
                ipl += 1
                d[ipl + i - 1] = F32(
                    _c(
                        float(w[ipl - 1])
                        * float(ctx.unit[nrow - 1])
                        / (float(ctx.unit[ib - 1]) * float(ctx.unit[ic - 1]))
                    )
                )
    else:
        idata[i + 8] = 1
    s.label = 500


def _l350(s):
    """350: UNITS."""
    ctx, w = s.ctx, s.er.e.datum
    nun = _i(float(w[1]) + 0.001)
    if nun == 0:
        for j in range(11):
            ctx.name[j] = _NORIG[j]
            ctx.unit[j] = F32(_UORIG[j])
        s.label = 100
        return
    ctx.name[nun - 1] = unpack(s.er.e.text(3))
    ctx.unit[nun - 1] = F32(_c(float(w[3]) * _UORIG[nun - 1]))
    if nun > 2:
        s.label = 100
        return
    ctx.unit[nun + 1] = ctx.unit[nun - 1]
    ctx.name[nun + 1] = ctx.name[nun - 1]
    s.label = 100


def _l360(s):
    """360: MULTIPOLE ABERRATIONS / BENDING MAGNET PARAMETERS."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 16
    nm = _i(abs(float(w[1])) + 0.001)
    if float(w[1]) > 0.0:
        s.label = _MPA_LABEL.get(nm, 100)
        return
    if nm <= 20:
        ctx.mpa = True
        idata[i + 1] = -nm
        d[i + 2] = F32(_c(float(w[2]) / float(ctx.unit[0]) ** (nm - 2)))
        angle = _c(float(w[3]) / 57.29578)
        d[i + 3] = F32(_c(np.cos(angle)))
        d[i + 4] = F32(_c(np.sin(angle)))
        s.label = 500
        return
    s.out.write(F.render("'0INDEX OF MULTIPOLE MAY NOT EXCEED 20'", []))
    raise SystemExit(0)


def _l362(s):
    s.ctx.bdb = F32(_c(float(s.er.e.datum[2]) / float(s.ctx.unit[0]) ** 2))
    s.label = 100


def _l363(s):
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    nm = _i(abs(float(w[1])) + 0.001)
    ctx.apb[nm - 3] = F32(_c(float(w[2]) * float(ctx.unit[2 * nm - 8])))
    idata[i + 1] = nm
    d[i + 2] = ctx.apb[nm - 3]
    s.label = 500


def _l3635(s):
    s.zc = _c(float(s.er.e.datum[2]) * float(s.ctx.unit[7]))
    s.label = 100


def _l364(s):
    s.ctx.layl = F32(s.er.e.datum[2])
    s.label = 100


def _l365(s):
    s.ctx.layx = F32(s.er.e.datum[2])
    s.label = 100


def _l3655(s):
    s.ctx.zmax = F32(_c(float(s.er.e.datum[2]) * float(s.ctx.unit[7])))
    s.label = 100


def _l3657(s):
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    ctx.p0 = F32(_c(float(w[2]) * float(ctx.unit[10])))
    idata[i + 1] = 11
    d[i + 2] = ctx.p0
    s.label = 500


def _l366(s):
    s.ctx.rab1 = F32(_c(float(s.er.e.datum[2]) / float(s.ctx.unit[7])))
    s.label = 100


def _l367(s):
    s.ctx.rab2 = F32(_c(float(s.er.e.datum[2]) / float(s.ctx.unit[7])))
    s.label = 100


def _l368(s):
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i + 1] = 100
    d[i + 2] = F32(_c(float(w[2]) * float(ctx.unit[0])))
    d[i + 3] = F32(_c(float(w[3]) * float(ctx.unit[2])))
    s.label = 500


def _l369(s):
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i + 1] = 101
    d[i + 2] = F32(_c(0.5 * (float(w[2]) * float(ctx.unit[0])) ** 2))
    s.label = 500


def _l3695(s):
    nm = _i(abs(float(s.er.e.datum[1])) + 0.001)
    s.ctx.kpart[nm - 200] = s.er.e.lable
    s.label = 100


def _l370(s):
    s.ctx.sec = True
    s.label = 500


def _l380(s):
    """380: SEXTUPOLE."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 18
    ctx.l = F32(_c(float(w[1]) * float(ctx.unit[7])))
    d[i + 1] = ctx.l
    d[i + 2] = F32(
        _c(
            float(w[2])
            * float(ctx.unit[8])
            / ((float(w[3]) * float(ctx.unit[0])) ** 2 * 33.356)
        )
    )
    s.label = 490


def _l390(s):
    """390: SOLENOID."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 19
    ctx.l = F32(_c(float(w[1]) * float(ctx.unit[7])))
    d[i + 1] = ctx.l
    d[i + 2] = F32(_c(0.5 * float(w[2]) * float(ctx.unit[8]) / 33.356))
    s.label = 490


def _l400(s):
    """400: BEAM ROTATION."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 20
    angle = _c(float(w[1]) * float(ctx.unit[6]))
    d[i + 1] = F32(_c(np.cos(angle)))
    d[i + 2] = F32(_c(np.sin(angle)))
    s.label = 500


def _l410(s):
    """410: THIN FOIL."""
    ctx, d, idata, w, i = s.ctx, s.ctx.data, s.ctx.idata, s.er.e.datum, s.ctx.i
    idata[i] = 21
    d[i + 1] = F32(_c(float(w[1]) * float(ctx.unit[1])))
    s.label = 500


def _l450(s):
    """450: SET UP HISTOGRAM."""
    ctx, w, er = s.ctx, s.er.e.datum, s.er
    kode = _i(float(w[1]) + 0.001)
    kfl = kode // 100
    nun = kode - 100 * kfl
    fact, legal = el.hstun(ctx, nun)
    if not legal:
        s.label = 100
        return
    s.m = m = ctx.limno + 1
    w[2] = F32(_c(float(w[2]) * fact))
    w[3] = F32(_c(float(w[3]) * fact))
    w[4] = F32(_c(float(w[4]) * fact))
    if float(w[4]) == 0.0:
        w[4] = F32(_c((float(w[3]) - float(w[2])) / 100.0))
    if float(w[4]) == 0.0:
        w[4] = F32(0.001)
    s.intvl = _i(max(_c((float(w[3]) - float(w[2])) / float(w[4])), 1.0) + 0.001)
    ninny = er.ntype - 49
    s.label = {1: 452, 2: 454, 3: 456}[ninny]


def _l452(s):
    """452: ONE DIMENSIONAL HISTOGRAM."""
    ctx, w = s.ctx, s.er.e.datum
    nun = _i(float(w[1]) + 0.001) % 100
    kfl = _i(float(w[1]) + 0.001) // 100
    lim = ctx.limno + s.intvl + 3
    if lim > 10000:
        s.label = 470
        return
    ctx.limno = lim
    if nun != 8:
        s.label = 460
        return
    ctx.loss = ctx.loss + 1
    j = ctx.loss
    ctx.xstrt[j] = w[2]
    ctx.xend[j] = w[3]
    ctx.lthx[j] = s.intvl
    ctx.xbin[j] = w[4]
    ctx.nunx[j] = 8
    ctx.nuny[j] = 0
    ctx.nblk[j] = s.m
    ctx.kflg[j] = kfl
    s.label = 100


def _l454(s):
    """454: SET X SCALE (HORIZONTAL)."""
    ctx, w = s.ctx, s.er.e.datum
    nun = _i(float(w[1]) + 0.001) % 100
    s.astrt = float(w[2])
    s.aend = float(w[3])
    s.na = min(s.intvl, 100)
    s.da = _c((float(w[3]) - float(w[2])) / float(s.na))
    s.nuna = nun
    s.label = 460 if nun != 8 else 100


def _l456(s):
    """456: Y SCALE (VERTICAL)."""
    ctx, w = s.ctx, s.er.e.datum
    nun = _i(float(w[1]) + 0.001) % 100
    kfl = _i(float(w[1]) + 0.001) // 100
    lim = ctx.limno + (s.na + 1) * (s.intvl + 1) + 5
    if lim > 10000:
        s.label = 470
        return
    ctx.limno = lim
    if nun != 8 and s.nuna != 8:
        s.label = 460
        return
    ctx.loss = ctx.loss + 1
    j = ctx.loss
    ctx.xstrt[j] = F32(s.astrt)
    ctx.xend[j] = F32(s.aend)
    ctx.lthx[j] = s.na
    ctx.xbin[j] = F32(s.da)
    ctx.nunx[j] = s.nuna
    ctx.ystrt[j] = w[2]
    ctx.yend[j] = w[3]
    ctx.lthy[j] = s.intvl
    ctx.ybin[j] = w[4]
    ctx.nuny[j] = nun
    ctx.nblk[j] = s.m
    ctx.kflg[j] = kfl
    s.label = 100


def _l460(s):
    """460: STORE HISTOGRAM DATA TO DATA ARRAY."""
    ctx, w, i = s.ctx, s.er.e.datum, s.ctx.i
    kode = _i(float(w[1]) + 0.001)
    kfl = kode // 100
    nun = kode - 100 * kfl
    ctx.idata[i] = 50
    ctx.nhists = ctx.nhists + 1
    k = ctx.nhists
    ctx.mtype[k] = _i(float(w[0])) - 49
    s.label = 461


def _l461(s):
    """460 continued: fill the /BLOC7/ histogram table."""
    ctx, w = s.ctx, s.er.e.datum
    kode = _i(float(w[1]) + 0.001)
    kfl = kode // 100
    nun = kode - 100 * kfl
    k = ctx.nhists
    ctx.nentry[k] = s.m
    ctx.ncoor[k] = nun
    ctx.begin[k] = w[2]
    ctx.end[k] = w[3]
    ctx.step[k] = w[4]
    ctx.intvls[k] = s.intvl
    ctx.zhist[k] = F32(s.zc)
    ctx.nflag[k] = s.er.e.vary[1]
    ctx.kflag[k] = kfl
    s.label = 500


def _l470(s):
    """470: HISTOGRAM SPACE OVERFLOW."""
    s.out.write(
        F.render(
            "'0THE HISTOGRAM SPECIFIED ABOVE CAUSED A STORAGE OVERFLOW,'"
            " ' IT HAS BEEN IGNORED.'",
            [],
        )
    )
    s.label = 100


def _l480(s):
    """480: FLAG FOR HISTOGRAM ENTRY."""
    ctx, i = s.ctx, s.ctx.i
    ctx.idata[i] = 53
    nfl = s.er.e.vary[1]
    ctx.idata[i + 1] = nfl
    ctx.zflag[nfl] = F32(s.zc)
    s.label = 500


def _l550(s):
    """550: PREPARE FOR DECAY CALCULATION."""
    s.ctx.dkflag = True
    s.ctx.sec = True
    decayp(s.ctx, s.er.e.datum)
    s.label = 100


def _l600(s):
    """600: END OF INPUT DATA."""
    if s.er.flush:
        s.label = 10
        return
    s.ctx.i1 = s.ctx.i - 1
    s.out.write(F.render("'0SENTINEL'", []))
    s.label = 0


# --------------------------------------------------------------------------
# label dispatch tables (Fortran computed GOTOs)
_TYPE_LABEL = {
    1: 210,
    2: 220,
    3: 230,
    4: 240,
    5: 250,
    6: 260,
    7: 270,
    8: 280,
    9: 290,
    10: 300,
    11: 310,
    12: 320,
    13: 330,
    14: 340,
    15: 350,
    16: 360,
    17: 370,
    18: 380,
    19: 390,
    20: 400,
    21: 410,
}
_MPA_LABEL = {
    1: 362,
    4: 363,
    5: 363,
    6: 3635,
    7: 364,
    8: 365,
    9: 3655,
    11: 3657,
    12: 366,
    13: 367,
    100: 368,
    101: 369,
}
_MPA_LABEL.update({n: 3695 for n in range(200, 1000)})

_NORIG = [
    "CM  ",
    "MR  ",
    "CM  ",
    "MR  ",
    "CM  ",
    "PC  ",
    "DEG ",
    "M   ",
    "KG  ",
    "GEVA",
    "GEVC",
]
_UORIG = [0.01, 0.001, 0.01, 0.001, 0.01, 0.01, 0.01745329, 1.0, 1.0, 1.0, 1.0]

_SETUP_LABELS = {
    10: _l10,
    50: _l50,
    100: _l100,
    200: _l200,
    490: _l490,
    500: _l500,
    550: _l550,
    600: _l600,
}
for _n in (
    210,
    212,
    220,
    221,
    230,
    240,
    245,
    250,
    260,
    270,
    280,
    290,
    300,
    310,
    320,
    330,
    340,
    350,
    360,
    362,
    363,
    3635,
    364,
    365,
    3655,
    3657,
    366,
    367,
    368,
    369,
    3695,
    370,
    380,
    390,
    400,
    410,
    450,
    452,
    454,
    456,
    460,
    461,
    470,
    480,
):
    _SETUP_LABELS[_n] = globals()["_l%d" % _n]


# --------------------------------------------------------------------------
def turtle(inp, outp):
    """PROGRAM TURTLE (turtle.f:53-79)."""
    lines = open(inp, "rb").read().decode("latin-1").split(chr(10))
    reader = CardReader(lines)
    er = ElementReader(reader)
    out = Out()
    ctx = Context()
    ctx.rng = G900()
    initze(ctx)
    setup(ctx, reader, er, out)
    report.heding(ctx, out)
    zero(ctx)
    left = 10000 - ctx.limno
    out.write(F.render("/'0THE REST SPACE OF HIST STORAGE',I6,' CELLS'", [left]))
    tracking.rayrun(ctx)
    report.ohist(ctx, out)
    report.aplim(ctx, out)
    out.save(outp)
    return ctx, out


# ---CHUNK-F2---
