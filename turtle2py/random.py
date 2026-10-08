"""G900 multiplicative congruential RNG - exact port of RANF/DRANF in turtle.f.

The Fortran routine (turtle.f:3130-3165) keeps a 48-bit state split into two
DOUBLE PRECISION halves DS(1) (low 24 bits) and DS(2) (high 24 bits) and
multiplies by a 48-bit multiplier using split arithmetic:

    DS = (DS * DM) mod 2**48,   DR = DS / 2**48
    RANF  = SNGL(DR)   (float32)
    DRANF = DR         (float64)

Constants decoded from the DATA statements:
    DS(1)=16651885, DS(2)=2868876   -> seed  S0 = 48131768981101
    DM(1)=15184245, DM(2)=2651554   -> mult  M  = 44485709377909
    DX24 = 2**24, DX48 = 2**48

The split arithmetic is exactly integer modular arithmetic (verified: the
carry chain DL/DC/DU reproduces (S*M) mod 2**48 with Python big ints), so
this class reproduces the Fortran stream bit-for-bit.  The argument of
RANF(X) is never used by the Fortran code; it is ignored here as well.
"""
import numpy as np

DX24 = 2 ** 24
DX48 = 2 ** 48
M = 2651554 * DX24 + 15184245          # 44485709377909
S0 = 2868876 * DX24 + 16651885         # 48131768981101  (initial DS state)


class G900:
    def __init__(self, seed: int = S0):
        self.s = seed % DX48

    def _advance(self) -> float:
        self.s = (self.s * M) % DX48
        return self.s / DX48

    def ranf(self, x=None) -> np.float32:
        """REAL FUNCTION RANF(X): SNGL(DR) - float32 in [0,1)."""
        return np.float32(self._advance())

    def dranf(self) -> float:
        """ENTRY DRANF(): full double value DR."""
        return self._advance()

    def g900gt(self) -> int:
        """ENTRY G900GT(): current 48-bit state."""
        return self.s

    def g900st(self, dseed: int) -> int:
        """ENTRY G900ST(DSEED): set the state."""
        self.s = int(dseed) % DX48
        return self.s % DX24
