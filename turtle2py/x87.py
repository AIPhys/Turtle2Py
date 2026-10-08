"""x87 extended-precision emulation for the Watcom F77 port.

Watcom F77 on i386 keeps REAL*4 values in 80-bit x87 registers: a REAL*4
variable is stored rounded to float32, but every arithmetic operation and
every transcendental call is performed on the 64-bit-mantissa extended value,
and rounding to float32 happens only when the result is stored into a
Fortran REAL variable.

Semantics reproduced here:
  * M(x)  - load a REAL*4 value (a Python float that is exactly a float32)
            into the extended register: exact, no rounding.
  * arithmetic (+ - * /) and transcendental calls (sin cos tan exp atan asin
            sqrt log) are computed at 64-bit mantissa precision.
  * C(m)  - store to a REAL*4 variable: round once to float32.

Verified (2026-10-03) against the Fortran QD dump (probe13.res, 504 lines):
FOCUS RH/RV chains match bit-for-bit with this emulation; the numpy-double
path diverges by 1-2 ULP in RH(2), RH(3), RV(2), RV(3).

mpmath with mp.mp.prec = 64 gives correctly-rounded results at 64-bit
mantissa, which is the same rounding model as the x87 for basic arithmetic;
for transcendentals it is correctly-rounded to 64 bits, which agrees with
Watcom's extended-precision library after the float32 store (40 guard bits).
"""

import mpmath as mp
import numpy as np

mp.mp.prec = 64


def M(x):
    """Load a REAL*4 value into the extended register (exact)."""
    return mp.mpf(float(x))


def C(m):
    """Store an extended value to a REAL*4 variable (single rounding)."""
    return float(np.float32(m))


E = M
S = C


def F(x):
    """Load a REAL*4 value as an extended mpf (alias of M, for readability)."""
    return mp.mpf(float(x))


# --- transcendental functions, evaluated at extended precision ---
#
# Watcom F77 calls the math library (SIN/COS/TAN/EXP/ALOG/ATAN/ASIN) with a
# REAL*4 argument passed by value: the argument is rounded to float32 before
# the call, and the library computes in x87 extended (64-bit mantissa).
# SQRT compiles to the x87 FSQRT instruction: the extended operand is used
# directly, no float32 rounding of the argument.


def round32(m):
    """Round an extended value to REAL*4 directly (24-bit mantissa,
    round-half-even), avoiding float64 double-rounding."""
    m = m.m if isinstance(m, V) else (m if isinstance(m, mp.mpf) else mp.mpf(float(m)))
    if not mp.isfinite(m):
        return float(m)
    with mp.workprec(24):
        r = mp.mpf(m)
    return float(np.float32(r))


def _arg(x):
    """Argument of a transcendental library call.

    Watcom F77 passes REAL arguments to the math library as 80-bit extended
    values, so an expression argument (e.g. SIN(THETA1+ALFA)) reaches the
    library UNROUNDED.  Verified 2026-10-03 against the probe15 SD dump at
    I=272: SIN(THETA1+ALFA) with the extended argument reproduces SINT2
    bit-for-bit (ulp 0), while rounding the argument to REAL*4 is off by
    6 ULP.  A variable argument is already exactly a float32, so this is a
    no-op there.
    """
    return x.m if isinstance(x, V) else mp.mpf(float(x))


def _is_f32(x):
    """True when a transcendental argument is a plain REAL*4 value.

    Watcom links the REAL*4 math library (result rounded to REAL*4) when the
    argument is a REAL*4 variable, and the extended library (result kept in
    the x87 register, unrounded) when the argument is an in-register extended
    expression.  Verified 2026-10-05: probe35s.res SIN(XR4) is float32-rounded
    (0/101), while probe40s.res SINT2 = SIN(THETA1+ALFA) - SIN(ALFA)*(...)
    reproduces bit-for-bit only with the EXTENDED SIN(THETA1+ALFA) result
    (extended/extended -> match; any library-rounded variant -> 1 ULP off).
    """
    m = x.m if isinstance(x, V) else mp.mpf(float(x))
    return mp.mpf(float(np.float32(m))) == m


def _lib(m, rounded=False):
    """Return value of a math-library call.

    Watcom's SIN/COS/TAN/EXP/ATAN/ASIN return the x87 EXTENDED result in a
    register: no float32 rounding at the return.  Verified 2026-10-05 against
    probe40s.res (BEND sector, SINT2 = SIN(THETA1+ALFA) - SIN(ALFA)*(RAY(1)+
    RHO0)/RHO, dumped as REAL*8): only the model with BOTH SIN results kept
    extended reproduces SINT2 bit-for-bit; rounding either result to REAL*4
    is 1 ULP off.  The apparent float32 rounding in probe35s.res is the
    DBLE(SIN(XR4)) conversion in the WRITE statement, not the library return.
    """
    return round32(m) if rounded else m


def sin_ext(x):
    """SIN with the result kept EXTENDED (no REAL*4 return rounding).

    Use when the call sits in a compound expression that also contains an
    extended-argument transcendental: Watcom evaluates the whole expression
    through the extended library, so every transcendental result in it stays
    in the x87 register.  Verified 2026-10-05 vs probe40s.res (BEND sector
    SINT2): both SIN results extended reproduce it bit-for-bit; rounding
    SIN(ALFA) to REAL*4 is 1 ULP off.
    """
    return _lib(mp.sin(_arg(x)), False)


