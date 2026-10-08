"""Interactive plotly viewer: beamline geometry, envelopes, projections, table.

Layout (one HTML page, browser-native view change / projection / zoom):

  Row 1: 3-D beamline (elements + rays) with camera preset buttons
         (top / side / front / iso) + element description table.
  Row 2: top view x-z, side view y-z (glyphs + aperture overlay),
         surviving rays (axis floored at min survivors, 1k step).
  Row 3: x envelope, y envelope (log scale, mm, rms + max + aperture),
         rays lost per element.
  Row 4: phase-space projections x-x', y-y' and x-y at exit.

Units: z in meters, x,y in mm, x',y' in mr.  Transverse coords are
magnified (MAG) in the 3-D view; z is the base horizontal axis.
"""

from __future__ import annotations

import math
import time

import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots

MAG = 0.5  # mm -> m scale in the 3-D view (transverse magnification)

TYPE_COLOR = {
    "BEND": "#c0392b",
    "QUAD": "#2e86c1",
    "DRIFT": "#95a5a6",
    "SLIT": "#f39c12",
    "FACE": "#8e44ad",
    "SHIFT": "#16a085",
    "PARAMS": "#7f8c8d",
    "CAP": "#d35400",
    "BEAM": "#27ae60",
    "SEXT": "#e84393",
    "SOLO": "#00b894",
    "ROTATE": "#6c5ce7",
    "ACCEL": "#2c3e50",
    "MISALIGN": "#795548",
    "MATRIX": "#607d8b",
}

INK = "#2c3e50"


def _color(e) -> str:
    return TYPE_COLOR.get(e.name, "#bdc3c7")


def _hover(e) -> str:
    lines = [
        f"<b>{e.label or e.name}</b>",
        f"type {e.typ}  {e.name}",
        f"z = {e.z0:.2f} -> {e.z1:.2f} m",
        f"length {e.length:.3f} m",
    ]
    for k, v in e.info.items():
        lines.append(f"{k}: {v:.6g}" if isinstance(v, float) else f"{k}: {v}")
    if e.text:
        lines.append(f"<i>{e.text}</i>")
    return "<br>".join(lines)


def _glyph_shapes(elements):
    """Rectangle glyphs for magnets/slits on the 2-D geometry views (mm)."""
    shapes = []
    for e in elements:
        if e.length <= 0:
            continue
        c = _color(e)
        half = max(e.length * 0.18, 0.15)  # mm
        shapes.append(
            dict(
                type="rect",
                x0=e.z0,
                x1=e.z1,
                y0=-half,
                y1=half,
                fillcolor=c,
                line=dict(color=c, width=1),
                opacity=0.45,
            )
        )
    return shapes


def _aperture_lines(elements, key):
    """Aperture-limit segments on the envelope views (z in m, lim in mm)."""
    segs = []
    for e in elements:
        if e.typ == 6:
            a = abs(float(e.info.get("lo", 0.0)))
            b = abs(float(e.info.get("hi", 0.0)))
            lim = a if key == "x" else b
        elif e.typ == 4:
            a = abs(float(e.info.get("aperture_x", 0.0)))
            b = abs(float(e.info.get("aperture_y", 0.0)))
            lim = a if key == "x" else b
        else:
            continue
        # skip oversized apertures (> 20 mm): they dwarf the beam envelope
        if lim and lim * 10.0 <= 20.0:
            segs.append((e.z0, e.z1, lim * 10.0))
    return segs


def _camera_buttons(scene_x=(0.0, 0.64), scene_y=(0.825, 1.0)):
    """Camera presets: relayout of scene.camera.eye/up (z = base axis).

    Anchored to the lower-left corner of the 3-D scene panel (figure coords).
    """
    return dict(
        type="buttons",
        direction="right",
        x=scene_x[0] + 0.015,
        y=scene_y[0] + 0.005,
        xanchor="left",
        yanchor="bottom",
        pad=dict(r=8, t=8),
        showactive=True,
        buttons=[
            dict(
                label="top",
                method="relayout",
                args=[
                    {
                        "scene.camera.eye": dict(x=0.0, y=1.6, z=0.0),
                        "scene.camera.up": dict(x=0, y=0, z=1),
                    }
                ],
            ),
            dict(
                label="side",
                method="relayout",
                args=[
                    {
                        "scene.camera.eye": dict(x=0.0, y=0.0, z=1.6),
                        "scene.camera.up": dict(x=0, y=1, z=0),
                    }
                ],
            ),
            dict(
                label="front",
                method="relayout",
                args=[
                    {
                        "scene.camera.eye": dict(x=1.6, y=0.0, z=0.0),
                        "scene.camera.up": dict(x=0, y=0, z=1),
                    }
                ],
            ),
            dict(
                label="iso",
                method="relayout",
                args=[
                    {
                        "scene.camera.eye": dict(x=1.2, y=0.9, z=0.9),
                        "scene.camera.up": dict(x=0, y=0, z=1),
                    }
                ],
            ),
        ],
    )


