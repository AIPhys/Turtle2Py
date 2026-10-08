import numpy as np
import pytest
from turtle2py.state import Context
from turtle2py import elements as e


def mk(h=1.888151, ll=10.0):
    ctx = Context()
    ctx.p = np.float32(h)
    ctx.p0 = np.float32(h)
    ctx.ll = np.float32(ll)
    ctx.i = 2
    return ctx


def test_nu():
    ctx = mk()
    assert e.nu(ctx, 3) == 2
    assert e.nu(ctx, 16) == 5
    assert e.nu(ctx, 51) == 1
    assert e.nu(ctx, 53) == 2
    ctx.sec = True
    assert e.nu(ctx, 4) == 41
    ctx.sec = False
    ctx.idata[ctx.i + 8] = 0
    assert e.nu(ctx, 14) == 30


def test_sector_identity():
    # type-4 style sector with H=0 -> labels 300, alfa=0, RHO0!=0: identity
    ctx = mk()
    ctx.data[4] = 0.0   # H
    ctx.data[5] = 0.0   # N
    ctx.data[6] = 1.0   # RHO0
    ctx.data[7] = 0.0   # BDB
    ctx.ray[1:5] = [0.001, 0.002, -0.003, 0.004]
    before = ctx.ray[1:5].copy()
    ks = e.bend(ctx)
    assert ks == 0
    # COST2 = SQRT(1-SINT2**2) differs from COS(THETA1) by float32 rounding
    assert np.allclose(ctx.ray[1:5], before, rtol=1e-4, atol=1e-9)


def test_bend_normal_focus():
    # normal magnet H=0.5, N=0.5, BDB=0: kh2=0.125, kv2=0.125
    ctx = mk(ll=1.0)
    ctx.data[4] = 0.5
    ctx.data[5] = 0.5
    ctx.data[6] = 0.0
    ctx.data[7] = 0.0
    ctx.ray[1:5] = [0.001, 0.0, 0.0, 0.0]
    ks = e.bend(ctx)
    assert ks == 0
    # horizontal: x' = -k*sin(kl)*x with k=sqrt(0.125)
    k = np.sqrt(0.125)
    assert float(ctx.ray[2]) == pytest.approx(-k * np.sin(k) * 0.001, rel=1e-5)
    assert float(ctx.ray[4]) == pytest.approx(-k * np.sin(k) * 0.0, rel=1e-5, abs=1e-12)


def test_quad_drift_and_focus():
    ctx = mk(ll=10.0)
    ctx.data[4] = 0.0
    ctx.ray[1:5] = [0.001, 0.002, -0.003, 0.004]
    e.quad(ctx)
    assert np.allclose(ctx.ray[1:5], [0.001 + 10 * 0.002, 0.002,
                                       -0.003 + 10 * 0.004, 0.004],
                       rtol=1e-5, atol=1e-9)
    # focusing in x for positive DATA(I+2)
    ctx2 = mk(ll=1.0)
    ctx2.data[4] = np.float32(1.888151 * 0.1)  # kh2 = 0.1
    ctx2.ray[1:5] = [0.01, 0.0, 0.0, 0.0]
    e.quad(ctx2)
    k = np.sqrt(0.1)
    assert float(ctx2.ray[2]) == pytest.approx(-k * np.sin(k) * 0.01, rel=1e-5)
    assert float(ctx2.ray[2]) < 0.0


def test_solo_zero_drift():
    # SOLO with zero field: C=1, S=0, SOK=LL -> drift in both planes
    ctx = mk(ll=10.0)
    ctx.data[4] = 0.0
    ctx.ray[1:5] = [0.001, 0.002, -0.003, 0.004]
    e.solo(ctx)
    assert np.allclose(ctx.ray[1:5], [0.001 + 10 * 0.002, 0.002,
                                       -0.003 + 10 * 0.004, 0.004],
                       rtol=1e-5, atol=1e-9)


def test_solo_invariant():
    # canonical angular momentum x*py - y*px conserved by solenoid
    ctx = mk(ll=5.0)
    ctx.data[4] = np.float32(1.888151 * 0.3)
    ctx.ray[1:5] = [0.002, 0.0013, -0.0017, 0.0021]
    l0 = float(ctx.ray[1]) * float(ctx.ray[4]) - float(ctx.ray[3]) * float(ctx.ray[2])
    e.solo(ctx)
    l1 = float(ctx.ray[1]) * float(ctx.ray[4]) - float(ctx.ray[3]) * float(ctx.ray[2])
    assert l1 == pytest.approx(l0, rel=1e-5)


def test_sext_zero_drift():
    ctx = mk(ll=10.0)
    ctx.sec = True
    ctx.data[4] = 0.0
    ctx.ray[1:5] = [0.001, 0.002, -0.003, 0.004]
    e.sext(ctx)
    assert np.allclose(ctx.ray[1:5], [0.001 + 10 * 0.002, 0.002,
                                       -0.003 + 10 * 0.004, 0.004],
                       rtol=1e-5, atol=1e-9)


def test_multi_noop():
    ctx = mk()
    ctx.mmax = 0
    ctx.ray[1:5] = [0.001, 0.002, -0.003, 0.004]
    before = ctx.ray[1:5].copy()
    e.multi(ctx)
    assert np.array_equal(ctx.ray[1:5], before)


def test_hstval_hstun():
    ctx = mk()
    ctx.ray[1:5] = [0.001, 0.002, -0.003, 0.004]
    ctx.z = np.float32(12.5)
    ctx.p = np.float32(1.888151)
    assert float(e.hstval(ctx, 1)) == pytest.approx(0.001, rel=1e-6)
    assert float(e.hstval(ctx, 8)) == pytest.approx(12.5, rel=1e-6)
    assert float(e.hstval(ctx, 11)) == pytest.approx(1.888151, rel=1e-6)
    f, legal = e.hstun(ctx, 1)
    assert legal and float(f) == pytest.approx(0.01, rel=1e-6)
    f, legal = e.hstun(ctx, 5)
    assert not legal
    f, legal = e.hstun(ctx, 21)
    assert legal and float(f) == pytest.approx(0.01, rel=1e-6)


def test_repeat_stack():
    ctx = mk()
    ctx.ip = 0
    ctx.idata[3] = 3   # IDATA(I+1): repeat 3 times
    ctx.i = 2
    e.repeat(ctx)
    assert ctx.ip == 1 and ctx.ic[1] == 3 and ctx.is_[1] == 2
    ctx.idata[3] = 0
    e.repeat(ctx)
    assert ctx.ic[1] == 2 and ctx.i == 2
    e.repeat(ctx)
    e.repeat(ctx)
    assert ctx.ic[1] == 0 and ctx.ip == 0
