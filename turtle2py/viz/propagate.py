"""Fast vectorised beam propagation for visualisation (float64, numpy).

NOT the bit-exact port: plain float64 arithmetic and the same linear FOCUS
matrices as the reference (turtle.f:1909), so 1e5-1e6 rays run in seconds.
It reads the DATA/IDATA arrays that SETUP produced, so lengths, strengths and
apertures are the deck's numbers.  Decay, MULTI and second-order bend terms
are omitted; aperture tests follow BSTOP / QSTOP / SLIT exactly.

Units: x,y in cm; x',y' in mr (dimensionless slope); dp/p in PC; z in cm.
"""

from __future__ import annotations

import math

import numpy as np

from .. import elements as el

PI = 3.141592653589793
Z_TEMP = 11.037  # Maximov source correlation length, m (turtle.f:318)
YY_MAX = 0.001 * 13.8745  # cm
Y1_MAX = 0.001 * 2.1622  # mr


def emit(nrays: int, raymax, pbeam: float, seed: int = 12345) -> np.ndarray:
    """Vectorised EMIT_MY (turtle.f:251-371): (nrays,6) [x,xp,y,yp,dp,p].

    Horizontal: 50-bin (1-(x/xa)^0.25)^3 distribution + Rayleigh x'.
    Vertical: Maximov source with the reference's triple rejection, plus a
    Rayleigh y' kick.  dp uniform, p = Pbeam*(1+dp).
    """
    rng = np.random.default_rng(seed)
    xa, xp0, ya, yp0 = raymax[0], raymax[1], raymax[2], raymax[3]
    dpm = raymax[5]

    def rayleigh(k):
        return np.sqrt(-2.0 * np.log(rng.random(k)))

    # --- horizontal position: 50-bin table, as in EMIT_MY label 10/20/30/31
    dx = xa / 50.0
    xs = dx * (np.arange(1, 51) - 0.5)
    w = (1.0 - (xs / xa) ** 0.25) ** 3
    cdf = np.cumsum(w) / w.sum()
    ib = np.searchsorted(cdf, rng.random(nrays))
    x = dx * (ib + 1 - rng.random(nrays))
    xp = xp0 * rayleigh(nrays) * np.sin(PI * rng.random(nrays))

    # --- vertical Maximov source with rejection (label 40)
    sig_yy, sig_y1 = YY_MAX / 3.0, Y1_MAX / 3.0
    y = np.empty(nrays)
    ypp = np.empty(nrays)
    done = 0
    while done < nrays:
        m = nrays - done
        xr3, xr4 = rayleigh(m), PI * rng.random(m)
        dyy = sig_yy * xr3 * np.cos(xr4)
        dy1 = sig_y1 * xr3 * np.sin(xr4)
        yv = dyy + dy1 * Z_TEMP
        ok = (np.abs(dyy) <= YY_MAX) & (np.abs(dy1) <= Y1_MAX) & (np.abs(yv) <= ya)
        k = int(ok.sum())
        y[done : done + k] = yv[ok]
        ypp[done : done + k] = dy1[ok]
        done += k

    ypp = ypp + yp0 * rayleigh(nrays) * np.sin(PI * rng.random(nrays))
    dp = dpm * (2.0 * rng.random(nrays) - 1.0) if dpm else np.zeros(nrays)
    p = pbeam * (1.0 + dp)
    return np.column_stack([x, xp, y, ypp, dp, p])


def focus_v(k2, L):
    """Vectorised FOCUS(K2,L) (turtle.f:1909-1934) -> (R1,R2,R3,R4)."""
    k2 = np.asarray(k2, dtype=np.float64)
    k = np.sqrt(np.abs(k2))
    kl = k * L
    pos, neg = k2 > 0.0, k2 < 0.0
    r1 = np.ones_like(k2)
    r2 = np.full_like(k2, L)
    r3 = np.zeros_like(k2)
    r4 = np.ones_like(k2)
    if pos.any():
        c, s = np.cos(kl[pos]), np.sin(kl[pos])
        small = np.abs(kl[pos]) < 0.01
        r3[pos] = -k[pos] * s
        r1[pos] = c
        r2[pos] = np.where(small, L * (1.0 - k2[pos] * L * L / 6.0), -r3[pos] / k2[pos])
        r4[pos] = c
    if neg.any():
        e = np.exp(kl[neg])
        ei = 1.0 / e
        r3n = 0.5 * (e - ei) * k[neg]
        small = np.abs(kl[neg]) < 0.01
        r1[neg] = 0.5 * (e + ei)
        r2[neg] = np.where(small, L * (1.0 - k2[neg] * L * L / 6.0), -r3n / k2[neg])
        r3[neg] = r3n
        r4[neg] = 0.5 * (e + ei)
    return r1, r2, r3, r4