def _phase(fig, row, col, u, v, lu, lv, name):
    """Density contour + points for a phase-space projection."""
    fig.add_trace(
        go.Histogram2dContour(
            x=u,
            y=v,
            nbinsx=64,
            nbinsy=64,
            colorscale="Blues",
            showscale=False,
            contours=dict(coloring="fill"),
            opacity=0.85,
            name=name,
            hoverinfo="skip",
        ),
        row,
        col,
    )
    idx = np.linspace(0, len(u) - 1, min(2500, len(u))).astype(int)
    fig.add_trace(
        go.Scattergl(
            x=u[idx],
            y=v[idx],
            mode="markers",
            marker=dict(size=3, color=INK, opacity=0.45),
            name=f"{name} pts",
            showlegend=False,
        ),
        row,
        col,
    )
    fig.update_xaxes(title_text=lu, row=row, col=col)
    fig.update_yaxes(title_text=lv, row=row, col=col)


def _hist_smooth(h, n=95):
    """Bilinear-smoothed density on an n x n grid over the card range.

    The reconstructed 19x19 grid is quantized: dots in coarse cells and
    contours along cell edges read as a ladder.  Bilinear interpolation
    (scipy.ndimage.zoom, order=1, node-preserving) gives a smooth density;
    the total is rescaled to the exact row-total sum.
    Returns (xf, yf, zf) with xf/yf fine bin centres in plot units.
    """
    from scipy.ndimage import zoom

    from .resparse import reconstruct_grid

    k = 10.0 if h.hunit.upper() == "CM" else 1.0
    kv = 10.0 if h.vunit.upper() == "CM" else 1.0
    g = np.asarray(reconstruct_grid(h), dtype=float)  # [iy][ix]
    if g.size == 0:
        return [], [], []
    zf = zoom(g, (n / g.shape[0], n / g.shape[1]), order=1)
    s, t = zf.sum(), g.sum()
    if s > 0 and t > 0:
        zf = zf * (t / s)
    xf = np.linspace(h.xmin * k, h.xmax * k, n)
    yf = np.linspace(h.ymin * kv, h.ymax * kv, n)
    return xf, yf, zf


def seed_of(name, z_m):
    """Deterministic per-panel/per-z RNG seed for histogram dot sampling."""
    import zlib

    return zlib.crc32(name.encode()) ^ int(round(float(z_m) * 1000))


def _hist_points(h, nmax=3000, seed=12345):
    """Scatter points sampled from the smoothed Turtle density.

    Sampling the bilinear-smoothed 95x95 grid (weights = interpolated counts,
    points uniform in the fine cell) removes the 19x19 cell quantization that
    reads as a ladder.  Counts are BCDWR-saturated, so the sample is a visual
    approximation of the true density, not exact rays.
    """
    x, y, z = _hist_smooth(h)
    if not len(x):
        return np.array([]), np.array([])
    dx = (x[1] - x[0]) if len(x) > 1 else 0.0
    dy = (y[1] - y[0]) if len(y) > 1 else 0.0
    counts = np.asarray(z, dtype=float).ravel()
    tot = counts.sum()
    if tot <= 0:
        return np.array([]), np.array([])
    rng = np.random.default_rng(seed)
    n = int(min(nmax, tot))
    idx = rng.choice(len(counts), size=n, p=counts / tot)
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    iy, ix = np.divmod(idx, len(xs))  # ix = y-row, iy = x-col
    px = xs[ix] + (rng.random(n) - 0.5) * dx
    py = ys[iy] + (rng.random(n) - 0.5) * dy
    return px, py