def sin(x):
    """SIN(): the extended-precision library routine, argument UNROUNDED,
    result rounded to REAL*4 at return."""
    return _lib(mp.sin(_arg(x)), _is_f32(x))


def cos(x):
    return _lib(mp.cos(_arg(x)), _is_f32(x))


def cos32(x):
    """COS() with the argument spilled to REAL*4 first.

    Verified 2026-10-05 against probe16.res (all 288 sector bends, SD/R2
    pairs): COS(THETA1+ALFA) inside the RAY2(1) expression of BEND label 300
    reproduces the reference bit-for-bit (0/288) only when the argument is
    rounded to REAL*4; the extended argument is off (263/288).  The
    SIN(THETA1+ALFA) in the SINT2 statement takes the UNROUNDED extended
    argument (0/288), so the spill happens for the complex RAY2(1)
    expression only.
    """
    return _lib(mp.cos(mp.mpf(S(x))))


def tan(x):
    return _lib(mp.tan(_arg(x)), _is_f32(x))


def exp(x):
    return _lib(mp.exp(_arg(x)), _is_f32(x))


def atan(x):
    return _lib(mp.atan(_arg(x)), _is_f32(x))


def asin(x):
    return _lib(mp.asin(_arg(x)), _is_f32(x))


def atan2(y, x):
    """ATAN2(Y, X): the library takes REAL*4 arguments."""
    return _lib(mp.atan2(_arg(y), _arg(x)), _is_f32(y) and _is_f32(x))


def sqrt(x):
    m = x.m if isinstance(x, V) else mp.mpf(float(x))
    return mp.sqrt(m)


def log(x):
    """ALOG guarded like the port: x <= 0 -> -inf (caller resamples)."""
    x = float(x)
    if x <= 0.0:
        return mp.mpf("-inf")
    return mp.log(_arg(x))


def abs_(x):
    return abs(mp.mpf(float(x)))


class V:
    """An x87 extended register holding a value.

    Plain Python floats (REAL*4 variables) load exactly; arithmetic is done
    at 64-bit mantissa.  S(v) stores to REAL*4 (single float32 rounding).
    Transcendental helpers T.* take the float32-rounded argument.
    """

    __slots__ = ("m",)

    def __init__(self, v):
        self.m = v.m if isinstance(v, V) else mp.mpf(float(v))

    def __add__(s, o):
        return _n(s.m + (o.m if isinstance(o, V) else mp.mpf(float(o))))

    __radd__ = __add__

    def __sub__(s, o):
        return _n(s.m - (o.m if isinstance(o, V) else mp.mpf(float(o))))

    def __rsub__(s, o):
        return _n((o.m if isinstance(o, V) else mp.mpf(float(o))) - s.m)

    def __mul__(s, o):
        return _n(s.m * (o.m if isinstance(o, V) else mp.mpf(float(o))))

    __rmul__ = __mul__

    def __truediv__(s, o):
        return _n(_div(s.m, o.m if isinstance(o, V) else mp.mpf(float(o))))

    def __rtruediv__(s, o):
        return _n(_div(o.m if isinstance(o, V) else mp.mpf(float(o)), s.m))

    def __pow__(s, o):
        return _n(s.m ** (o.m if isinstance(o, V) else mp.mpf(float(o))))

    def __neg__(s):
        return _n(-s.m)

    def __abs__(s):
        return _n(abs(s.m))

    def __float__(s):
        return float(s.m)

    def __lt__(s, o):
        return s.m < (o.m if isinstance(o, V) else mp.mpf(float(o)))

    def __le__(s, o):
        return s.m <= (o.m if isinstance(o, V) else mp.mpf(float(o)))

    def __gt__(s, o):
        return s.m > (o.m if isinstance(o, V) else mp.mpf(float(o)))

    def __ge__(s, o):
        return s.m >= (o.m if isinstance(o, V) else mp.mpf(float(o)))


def _div(a, b):
    """IEEE x87 division: x/0 -> +-inf, 0/0 -> nan (mpmath raises ZeroDivisionError).

    Watcom's x87 never traps: a zero RMS half width in a summary block
    (e.g. te455_0.dat, where all rays land in one x' bin) makes the
    correlation 0/0 = nan, printed as '-nan'.
    """
    if b == 0:
        if a == 0:
            return mp.nan
        return mp.inf if a > 0 else -mp.inf
    return a / b


def _n(m):
    v = V.__new__(V)
    v.m = m
    return v


def S(v):
    """Store an extended value to a REAL*4 variable (single rounding)."""
    return float(np.float32(v.m if isinstance(v, V) else v))


def R(v):
    """Load a REAL*4 variable (Python float) into an extended register."""
    return V(v)


def P(v, n):
    """Integer power as Watcom compiles it: unrolled left-associated
    multiplication in the extended register (no pow/exp/log)."""
    m = v.m if isinstance(v, V) else mp.mpf(float(v))
    r = m
    for _ in range(n - 1):
        r = r * m
    return _n(r)


def K(x):
    """A REAL*4 literal constant as an extended register (float32-rounded)."""
    return V(float(np.float32(x)))