def _sector(x, xp, y, yp, p, p0, L, h, n, rho0, sec):
    """BEND (turtle.f:1846-1862, N==0 and BDB==0): exact sector geometry."""
    alfa = L * h
    rho = rho0 * p / p0
    th1 = np.arctan(xp)
    cost1 = np.cos(th1)
    sint2 = np.sin(alfa + th1) - np.sin(alfa) * (x + rho0) / rho
    lost = np.abs(sint2) >= 1.0
    sint2 = np.clip(sint2, -0.999999, 0.999999)
    cost2 = np.sqrt(1.0 - sint2 * sint2)
    cosal = math.cos(alfa)
    x2 = x * cosal + rho * (cost2 - np.cos(alfa + th1)) - rho0 * (1.0 - cosal)
    xp2 = sint2 / cost2
    y2 = y + yp * rho * cost1 * (alfa + th1 - np.arcsin(sint2))
    yp2 = yp * cost1 / cost2
    return x2, xp2, y2, yp2, lost


def _bend_lin(x, xp, y, yp, p, L, h, n, sec):
    """BEND (turtle.f:1713-1845) linear part: FOCUS on KH2/KV2 + momentum term."""
    kh2 = np.full(x.shape, h * h * (1.0 - n), dtype=np.float64)
    kv2 = np.full(x.shape, h * h * n, dtype=np.float64)
    a1, a2, a3, a4 = focus_v(kh2, L)
    b1, b2, b3, b4 = focus_v(kv2, L)
    dh = h * (p - p.mean()) / p  # DH = H*(P-P0)/P, P0 ~ p0
    x2 = a1 * x + a2 * xp + (dh * dh) * 0.0
    xp2 = a3 * x + a4 * xp
    y2 = b1 * y + b2 * yp
    yp2 = b3 * y + b4 * yp
    return x2, xp2, y2, yp2


def _scatt(rng, x, xp, y, yp, theta0, dz_cm):
    """SCATT_MY label 30 (turtle.f:1084-1105): angles + coordinates."""
    n = x.shape[0]
    s1 = theta0
    sr = theta0 * dz_cm / math.sqrt(12.0)

    def pair(sig):
        s = np.sqrt(-2.0 * np.log(rng.random(n)))
        ph = 2.0 * math.pi * rng.random(n)
        return s * np.cos(ph) * sig, s * np.sin(ph) * sig

    dx1, dy1 = pair(s1)
    dxr, dyr = pair(sr)
    x = x + dxr + dx1 * dz_cm * 0.5
    y = y + dyr + dy1 * dz_cm * 0.5
    xp = xp + dx1
    yp = yp + dy1
    return x, xp, y, yp


def apertures(ctx):
    """Aperture limits per element from SETUP/BSTOP/QSTOP/SLIT (cm, mr)."""
    d = np.asarray(ctx.data, dtype=np.float64)
    idata = np.asarray(ctx.idata, dtype=np.int32)
    from .. import elements as el

    out = []
    i = 1
    while i <= ctx.i1:
        t = int(idata[i])
        lo_x = lo_y = None
        if t == 4 and ctx.cap[1]:
            if ctx.apb[1] != 0.0:
                lo_x = float(ctx.apb[1])
            if ctx.apb[2] != 0.0:
                lo_y = float(ctx.apb[2])
        elif t == 5 and ctx.cap[1]:
            if ctx.ellips:
                lo_x, lo_y = float(ctx.qap[1]), float(ctx.qap[2])
            elif ctx.hyper:
                lo_x = lo_y = math.sqrt(abs(float(ctx.qap[3])))
            else:
                r = math.sqrt(abs(float(d[i + 3])))
                lo_x = lo_y = r
        elif t == 6:
            ifp = int(idata[i + 1]) // 100
            iff = int(idata[i + 1]) - 100 * ifp
            ifg = int(idata[i + 3])
            a, b = float(d[i + 2]), float(d[i + 4])
            if ifg == 0:
                lo_x = abs(a) if iff == 1 else None
                lo_y = abs(a) if iff == 3 else None
            else:
                lo_x = abs(a) if iff == 1 else None
                lo_y = abs(a) if iff == 3 else None
        out.append((i, t, lo_x, lo_y))
        i += el.nu(ctx, t)
    return out