def _phase_ellipses(h, ks=(1.0, 2.0, 3.0), npts=129):
    """Phase ellipses (k-sigma) from the smoothed density moments.

    Weighted mean and covariance of the density grid -> eigen axes a>=b and
    major-axis angle th; returns [(ex, ey), ...] per k.  For a matched beam
    these are the Courant-Snyder phase ellipses.
    """
    xf, yf, zf = _hist_smooth(h)
    if not len(xf):
        return []
    w = np.asarray(zf, dtype=float)
    W = w.sum()
    if W <= 0:
        return []
    X, Y = np.meshgrid(np.asarray(xf, dtype=float), np.asarray(yf, dtype=float))
    mx = float((w * X).sum() / W)
    my = float((w * Y).sum() / W)
    dx, dy = X - mx, Y - my
    sxx = float((w * dx * dx).sum() / W)
    syy = float((w * dy * dy).sum() / W)
    sxy = float((w * dx * dy).sum() / W)
    evals, evecs = np.linalg.eigh(np.array([[sxx, sxy], [sxy, syy]]))
    evals = np.clip(evals, 0.0, None)
    a, b = float(np.sqrt(evals[-1])), float(np.sqrt(evals[0]))
    th = float(np.arctan2(evecs[1, -1], evecs[0, -1]))
    t = np.linspace(0.0, 2.0 * np.pi, npts)
    ct, st = np.cos(t), np.sin(t)
    cth, sth = np.cos(th), np.sin(th)
    out = []
    for k in ks:
        ex = mx + k * (a * ct * cth - b * st * sth)
        ey = my + k * (a * ct * sth + b * st * cth)
        out.append((ex, ey))
    return out


def _fit_range(vals, lo, hi, pad=0.06):
    """Axis range covering the card box AND the plotted values (ellipses)."""
    vals = [float(v) for v in vals]
    a = min([lo] + vals)
    b = max([hi] + vals)
    d = max(b - a, 1e-4)
    return [a - pad * d, b + pad * d]


def _phase_hist(fig, row, col, h, lu, lv, name):
    """Phase panel from a Turtle 2-D histogram: sampled dots + phase ellipses."""
    px, py = _hist_points(h, seed=seed_of(name, h.z_m))
    fig.add_trace(
        go.Scatter(
            x=px,
            y=py,
            mode="markers",
            marker=dict(size=3, color=INK, opacity=0.45),
            name=name,
            hoverinfo="skip",
        ),
        row,
        col,
    )
    ell = _phase_ellipses(h)
    for k, (ex, ey) in zip((1, 2, 3), ell):
        fig.add_trace(
            go.Scatter(
                x=ex,
                y=ey,
                mode="lines",
                line=dict(width=1.0, color="#39618f"),
                opacity=0.8,
                name=f"{name} {k}sig",
                showlegend=False,
                hoverinfo="skip",
                visible=False,  # toggled by the "ellipses" control
            ),
            row,
            col,
        )
    kx = 10.0 if h.hunit.upper() == "CM" else 1.0
    ky = 10.0 if h.vunit.upper() == "CM" else 1.0
    exs = [v for e in ell for v in e[0]] + list(px)
    eys = [v for e in ell for v in e[1]] + list(py)
    fig.update_xaxes(
        title_text=lu,
        row=row,
        col=col,
        range=_fit_range(exs, h.xmin * kx, h.xmax * kx),
    )
    fig.update_yaxes(
        title_text=lv,
        row=row,
        col=col,
        range=_fit_range(eys, h.ymin * ky, h.ymax * ky),
    )


def _contour_toggle_menu(contour_traces):
    """On/off control for the phase-panel ellipse overlays (dots stay)."""
    return dict(
        type="dropdown",
        direction="up",
        x=0.20,
        y=0.0,
        xanchor="left",
        yanchor="bottom",
        pad=dict(r=10, t=10),
        showactive=True,
        active=0,
        buttons=[
            dict(
                label="ellipses: off",
                method="restyle",
                args=[{"visible": [False] * len(contour_traces)}, list(contour_traces)],
            ),
            dict(
                label="ellipses: on",
                method="restyle",
                args=[{"visible": [True] * len(contour_traces)}, list(contour_traces)],
            ),
        ],
    )


