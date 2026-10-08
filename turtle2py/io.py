"""Card reader: exact port of RDNEXT/RDFIX/RDFLT/RDSTRG/RDPACK/RDSKIP/RDELMT.

The Fortran reader works on 80-character cards (FORMAT(80A1)) and scans
character by character.  This module reproduces that scanner, including
separators, labels, vary codes, the 'S' sentinel, and the element validity
checks of RDELMT (turtle.f:2134-2324).

Watcom INTEGER h-constants (1Hx, 2Hxy, ...) pack the characters into the
low-order bytes, so INTEGER BLANK = 1H' ' is 32, not 0x20202020.
"""

import numpy as np

F32 = np.float32

# /BLOC42/  (BLOCK DATA DATUM, turtle.f:82-115)
TABLE = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")  # TABLE(36)
PLUS = ["+", "?"]
MINUS = "-"
BLANK = " "
PERIOD = "."
SEMI = [";", ",", "*", "&", "!"]
QUOTE = ["'", "#", "/", "=", "&", "^"]
PAR1 = ["(", ":"]
PAR2 = [")", "<"]
SENTINEL = TABLE[28]  # TABLE(29) = 'S'
ARROW = "^"

MASK1 = 255
IBLAN1 = 538976288  # 0x20202020, UBUNCH blank seed

from mpmath import mp as _mp

_mp.prec = 64  # x87 extended: 64-bit significand


def _mpf(v):
    return _mp.mpf(v)


def _f32m(x):
    """Round an extended-precision mpf to float32 and return it as mpf."""
    return _mp.mpf(float(np.float32(float(x))))


def _to_int32(u):
    u &= 0xFFFFFFFF
    return u - 0x100000000 if u >= 0x80000000 else u


def _h(s):
    """Watcom h-constant: characters packed into the low-order bytes."""
    w = 0
    for k, c in enumerate(s):
        w |= (ord(c) & MASK1) << (8 * k)
    return _to_int32(w)


BLANK_WORD = IBLAN1  # INTEGER BLANK: 1H' ' fills all 4 bytes = 0x20202020

# RDELMT tables (turtle.f:2149-2155)
NO1 = [8, 2, 2, 4, 4, 3, 7, 8, 2, 2, 3, 3, 2, 8, 4, 3, 1, 4, 3, 2, 2]
UTABLE = [
    _h("CM"),
    _h("M"),
    _h("IN"),
    _h("FT"),
    _h("MM"),
    _h("R"),
    _h("MR"),
    _h("PC"),
    _h("P/10"),
    _h("N"),
    _h("MEV"),
    _h("GEV"),
    _h("KG"),
    _h("G"),
]
CTABLE = [
    1.0,
    100.0,
    2.54,
    30.48,
    0.1,
    1000.0,
    1.0,
    1.0,
    0.1,
    100.0,
    0.001,
    1.0,
    1.0,
    0.001,
]


def _index(ch, seq):
    """Fortran `DO J=1,n: IF(ITEM .EQ. X(J))` -> 1-based J, else 0."""
    for k, c in enumerate(seq):
        if ch == c:
            return k + 1
    return 0


def unpack(word):
    """A4 edit of an INTEGER word: 4 bytes in memory order (little-endian)."""
    return _to_int32(word).to_bytes(4, "little", signed=True).decode("latin-1")


class StopInput(Exception):
    """RDNEXT(ISKIP=2) STOP when it meets the 'S' sentinel."""


