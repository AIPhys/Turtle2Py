"""CLI: python -m turtle2py.viz [input.dat] [-o viz.html] [-n NRAYS] [--png viz.png]

Fast visualisation of a Turtle deck: element geometry + descriptions,
x/y beam envelopes, phase-space projections, interactive plotly HTML.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from .model import parse_deck, element_table
from .propagate import emit, trace
from .resparse import parse_res
from .viewer import build_figure


def run(
    inp: str,
    outp: str,
    nrays: int,
    png: str | None = None,
    seed: int = 12345,
    res: str | None = None,
):
    elements, meta = parse_deck(inp)
    rays = emit(nrays, meta["raymax"], meta["pbeam"], seed=seed)
    env = trace(_ctx_of(inp), rays)
    alive = env["alive_mask"]
    if res is None:
        res = "viz_hist.res"
    if res and __import__("os").path.exists(res):
        env["phase_hists"] = parse_res(res)
        print(f"phase histograms: {len(env['phase_hists'])} from {res}")
    fig = build_figure(elements, meta, env, env["rays"], alive)
    ps = env.get("phase_select_js")
    fig.write_html(
        outp,
        include_plotlyjs="cdn",
        post_script=[ps] if ps else None,
    )
    if png:
        try:
            fig.write_image(png)
        except Exception as exc:  # kaleido missing
            print("png export skipped:", exc, file=sys.stderr)
    table = element_table(elements)
    print(f"elements: {len(elements)}  zmax: {meta['zmax']:.2f} cm")
    print(f"rays: {nrays}  surviving: {int(alive.sum())}")
    print(
        f"exit envelope  x_rms={env['xrms'][-1]:.5f} cm  y_rms={env['yrms'][-1]:.5f} cm"
    )
    print(f"html: {outp}")
    return elements, meta, env, table


def _ctx_of(inp: str):
    """SETUP-processed Context (DATA/IDATA) for the fast propagator."""
    from ..io import CardReader, ElementReader
    from ..random import G900
    from ..state import Context
    from ..fields import initze, setup, Out

    lines = open(inp, "rb").read().decode("latin-1").split("\n")
    r = CardReader(lines)
    er = ElementReader(r)
    ctx = Context()
    ctx.rng = G900()
    initze(ctx)
    setup(ctx, r, er, Out())
    return ctx


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m turtle2py.viz")
    ap.add_argument("input", nargs="?", default="turtle_in.dat")
    ap.add_argument("-o", "--out", default="viz.html")
    ap.add_argument("-n", "--rays", type=int, default=20000)
    ap.add_argument("--png", default=None)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument(
        "--res", default="viz_hist.res", help="Turtle .res with phase histograms"
    )
    a = ap.parse_args(argv)
    run(a.input, a.out, a.rays, a.png, a.seed, a.res)


if __name__ == "__main__":
    main()