def _phase_hist_payload(hists, trace_ids):
    """Per-z phase panel state for the custom JS z-select.

    hists: list[PhaseHist] from resparse.parse_res (3 pairs per z: x-x', y-y', x-y).
    trace_ids: [(dot, e1, e2, e3), ...] for panels (x-x', y-y', x-y).
    All three panels switch per z (x-y cards are emitted at every POI).

    Plotly dropdowns cannot combine restyle + relayout (one method per
    button), and per-z axis ranges now differ (cards are fitted to the beam),
    so z switching is done by a JS <select> calling Plotly.restyle +
    Plotly.relayout.  Restyle cycling form (verified in this plotly build):
    args = [obj, traceIndices] with value arrays cycling across traces in
    order; scatter traces ignore z.  Numeric-keyed trace objects in
    Plotly.update are NOT applied by this build - do not use them.
    """
    by_z: dict = {}
    for h in hists:
        by_z.setdefault(round(h.z_m, 3), []).append(h)
    zs = sorted(by_z, reverse=True)  # exit first: matches the initial render
    tix = [t for pair in trace_ids for t in pair]  # 12 traces: dots + 3 ellipses
    payload = {"labels": [], "x": [], "y": [], "ranges": [], "tix": tix}
    for zm in zs:
        pairs = by_z[zm]
        per = {
            0: next(
                (
                    h
                    for h in pairs
                    if h.hname.upper() == "X" and h.vname.upper() == "X'"
                ),
                None,
            ),
            1: next(
                (
                    h
                    for h in pairs
                    if h.hname.upper() == "Y" and h.vname.upper() == "Y'"
                ),
                None,
            ),
            2: next(
                (h for h in pairs if h.hname.upper() == "X" and h.vname.upper() == "Y"),
                None,
            ),
        }
        xs: list = []
        ys: list = []
        rng: list = []
        for i in (0, 1, 2):
            h = per[i]
            if h is None:
                xs += [[]] * 4
                ys += [[]] * 4
                rng += [[0, 1], [0, 1]]
                continue
            kx = 10.0 if h.hunit.upper() == "CM" else 1.0
            ky = 10.0 if h.vunit.upper() == "CM" else 1.0
            nm = ["x-x'", "y-y'", "x-y"][i]
            px, py = _hist_points(h, seed=seed_of(nm, zm))
            xs.append([round(float(v), 4) for v in px])
            ys.append([round(float(v), 4) for v in py])
            ell = _phase_ellipses(h)
            exs, eys = list(px), list(py)
            for ex, ey in ell:
                xs.append([round(float(v), 4) for v in ex])
                ys.append([round(float(v), 4) for v in ey])
                exs += list(ex)
                eys += list(ey)
            rng += [
                [round(v, 4) for v in _fit_range(exs, h.xmin * kx, h.xmax * kx)],
                [round(v, 4) for v in _fit_range(eys, h.ymin * ky, h.ymax * ky)],
            ]
        payload["labels"].append(f"z = {zm:.2f} m")
        payload["x"].append(xs)
        payload["y"].append(ys)
        payload["ranges"].append(rng)
    return payload


def _phase_select_js(payload):
    """post_script JS: native <select> switching phase panels per z.

    Runs inside plotly's write_html template with `gd` and `Plotly` in scope.
    """
    import json

    data = json.dumps(payload, separators=(",", ":"))
    return (
        "var PH=" + data + ";(function boot(){var Plotly=window.Plotly;"
        "var gd=document.querySelector('.js-plotly-plot');"
        "if(!Plotly||!gd){setTimeout(boot,200);return;}"
        "var s=document.createElement('select');"
        "s.style.cssText='position:absolute;left:10px;bottom:10px;z-index:10;"
        "font:13px sans-serif;color:#1b2733;background:#fff;border:1px solid #99b;"
        "border-radius:4px;padding:3px 6px;outline:none;';"
        "PH.labels.forEach(function(L,i){var o=document.createElement('option');"
        "o.value=i;o.textContent=L;s.appendChild(o);});"
        "s.onchange=function(){var i=+s.value;"
        "Plotly.restyle(gd,{x:PH.x[i],y:PH.y[i]},PH.tix);"
        "var r=PH.ranges[i],L={};for(var j=0;j<r.length;j++){"
        "L[(j%2?'yaxis':'xaxis')+(7+(j>>1))+'.range']=r[j];}"
        "Plotly.relayout(gd,L)};"
        "var p=gd.parentNode;p.style.position='relative';p.appendChild(s);})();"
    )


