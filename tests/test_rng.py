"""pytest: G900 RNG reproduces the Fortran RANF/DRANF test vector (PROGRESS.md §5)."""
import sys, os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from turtle2py.random import G900, M, S0, DX48

# (DR float64, RANF float32, state after) - first 5 calls from seed S0
VECTOR = [
    (0.5801136485795872, 0.5801136493682861, 163287475723473),
    (0.9505127349807658, 0.9505127072334290, 267545549941893),
    (0.7863714253306036, 0.7863714098930359, 221343878630857),
    (0.2976202640037293, 0.2976202666759491, 83772656879069),
    (0.4536999002984920, 0.4536998867988586, 127705168870145),
]


def test_constants():
    assert M == 44485709377909
    assert S0 == 48131768981101
    assert DX48 == 2 ** 48


def test_vector():
    """One RANF call per row: float32 value and state after must match."""
    g = G900()
    for i, (dr, rf, st) in enumerate(VECTOR, 1):
        v = g.ranf()
        assert v == np.float32(rf), f'call {i}: RANF {v} != {rf}'
        assert g.g900gt() == st, f'call {i}: state'


def test_dranf_vector():
    """DRANF stream (float64 DR) from seed S0.

    The §5 table prints DR to 16 digits; the exact value is state/2**48.
    """
    g = G900()
    for i, (dr, _rf, st) in enumerate(VECTOR, 1):
        v = g.dranf()
        assert v == st / DX48, f'call {i}: DRANF != state/2**48'
        assert abs(v - dr) < 1e-15, f'call {i}: DRANF {v} vs table {dr}'


def test_seed_roundtrip():
    g = G900()
    for _ in range(3):
        g.ranf()
    st = g.g900gt()
    h = G900()
    h.g900st(st)
    assert h.g900gt() == st
    assert h.ranf() == g.ranf()