def trace(ctx, rays, seed=12345, record=True, stride=1):
    """Vectorised RAYRUN over the SETUP-processed deck.

    Returns dict with per-element envelope stats (z in cm, x/y in cm,
    x'/y' in mr) and, when record, per-ray trajectories (x,y,z) sampled
    every `stride` elements for the 3-D view.
    """
    from .. import elements as el

    rng = np.random.default_rng(seed)
    d = np.asarray(ctx.data, dtype=np.float64)
    idata = np.asarray(ctx.idata, dtype=np.int32)
    x = rays[:, 0].astype(np.float64).copy()
    xp = rays[:, 1].astype(np.float64).copy()
    y = rays[:, 2].astype(np.float64).copy()
    yp = rays[:, 3].astype(np.float64).copy()
    p = rays[:, 5].astype(np.float64).copy()
    p0 = float(ctx.p0)
    n = x.shape[0]
    alive = np.ones(n, dtype=bool)
    z = 0.0
    env = {
        "z": [0.0],
        "type": ["source"],
        "name": [""],
        "alive": [n],
        "x_rms": [float(np.std(x))],
        "y_rms": [float(np.std(y))],
        "x_max": [float(np.max(np.abs(x)))],
        "y_max": [float(np.max(np.abs(y)))],
        "xp_rms": [float(np.std(xp))],
        "yp_rms": [float(np.std(yp))],
        "loss": [0],
    }
    traj = [np.zeros((n, 3))] if record else None
    phase_hist: list[np.ndarray] = []  # per-sample (x, xp, y, yp) for all rays
    alive_hist: list[np.ndarray] = []  # per-sample alive mask
    i = 1
    while i <= ctx.i1:
        t = int(idata[i])
        killed = 0
        if t >= 50:
            i += el.nu(ctx, t)
            continue
        if t == 16:
            if int(idata[i + 1]) == 11:
                p0 = float(d[i + 2])
            i += el.nu(ctx, 16)
            continue
        if t == 13:
            i += el.nu(ctx, 13)
            continue
        if t == 1:
            if int(idata[i + 8]) == 0:
                th = float(d[i + 2])
                if th > 0:
                    xp = xp + th * np.sqrt(-2.0 * np.log(rng.random(n))) * np.sin(
                        2 * math.pi * rng.random(n)
                    )
                    yp = yp + th * np.sqrt(-2.0 * np.log(rng.random(n))) * np.sin(
                        2 * math.pi * rng.random(n)
                    )
                p = p + float(d[i + 7])
            i += el.nu(ctx, 1)
            continue
        if t == 3:
            L = float(d[i + 1])
            x = x + L * xp
            y = y + L * yp
            z += L
            i += el.nu(ctx, 3)
        elif t == 5:
            L = float(d[i + 1])
            kh2 = np.float64(d[i + 2]) / p
            a1, a2, a3, a4 = focus_v(kh2, L)
            b1, b2, b3, b4 = focus_v(-kh2, L)
            x, xp = a1 * x + a2 * xp, a3 * x + a4 * xp
            y, yp = b1 * y + b2 * yp, b3 * y + b4 * yp
            z += L
            if ctx.cap[1]:
                if ctx.ellips:
                    bad = (x / ctx.qap[1]) ** 2 + (y / ctx.qap[2]) ** 2 > 1.0
                elif ctx.hyper:
                    bad = np.abs(x * y) > abs(ctx.qap[3])
                else:
                    bad = x * x + y * y > abs(d[i + 3])
                killed = int((bad & alive).sum())
                alive &= ~bad
            i += el.nu(ctx, 5)
        elif t == 4:
            L = float(d[i + 1])
            h = np.float64(d[i + 2])
            nn = float(d[i + 3])
            rho0 = float(d[i + 4])
            if nn == 0.0 and float(d[i + 5]) == 0.0:
                x, xp, y, yp, lost = _sector(
                    x, xp, y, yp, p, p0, L, h, nn, rho0, ctx.sec
                )
                killed += int((lost & alive).sum())
                alive &= ~lost
            else:
                kh2 = np.full(n, h * h * (1.0 - nn))
                kv2 = np.full(n, h * h * nn)
                a1, a2, a3, a4 = focus_v(kh2, L)
                b1, b2, b3, b4 = focus_v(kv2, L)
                x, xp = a1 * x + a2 * xp, a3 * x + a4 * xp
                y, yp = b1 * y + b2 * yp, b3 * y + b4 * yp
            if ctx.cap[1] and ctx.apb[1] != 0.0:
                bad = np.abs(x) > ctx.apb[1]
                killed += int((bad & alive).sum())
                alive &= ~bad
            if ctx.cap[1] and ctx.apb[2] != 0.0:
                bad = np.abs(y) > ctx.apb[2]
                killed += int((bad & alive).sum())
                alive &= ~bad
            z += L
            i += el.nu(ctx, 4)
        elif t == 2:
            h = np.float64(d[i + 1]) / p
            tanb = float(d[i + 2])
            tancor = tanb - h * float(d[i + 5])
            xp = xp + h * x * tanb
            yp = yp - h * y * tancor
            i += el.nu(ctx, 2)
        elif t == 6:
            ifp = int(idata[i + 1]) // 100
            iff = int(idata[i + 1]) - 100 * ifp
            ifg = int(idata[i + 3])
            a, b = float(d[i + 2]), float(d[i + 4])
            if ifp == 0:
                v = (x, xp, y, yp)[iff - 1]
                if ifg == 0:
                    bad = np.abs(v) >= abs(a) if a >= 0 else np.abs(v) > abs(a)
                else:
                    w = (x, xp, y, yp)[ifg - 1]
                    rad2 = (v / a) ** 2 + (w / b) ** 2
                    bad = rad2 >= 1.0 if a >= 0 else rad2 > 1.0
                killed = int((bad & alive).sum())
                alive &= ~bad
            i += el.nu(ctx, 6)
        elif t == 7:
            x = x + float(d[i + 1])
            xp = xp + float(d[i + 2])
            y = y + float(d[i + 3])
            yp = yp + float(d[i + 4])
            p = p + float(d[i + 6]) * p0
            i += el.nu(ctx, 7)
        elif t == 21:
            th = float(d[i + 1])
            xp = xp + th * np.sqrt(-2.0 * np.log(rng.random(n))) * np.sin(
                2 * math.pi * rng.random(n)
            )
            yp = yp + th * np.sqrt(-2.0 * np.log(rng.random(n))) * np.sin(
                2 * math.pi * rng.random(n)
            )
            i += el.nu(ctx, 21)
        else:
            i += el.nu(ctx, t)
        av = alive
        env["z"].append(z)
        env["type"].append(str(t))
        env["name"].append("")
        env["alive"].append(int(av.sum()))
        if av.any():
            env["x_rms"].append(float(np.std(x[av])))
            env["y_rms"].append(float(np.std(y[av])))
            env["x_max"].append(float(np.max(np.abs(x[av]))))
            env["y_max"].append(float(np.max(np.abs(y[av]))))
            env["xp_rms"].append(float(np.std(xp[av])))
            env["yp_rms"].append(float(np.std(yp[av])))
        else:
            for k in ("x_rms", "y_rms", "x_max", "y_max", "xp_rms", "yp_rms"):
                env[k].append(0.0)
        env["loss"].append(killed)
        if record:
            traj.append(np.column_stack([x, y, np.full(n, z)]))
            phase_hist.append(np.column_stack([x, xp, y, yp]))
            alive_hist.append(av.copy())
    env["traj"] = traj
    env["phase_hist"] = phase_hist
    env["alive_hist"] = alive_hist
    all_out = np.column_stack([x, xp, y, yp, rays[:, 4], p])
    env["rays_out"] = all_out[alive]
    env["rays"] = all_out
    env["alive_mask"] = alive
    env["zmax"] = z
    # viewer-facing aliases
    env["xrms"], env["xmax"] = env["x_rms"], env["x_max"]
    env["yrms"], env["ymax"] = env["y_rms"], env["y_max"]
    env["xprms"], env["yprms"] = env["xp_rms"], env["yp_rms"]
    env["loss_total"] = int(n - alive.sum())
    return env