def _phase_z_menu(fig, env, panel_axes, trace_ids):
    """Dropdown: choose the z position where the phase-space plots are taken.

    panel_axes: [(row,col), ...] matching trace_ids groups [(contour, pts), ...].
    Restyles the 6 phase traces (contour + points per panel) and fits axes.
    """
    z = np.asarray(env["z"], dtype=float)
    ph = env.get("phase_hist")
    ah = env.get("alive_hist")
    if not ph or not ah:
        return None
    ns = len(ph)
    # phase_hist[k] is recorded after advancing to z[k+1] (z[0] = source)
    zz = z[1 : ns + 1] if len(z) >= ns + 1 else z[:ns]
    stride = max(1, ns // 24)
    picks = list(range(0, ns, stride))
    if picks[-1] != ns - 1:
        picks.append(ns - 1)
    picks = picks[::-1]  # exit first: matches the initial (exit) phase plots
    buttons = []
    for s in picks:
        P = np.asarray(ph[s])
        A = np.asarray(ah[s], dtype=bool)
        if A.any():
            P = P[A]
        if len(P) < 2:
            continue
        # axis ranges from the FULL alive distribution (boundary points);
        # only the plotted points are subsampled for size
        fx, fxp, fy, fyp = P[:, 0] * 10.0, P[:, 1], P[:, 2] * 10.0, P[:, 3]
        if len(P) > 3000:
            P = P[np.linspace(0, len(P) - 1, 3000).astype(int)]
        x, xp, y, yp = P[:, 0] * 10.0, P[:, 1], P[:, 2] * 10.0, P[:, 3]
        coords = [(x, xp), (y, yp), (x, y)]
        full = [(fx, fxp), (fy, fyp), (fx, fy)]
        args: dict = {}
        layout_args: dict = {}
        for (ci, pi), (u, v) in zip(trace_ids, coords):
            args[f"trace{ci}.x"] = u
            args[f"trace{ci}.y"] = v
            args[f"trace{pi}.x"] = u
            args[f"trace{pi}.y"] = v
        for (ax, ay), (u, v) in zip(panel_axes, full):
            pad_u = max((u.max() - u.min()) * 0.06, 1e-4)
            pad_v = max((v.max() - v.min()) * 0.06, 1e-4)
            layout_args[f"{ax}.range"] = [
                float(u.min() - pad_u),
                float(u.max() + pad_u),
            ]
            layout_args[f"{ay}.range"] = [
                float(v.min() - pad_v),
                float(v.max() + pad_v),
            ]
        buttons.append(
            dict(
                label=f"z = {zz[s]:.2f} m",
                method="update",
                args=[args, layout_args],
            )
        )
    return dict(
        type="dropdown",
        direction="up",
        x=0.0,
        y=0.0,
        xanchor="left",
        yanchor="bottom",
        pad=dict(r=10, t=10),
        showactive=True,
        buttons=buttons,
    )


def build_figure(elements, meta, env, rays, alive):
    z = np.asarray(env["z"], dtype=float)  # m (deck lengths are meters)
    xrms = np.asarray(env["xrms"]) * 10.0  # mm
    xmax = np.asarray(env["xmax"]) * 10.0
    yrms = np.asarray(env["yrms"]) * 10.0
    ymax = np.asarray(env["ymax"]) * 10.0
    alive_n = np.asarray(env["alive"], dtype=float)
    loss = np.asarray(env["loss"], dtype=float)

    fig = make_subplots(
        rows=4,
        cols=3,
        subplot_titles=(
            "3-D beamline",
            "element descriptions",
            "top view  x - z",
            "side view  y - z",
            "surviving rays",
            "x envelope  (mm, log)",
            "y envelope  (mm, log)",
            "rays lost  (log)",
            "phase space  x - x'",
            "phase space  y - y'",
            "x - y  at exit",
        ),
        specs=[
            [{"type": "scene", "colspan": 2}, None, {"type": "table"}],
            [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
        ],
        horizontal_spacing=0.09,
        vertical_spacing=0.10,
    )

    # ---- 1. 3-D beamline (z = base horizontal axis, stretched) ----------
    ex, ec, es, eh = [], [], [], []
    for e in elements:
        if e.typ >= 50:
            continue
        ex.append(0.5 * (e.z0 + e.z1))
        ec.append(_color(e))
        es.append(max(3.0, min(12.0, 3.0 + 1.2 * e.length)))
        eh.append(_hover(e))
    fig.add_trace(
        go.Scatter3d(
            x=ex,
            y=np.zeros(len(ex)),
            z=np.zeros(len(ex)),
            mode="markers",
            marker=dict(size=es, color=ec, symbol="square", opacity=0.95),
            hovertext=eh,
            hoverinfo="text",
            name="elements",
        ),
        1,
        1,
    )
    traj = env.get("traj")
    if traj:
        step = max(1, len(traj) // 160)
        T = np.asarray(traj[::step])
        nray = rays.shape[0]
        show = min(nray, 150)
        idx = np.linspace(0, nray - 1, show).astype(int)
        xs, ys, zs = [], [], []
        for k in idx:
            pts = T[:, k, :]  # (x, y, z) in cm
            xs.append(pts[:, 2])  # z in m (base axis)
            ys.append(pts[:, 1] * MAG * 10.0)  # y mm -> m x MAG
            zs.append(pts[:, 0] * MAG * 10.0)  # x mm -> m x MAG
            xs.append([None] * len(pts))
            ys.append([None] * len(pts))
            zs.append([None] * len(pts))
        fig.add_trace(
            go.Scatter3d(
                x=np.concatenate(xs),
                y=np.concatenate(ys),
                z=np.concatenate(zs),
                mode="lines",
                line=dict(color=INK, width=1.5),
                opacity=0.30,
                name="rays",
                hoverinfo="skip",
            ),
            1,
            1,
        )
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title="z (m)",
                showbackground=True,
                backgroundcolor="rgb(245,247,250)",
                gridcolor="rgb(210,215,222)",
            ),
            yaxis=dict(
                title="y (mm, x0.5)",
                showbackground=True,
                backgroundcolor="rgb(245,247,250)",
                gridcolor="rgb(210,215,222)",
            ),
            zaxis=dict(
                title="x (mm, x0.5)",
                showbackground=True,
                backgroundcolor="rgb(245,247,250)",
                gridcolor="rgb(210,215,222)",
            ),
            camera=dict(eye=dict(x=1.2, y=0.9, z=0.9), up=dict(x=0, y=0, z=1)),
            aspectmode="manual",
            aspectratio=dict(x=1.0, y=0.06, z=0.06),
        )
    )

    # ---- 2. element description table (no histogram cards, z 2 decimals) -
    from .model import element_table

    rows = [r for r in element_table(elements) if int(r["type"]) < 50]
    cols = ["i", "type", "name", "label", "z0", "z1", "length", "text"]
    cells = {c: [r.get(c, "") for r in rows] for c in cols}
    for c in ("z0", "z1"):
        cells[c] = [f"{v:.2f}" for v in cells[c]]
    cells["length"] = [f"{v:.3f}" for v in cells["length"]]
    fig.add_trace(
        go.Table(
            columnwidth=[38, 38, 58, 56, 46, 46, 50, 210],
            header=dict(
                values=[
                    "i",
                    "type",
                    "name",
                    "label",
                    "z0 (m)",
                    "z1 (m)",
                    "len (m)",
                    "description",
                ],
                fill_color=INK,
                font=dict(color="white", size=10),
                align="left",
            ),
            cells=dict(
                values=[cells[c] for c in cols],
                fill_color=[["#f8f9fa", "#eef2f5"] * len(rows)],
                align="left",
                font=dict(size=9),
            ),
        ),
        1,
        3,
    )

    # ---- 3/4. top & side views with glyphs + aperture overlay ------------
    for row, col, key in ((2, 1, "x"), (2, 2, "y")):
        rms, mx = (xrms, xmax) if key == "x" else (yrms, ymax)
        fig.add_trace(
            go.Scatter(
                x=z,
                y=mx,
                mode="lines",
                line=dict(color="#d62728", width=1, dash="dot"),
                name=f"{key} max",
            ),
            row,
            col,
        )
        fig.add_trace(
            go.Scatter(
                x=z,
                y=-mx,
                mode="lines",
                line=dict(color="#d62728", width=1, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            ),
            row,
            col,
        )
        fig.add_trace(
            go.Scatter(
                x=z,
                y=rms,
                mode="lines",
                line=dict(color="#1f77b4", width=2),
                fill="tonexty",
                fillcolor="rgba(31,119,180,0.15)",
                name=f"{key} rms",
            ),
            row,
            col,
        )
        fig.add_trace(
            go.Scatter(
                x=z,
                y=-rms,
                mode="lines",
                line=dict(color="#1f77b4", width=2),
                showlegend=False,
                hoverinfo="skip",
            ),
            row,
            col,
        )
        for s in _glyph_shapes(elements):
            fig.add_shape(**s, row=row, col=col)
        for z0, z1, lim in _aperture_lines(elements, key):
            for sgn in (1, -1):
                fig.add_shape(
                    type="line",
                    x0=z0,
                    x1=z1,
                    y0=sgn * lim,
                    y1=sgn * lim,
                    line=dict(color="#f39c12", width=2),
                    row=row,
                    col=col,
                )
        fig.update_xaxes(title_text="z  (m)", row=row, col=col)
        fig.update_yaxes(title_text=f"{key}  (mm)", row=row, col=col)
        # zoom to the beam: apertures above 20 mm are excluded, so the y-range
        # follows the envelope, not the oversized openings
        lim = max(float(np.nanmax(mx)), 0.5) * 1.35
        fig.update_yaxes(range=[-lim, lim], row=row, col=col)

    # ---- 5. surviving rays (floor = min survivors, 1k step) + loss markers ----
    fig.add_trace(
        go.Scatter(
            x=z,
            y=alive_n,
            mode="lines",
            line=dict(color="#27ae60", width=2, shape="hv"),
            fill="tozeroy",
            fillcolor="rgba(39,174,96,0.12)",
            name="alive",
        ),
        2,
        3,
    )
    hit = loss > 0
    fig.add_trace(
        go.Scatter(
            x=z[hit],
            y=alive_n[hit],
            mode="markers",
            marker=dict(size=7, symbol="x", color="#c0392b"),
            name="loss",
        ),
        2,
        3,
    )
    fig.update_xaxes(title_text="z  (m)", row=2, col=3)
    # y floor: minimum survivors rounded down to 1k, so the loss curve fills
    # the panel (4561 -> 4000) instead of a fixed 15k window.
    lo_rays = float(int(np.min(alive_n) // 1000) * 1000)
    hi_rays = float(np.max(alive_n))
    fig.update_yaxes(
        title_text="rays",
        row=2,
        col=3,
        range=[lo_rays, hi_rays + 0.02 * max(hi_rays - lo_rays, 1)],
    )

    # ---- 6/7. x & y envelopes (log scale, mm) ----------------------------
    for row, col, key in ((3, 1, "x"), (3, 2, "y")):
        rms, mx = (xrms, xmax) if key == "x" else (yrms, ymax)
        fig.add_trace(
            go.Scatter(
                x=z,
                y=mx,
                mode="lines",
                line=dict(color="#d62728", width=2.5),
                name=f"{key} max",
            ),
            row,
            col,
        )
        fig.add_trace(
            go.Scatter(
                x=z,
                y=rms,
                mode="lines",
                line=dict(color="#1f77b4", width=3),
                name=f"{key} rms",
            ),
            row,
            col,
        )
        for z0, z1, lim in _aperture_lines(elements, key):
            fig.add_shape(
                type="line",
                x0=z0,
                x1=z1,
                y0=lim,
                y1=lim,
                line=dict(color="#f39c12", width=2, dash="dash"),
                row=row,
                col=col,
            )
        fig.update_xaxes(title_text="z  (m)", row=row, col=col)
        lo = max(min(np.min(rms[rms > 0]), np.min(mx[mx > 0])) / 2.0, 1e-3)
        hi = max(np.max(mx), np.max(rms)) * 2.0
        fig.update_yaxes(
            title_text=f"{key}  (mm)",
            row=row,
            col=col,
            type="log",
            range=[math.log10(lo), math.log10(hi)],
        )

    # ---- 8. rays lost per element ----------------------------------------
    # Bars only where rays are actually lost: on a log axis, zero-height
    # bars are invisible and the panel reads as empty.
    hit = loss > 0
    bw = 0.8 * (z.max() - z.min()) / max(len(z), 1)  # one sample slot, visible
    fig.add_trace(
        go.Bar(
            x=z[hit],
            y=loss[hit],
            marker_color="#c0392b",
            name="loss",
            text=loss[hit].astype(int),
            textposition="outside",
            textfont=dict(size=10, color="#c0392b"),
            width=bw,
        ),
        3,
        3,
    )
    fig.update_xaxes(title_text="z  (m)", row=3, col=3)
    fig.update_yaxes(
        title_text="rays lost",
        row=3,
        col=3,
        range=[0, max(loss.max() * 1.25, 1)],
    )

    # ---- 9. phase-space projections from Turtle histograms (exit z) -------
    hists = env.get("phase_hists") or []
    ctoggle = None
    phase_js = None
    menu = None
    if hists:
        by_z: dict = {}
        for h in hists:
            by_z.setdefault(round(h.z_m, 3), []).append(h)
        zexit = max(by_z)
        pairs = by_z[zexit]
        hx = next(
            (h for h in pairs if h.hname.upper() == "X" and h.vname.upper() == "X'"),
            None,
        )
        hy = next(
            (h for h in pairs if h.hname.upper() == "Y" and h.vname.upper() == "Y'"),
            None,
        )
        hxy = next(
            (h for h in pairs if h.hname.upper() == "X" and h.vname.upper() == "Y"),
            None,
        )
        base = len(fig.data)
        _phase_hist(fig, 4, 1, hx, "x (mm)", "x' (mr)", "x-x'")
        _phase_hist(fig, 4, 2, hy, "y (mm)", "y' (mr)", "y-y'")
        if hxy is not None:
            _phase_hist(fig, 4, 3, hxy, "x (mm)", "y (mm)", "x-y")
        else:
            R = np.asarray(rays)[np.asarray(alive)]
            _phase(fig, 4, 3, R[:, 0] * 10.0, R[:, 2] * 10.0, "x (mm)", "y (mm)", "x-y")
        npanel = len(fig.data) - base  # 12 with x-y from the deck, else 9
        npair = npanel // 4
        groups = [tuple(base + 4 * p + k for k in range(4)) for p in range(npair)]
        phase_js = _phase_select_js(_phase_hist_payload(hists, groups))
        ctoggle = _contour_toggle_menu([t for g in groups for t in g[1:]])
    else:
        R = np.asarray(rays)[np.asarray(alive)]
        _phase(fig, 4, 1, R[:, 0] * 10.0, R[:, 1], "x (mm)", "x' (mr)", "x-x'")
        _phase(fig, 4, 2, R[:, 2] * 10.0, R[:, 3], "y (mm)", "y' (mr)", "y-y'")
        _phase(fig, 4, 3, R[:, 0] * 10.0, R[:, 2] * 10.0, "x (mm)", "y (mm)", "x-y")
        menu = _phase_z_menu(
            fig,
            env,
            panel_axes=[
                ("xaxis7", "yaxis7"),
                ("xaxis8", "yaxis8"),
                ("xaxis9", "yaxis9"),
            ],
            trace_ids=[
                (len(fig.data) - 6, len(fig.data) - 5),
                (len(fig.data) - 4, len(fig.data) - 3),
                (len(fig.data) - 2, len(fig.data) - 1),
            ],
        )

    # ---- view-change camera buttons ----------------------------------------
    menus = [_camera_buttons()]
    if menu is not None:
        menus.append(menu)
        fig.add_annotation(
            text="phase z \u2192",
            xref="paper",
            yref="paper",
            x=0.075,
            y=0.005,
            xanchor="left",
            showarrow=False,
            font=dict(size=12, color=INK),
        )
    if phase_js is not None:
        fig.add_annotation(
            text="\u2190 phase z",
            xref="paper",
            yref="paper",
            x=0.095,
            y=0.005,
            xanchor="left",
            showarrow=False,
            font=dict(size=12, color=INK),
        )
    if ctoggle is not None:
        menus.append(ctoggle)
        fig.add_annotation(
            text="phase ellipses \u2192",
            xref="paper",
            yref="paper",
            x=0.185,
            y=0.005,
            xanchor="left",
            showarrow=False,
            font=dict(size=12, color=INK),
        )
    fig.update_layout(updatemenus=menus)

    fig.update_layout(
        template="plotly_white",
        title=(
            f"Turtle2Py beamline — {meta.get('comment', '')[:70]}<br>"
            f"<sup>{int(rays.shape[0]):,} rays traced · {int(np.asarray(alive).sum()):,} surviving · "
            f"Pbeam = {meta['pbeam']:.6f} GeV/c · zmax = {meta['zmax']:.2f} m · "
            f"{len(elements)} elements · build {time.strftime('%Y-%m-%d %H:%M:%S')}</sup>"
        ),
        height=1500,
        width=1650,
        hovermode="closest",
        legend=dict(orientation="h", y=1.035, x=0),
        margin=dict(t=120, b=50, l=60, r=40),
        # NO uirevision: any persisted/zoomed axis range would override the
        # dropdown's axis ranges (points outside the chart area). The dropdown
        # is the intended way to change the phase-panel views.
    )
    env["phase_select_js"] = phase_js
    return fig