class CardReader:
    """COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM  +  input unit NIN."""

    def __init__(self, lines):
        # FORMAT(80A1): each physical line is one 80-char card.
        self.cards = [l.rstrip("\r\n")[:80].ljust(80) for l in lines]
        self.ncd = 0
        self.mc = 0
        self.empty = True
        self.item = BLANK

    # RDNEXT (ISKIP), turtle.f:2407-2438
    def rdnext(self, iskip):
        if iskip < 0:
            goto = 40
        elif iskip >= 2:
            goto = 20
        elif self.empty:
            goto = 20
        else:
            goto = 10
        while True:
            if goto == 10:
                if self.mc < 80:
                    goto = 30
                elif iskip != 0:
                    goto = 20
                else:
                    self.empty = True
                    self.item = BLANK
                    return
            elif goto == 20:
                self.mc = 0
                self.empty = False
                if self.ncd >= len(self.cards):
                    self.cards.append(" " * 80)  # EOF: FORMAT(80A1) -> blanks
                self.ncd += 1
                goto = 30
            elif goto == 30:
                self.mc += 1
                self.item = self.cards[self.ncd - 1][self.mc - 1]
                if iskip == 0:
                    return
                goto = 40
            else:  # 40
                if self.item == BLANK:
                    goto = 10
                    continue
                if self.item == SENTINEL and iskip == 2:
                    raise StopInput()
                return

    # RDFIX (IVALUE, IFLAG), turtle.f:2326-2354
    def rdfix(self):
        iflag = -1
        ival = 0
        if self.item == MINUS:
            isig = -1
            self.rdnext(0)
        else:
            isig = 1
            if self.item in PLUS:
                self.rdnext(0)
        while True:
            j = _index(self.item, TABLE[:10])
            if j == 0:
                return isig * ival, iflag
            ival = 10 * ival + j - 1
            iflag = 0
            self.rdnext(0)

    # RDFLT (VALUE, IFLAG), turtle.f:2356-2405
    def rdflt(self):
        iflag = -1
        # Watcom x87: VAL/FF are REAL*4 variables (rounded at each
        # assignment) but the arithmetic 10*VAL+d, VAL+FF*d, 0.1*FF is
        # carried in the extended register (64-bit mantissa).  Emulate with
        # mpmath prec=64, rounding to float32 only at each assignment.
        val = _mpf(0)
        jpl = 0
        nex = 0
        if self.item == MINUS:
            sig = -1.0
            self.rdnext(0)
        else:
            sig = 1.0
            if self.item in PLUS:
                self.rdnext(0)
        # The literal 0.1 in `FF = 0.1` and `FF = 0.1 * FF` is a REAL*4
        # constant, i.e. float32(0.1) = 0.100000001490116119384765625, not
        # exact 0.1.  Verified 2026-10-05: only this reproduces the reference
        # PRINT1 values 0.05211 / -0.00004 / -0.00001 (small_ref.res recs 144,
        # 209) while keeping PBEAM 1.8881509304046631 and P0 1.9028400182724.
        tenth = _f32m(_mpf("0.1"))
        ff = tenth
        while True:
            j = _index(self.item, TABLE[:10])
            if j != 0:
                iflag = 0
                if jpl == 0:
                    val = _f32m(_mpf(10) * val + _mpf(j - 1))
                else:
                    val = _f32m(val + ff * _mpf(j - 1))
                    ff = _f32m(tenth * ff)
                self.rdnext(0)
                continue
            if self.item != PERIOD:
                break
            if jpl != 0:
                iflag = 1
                break
            jpl = 1
            ff = _f32m(_mpf("0.1"))
            self.rdnext(0)
        if self.item == TABLE[15]:  # 'F' exponent marker
            self.rdnext(0)
            nex, iflag = self.rdfix()
        elif self.item in PLUS or self.item == MINUS:
            nex, iflag = self.rdfix()
        value = F32(np.copysign(float(val), sig))
        if nex != 0:
            value = _f32m(_mpf(float(value)) * _mpf(10.0**nex))
        return value, iflag

    # RDPACK (CHAR, TEXT, N) + UBUNCH, turtle.f:2440-2454, 3167-3195
    @staticmethod
    def rdpack(chars, nch):
        mwd = IBLAN1
        if nch <= 0:
            return BLANK_WORD
        js = 0
        for _ in range(nch >> 2):
            w = (
                (ord(chars[js]) & MASK1)
                | ((ord(chars[js + 1]) & MASK1) << 8)
                | ((ord(chars[js + 2]) & MASK1) << 16)
                | ((ord(chars[js + 3]) & MASK1) << 24)
            )
            js += 4
            mwd = _to_int32(w)
        ntrail = nch & 3
        if ntrail:
            js = nch
            for _ in range(ntrail):
                mwd = _to_int32(_shl(mwd, 8) | (ord(chars[js - 1]) & MASK1))
                js -= 1
        return mwd

    # RDSTRG (STRING, LMAX, L), turtle.f:2478-2519
    def rdstrg(self, lmax):
        l = 0
        words = [BLANK_WORD] * lmax
        istop = 0
        for j in range(1, 3):
            if self.item == PAR1[j - 1]:
                istop = j
                break
        if istop == 0:
            for j in range(1, 7):
                if self.item == QUOTE[j - 1]:
                    istop = -j
                    break
            if istop == 0:
                return words, 0
            istop = QUOTE[-istop - 1]
        else:
            istop = PAR2[istop - 1]
        iskip = 1
        chars = [" "] * 4
        while True:
            ic = 0
            while True:
                self.rdnext(iskip)
                if self.item == istop:
                    break
                iskip = 0
                if self.item == BLANK or lmax == 1:
                    iskip = 1
                ic += 1
                chars[ic - 1] = self.item
                if ic == 4:
                    break
            if ic != 0:
                l += 1
                if l <= lmax:
                    words[l - 1] = CardReader.rdpack(chars, ic)
            if self.item != istop:
                continue
            break
        self.rdnext(1)
        return words, l

    # RDSKIP (comments), turtle.f:2456-2474.  Returns the printed lines.
    def rdskip(self):
        out = []
        while self.item in PAR1:
            words, l = self.rdstrg(20)
            if l > 20:
                out.append("0NEXT COMMENT TRUNCATED TO 80 CHARS.")
            out.append("0(" + "".join(unpack(w) for w in words) + ")")
        return out


def _shl(w, k):
    return _to_int32((_to_int32(w) & 0xFFFFFFFF) << k)


class Element:
    """DATUM/VARY/NWORD/NVARY/LABLE from one RDELMT call."""

    def __init__(self):
        self.datum = np.zeros(30, np.float32)
        self.vary = np.zeros(30, np.int32)
        self.nword = 0
        self.nvary = 1
        self.lable = BLANK_WORD
        self.length = 0

    @property
    def label(self):
        return unpack(self.lable)

    @property
    def ntype(self):
        return int(abs(self.datum[0]))

    @property
    def typec(self):
        return float(self.datum[0])

    def text(self, j):
        """TEXT(j) = IDATA view of DATUM(j) (1-based)."""
        return self.datum.view(np.int32)[j - 1]


class ElementReader:
    """RDELMT (turtle.f:2134-2324) + /BLOC41/ state.

    rdelmt() returns (nword, flush); messages are appended to self.msg
    (they are written to NOUT by the caller, in order).
    """

    def __init__(self, reader):
        self.r = reader
        self.sntnl = False
        self.flush = False
        self.indic = 0
        self.msg = []
        self.valid = False
        self.e = Element()

    def rdelmt(self):
        from . import report

        e = self.e
        while True:
            # 10: set default values
            e.datum[:] = 0.0
            e.vary[:] = 0
            e.nword = 0
            e.nvary = 1
            e.lable = BLANK_WORD
            # 30
            if self.sntnl:
                self.sntnl = False
                self.valid = False
                return 0, self.flush
            self.flush = False
            self.valid = False
            self.printed = False
            self.msg.extend(self.r.rdskip())
            separ = True
            nword = self._scan(separ, e)
            # 700: PRINT1 on every element that completed the validity check
            if self.printed:
                self.msg.append(report.print1(None, e.lable, e.nword, e.datum, e.vary))
            if self.flush:
                continue
            return nword, self.flush

    def _scan(self, separ, e):
        r = self.r
        while True:
            # 110
            if _index(r.item, SEMI) != 0:
                return self._finish(e)
            if _index(r.item, QUOTE) != 0:
                # 350: label
                words, l = r.rdstrg(1)
                if l > 1:
                    self.msg.append("0NEXT LABEL TRUNCATED TO 4 CHARS.")
                separ = True
                if e.nword == 2 and self.ntype == 15:
                    e.datum.view(np.int32)[2] = words[0]  # TEXT(3)
                    e.nword = 3
                else:
                    if e.lable != BLANK_WORD:
                        self.msg.append(
                            "0LABEL '" + e.label + "' ON NEXT ELEMENT WAS OVERWRITTEN"
                        )
                    e.lable = words[0]
                continue
            if r.item == SENTINEL:
                # 450
                r.empty = True
                if e.nword == 0:
                    return 0
                self.sntnl = True
                return self._check(e)
            if not separ:
                # 130
                self.msg.append(
                    "0SCANNING STOPS DUE TO ERROR AT POSITION "
                    "SHOWN BELOW/" + r.cards[r.ncd - 1] + " " * (81 - r.mc) + ARROW
                )
                return e.nword
            # 150
            if e.nword == 0:
                # 200: type code
                ntype, iflag = r.rdfix()
                if iflag != 0:
                    return self._err130(e)
                e.nword = 1
                e.datum[0] = F32(ntype)
                self.ntype = abs(ntype)
                if r.item != PERIOD:
                    # 100
                    separ = r.item == BLANK
                    r.rdnext(-1)
                    continue
                # 210: vary codes
                separ = self._vary(e)
                continue
            # 300: data value
            value, iflag = r.rdflt()
            if iflag != 0:
                return self._err130(e)
            e.nword += 1
            if e.nword <= 30:
                e.datum[e.nword - 1] = value
            # 100
            separ = r.item == BLANK
            r.rdnext(-1)

    def _vary(self, e):
        r = self.r
        while True:
            r.rdnext(0)
            iflag = 0
            isig = 1
            if r.item == MINUS:
                isig = -1
                r.rdnext(0)
                iflag = 1
            elif r.item in PLUS:
                r.rdnext(0)
                iflag = 1
            j = _index(r.item, TABLE)
            if j == 0:
                if iflag:
                    self._err130(e)
                    return False
                separ = r.item == BLANK
                r.rdnext(-1)
                # GO TO 100 -> handled by caller loop re-entry below
                return separ
            if e.nvary < 30:
                e.nvary += 1
                e.vary[e.nvary - 1] = isig * (j - 1)
            # GO TO 210

    def _err130(self, e):
        r = self.r
        self.msg.append(
            "0SCANNING STOPS DUE TO ERROR AT POSITION SHOWN "
            "BELOW/" + r.cards[r.ncd - 1] + " " * (81 - r.mc) + ARROW
        )
        return e.nword

    def _finish(self, e):
        """500: separator reached."""
        if e.nword == 0:
            return self._err130(e)
        self.r.rdnext(1)
        return self._check(e)

    def _check(self, e):
        """502-700: validity of the element just read.  Every path that gets
        here ends at 700, i.e. PRINT1 is called."""
        self.printed = True
        ntype = self.ntype
        length = 0
        ok = False
        if ntype == 0:
            pass
        elif ntype <= 21:
            length = NO1[ntype - 1]
            if ntype == 16:
                if e.datum[1] == 9:
                    length = 6
                if e.datum[1] == 14:
                    length = 6
                if not (0.0 <= e.datum[1] < 99.5):
                    length = 4
                    if e.datum[1] >= 199.5:
                        length = 2
            d = e.nword - length
            if d == 0:
                ok = True
            elif d > 0:
                # 550
                if ntype != 6:
                    if ntype == 1:
                        length = 9
                    if ntype == 14:
                        length = 30
                    if e.nword - length == 0:
                        ok = True
                    else:
                        self.msg.append("0DATA LIST FOR NEXT ELEMENT IS TOO LONG")
                else:
                    if e.datum[3] != 0.0:
                        length = 5
                    d = e.nword - length
                    if d == 0:
                        ok = True
                    elif d > 0:
                        self.msg.append("0DATA LIST FOR NEXT ELEMENT IS TOO LONG")
                    else:
                        self._incomplete(e, length)
                        e.nword = length
                        return e.nword
                if not ok:
                    e.nword = length
                    return e.nword
            else:
                # 600
                if self.indic != 0:
                    ok = True
                elif ntype != 15:
                    e.nword = length
                    return e.nword
                else:
                    d = e.nword - 2
                    if d == 0:
                        if e.datum[1] != 0.0:
                            self.msg.append("0ERROR ON FOLLOWING 15. ELEMENT")
                            self.flush = True
                            return e.nword
                        e.datum.view(np.int32)[2] = BLANK_WORD
                        e.nword = length
                        return e.nword
                    elif d < 0:
                        e.datum.view(np.int32)[2] = BLANK_WORD
                        e.nword = length
                        return e.nword
                    else:
                        # 630
                        jfound = 0
                        for j in range(1, 15):
                            if e.text(3) == UTABLE[j - 1]:
                                jfound = j
                                break
                        if jfound == 0:
                            self.msg.append("0ERROR ON FOLLOWING 15. ELEMENT")
                            self.flush = True
                            return e.nword
                        e.datum[3] = F32(CTABLE[jfound - 1])
                        if e.datum[1] > 6.0 and jfound < 6:
                            e.datum[3] = F32(0.01) * e.datum[3]
                        e.nword = length
                        return e.nword
        elif ntype < 50:
            pass
        elif ntype <= 53:
            length = 5
            if ntype == 53:
                length = 1
            d = e.nword - length
            if d == 0:
                ok = True
            elif d > 0:
                self.msg.append("0DATA LIST FOR NEXT ELEMENT IS TOO LONG")
                e.nword = length
                return e.nword
            else:
                self._incomplete(e, length)
                e.nword = length
                return e.nword
        elif ntype == 60:
            length = 8
            d = e.nword - length
            if d == 0:
                ok = True
            elif d > 0:
                self.msg.append("0DATA LIST FOR NEXT ELEMENT IS TOO LONG")
                e.nword = length
                return e.nword
            else:
                self._incomplete(e, length)
                e.nword = length
                return e.nword
        else:
            pass
        if not ok:
            # 510
            self.msg.append("0NEXT ELEMENT IS ILLEGAL - RUN FLUSHED")
            self.flush = True
            return e.nword
        e.length = length
        return e.nword

    def _incomplete(self, e, length):
        pass
