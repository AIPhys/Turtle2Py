"""Fork of the viz pipeline: from ANY Turtle deck to a viz HTML.

Takes a raw input deck (e.g. after changing a channel/bend/quad config) and
runs the whole two-pass pipeline for it — the same chain that produced
turtle_in.dat -> viz.html — with every file derived from the input name:

  pass 1   gen_deck (wide +-HALF cards)  ->  turtle.exe  ->  <stem>_wide.res
  fit      CENTER / RMS HALF WIDTH      ->  <stem>_card_ranges.json
           (cards = center +- 4*RMS, floors 2 mm / 0.3 mr)
  pass 2   gen_deck (fitted cards)       ->  turtle.exe  ->  <stem>_hist.res
  viz      fast propagation + Turtle histograms (resparse) -> plotly HTML

Intermediates go to <input-dir>/<stem>_viz/; the HTML lands beside the input
as <stem>_viz.html unless out_html is given.  Nothing outside those paths is
touched.  Engine: turtle.exe by default (seconds; regenerate with
`wfl386 turtle.f`), the bit-exact python port as fallback.

Used by the GUI (turtle2py/viz/app.py); also importable directly.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import gen_deck
from .resparse import parse_res

ROOT = Path(__file__).resolve().parents[2]  # project root (holds turtle.exe)

SCALE = 4.0  # card half-width = SCALE * RMS
FLOOR_XY_MM = 2.0  # minimum half-width for x,y cards (mm)
FLOOR_XP_MR = 0.3  # minimum half-width for x',y' cards (mr)

_LOCK = threading.Lock()
_PROC: subprocess.Popen | None = None  # the run currently in flight (for cancel)
_CANCEL = threading.Event()  # set by cancel(): stops the pipeline, not just the run


def _kill_tree(p: subprocess.Popen) -> None:
    """Kill a child and its descendants (Windows launcher stubs spawn grandchildren)."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(p.pid)],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    else:
        p.terminate()


def cancel() -> bool:
    """Stop the pipeline in flight: kill the Turtle run and abort the rest.

    True if a child process was terminated.
    """
    global _PROC
    _CANCEL.set()
    with _LOCK:
        p = _PROC
    if p is not None and p.poll() is None:
        _kill_tree(p)
        return True
    return False


def _span(center: float, rms: float, floor: float) -> list:
    hw = max(SCALE * abs(rms), floor)
    return [round(center - hw, 4), round(center + hw, 4)]


def fit_ranges(res_path: str | Path, out_json: str | Path) -> Path:
    """Per-POI card ranges from a wide-pass .res (CENTER/RMS), in mm and mr.

    Same recipe as viz_card_ranges.json: 4x RMS half-width with 2 mm / 0.3 mr
    floors; z keys in cm, matching gen_deck.load_ranges.
    """
    hs = parse_res(str(res_path))
    by_z: dict = {}
    for h in hs:
        z = round(h.z_m, 3)
        hn, vn = h.hname.upper(), h.vname.upper()
        d = by_z.setdefault(z, {})
        if hn == "X" and vn == "X'":
            d["x"] = _span(h.center_x * 10.0, h.rms_x * 10.0, FLOOR_XY_MM)
            d["xp"] = _span(h.center_y, h.rms_y, FLOOR_XP_MR)
        elif hn == "Y" and vn == "Y'":
            d["y"] = _span(h.center_x * 10.0, h.rms_x * 10.0, FLOOR_XY_MM)
            d["yp"] = _span(h.center_y, h.rms_y, FLOOR_XP_MR)
    full = {str(z): d for z, d in sorted(by_z.items()) if len(d) >= 2}
    if not full:
        raise SystemExit(f"no usable histograms parsed from {res_path}")
    Path(out_json).write_text(json.dumps(full, indent=1), encoding="utf8")
    return Path(out_json)


def run_engine(
    exe: Path, deck: Path, res: Path, engine: str = "auto", log=print
) -> str:
    """Run Turtle on `deck`, writing `res` (both live in deck.parent).

    Turtle reads the input and output file names from stdin (CRLF), so cwd is
    the folder holding them.  Falls back to the bit-exact python port when
    turtle.exe is missing or fails (--engine exe disables the fallback).
    """
    global _PROC
    stdin = f"{deck.name}\r\n{res.name}\r\n".encode("latin-1")
    import os

    env = dict(os.environ, PYTHONPATH=str(ROOT))
    use_exe = engine in ("auto", "exe") and exe.is_file()
    cmd = [str(exe)] if use_exe else [sys.executable, "-m", "turtle2py"]
    label = "turtle.exe" if use_exe else "python port (bit-exact)"
    with _LOCK:
        _PROC = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            cwd=str(deck.parent),
            env=env,
            stdout=subprocess.PIPE if use_exe else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # No console window flashes from the GUI (pythonw): both passes.
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        p = _PROC
    try:
        out = p.communicate(stdin)[0]
        rc = p.returncode
    finally:
        with _LOCK:
            _PROC = None
    if _CANCEL.is_set():
        raise SystemExit("cancelled")
    if rc == 0 and res.is_file():
        return label
    if use_exe and engine == "auto" and p.returncode is not None:
        log(
            f"  turtle.exe rc={rc}: {out.decode('latin-1', 'replace')[-300:]} — falling back to python port"
        )
        return run_engine(exe, deck, res, "py", log)
    raise SystemExit(f"{label} failed on {deck.name}: rc={rc}")


def fork(
    input_deck: str | Path,
    out_html: str | Path | None = None,
    rays: int = 20000,
    seed: int = 12345,
    exe: str | Path | None = None,
    engine: str = "auto",
    work: str | Path | None = None,
    fit: bool = True,
    log=print,
) -> Path:
    inp = Path(input_deck)
    if not inp.is_file():
        raise SystemExit(f"input deck not found: {inp}")
    _CANCEL.clear()
    stem = inp.stem
    work = Path(work) if work else inp.parent / f"{stem}_viz"
    work.mkdir(parents=True, exist_ok=True)
    exe = Path(exe) if exe else ROOT / "turtle.exe"
    out_html = Path(out_html) if out_html else inp.parent / f"{stem}_viz.html"

    t0 = time.time()
    wide_deck, wide_res = work / f"{stem}_wide.dat", work / f"{stem}_wide.res"
    ranges = work / f"{stem}_card_ranges.json"
    viz_deck, hist_res = work / f"{stem}_viz.dat", work / f"{stem}_hist.res"

    # Ray count written into the generated decks (line 2): the python port is
    # driven by the GUI rays field; turtle.exe keeps the input deck's own count.
    deck_rays = rays if engine == "py" else None

    if fit:
        if _CANCEL.is_set():
            raise SystemExit("cancelled")
        log(f"[1/4] pass 1 deck (wide +-12 cards): {wide_deck.name}")
        gen_deck.main(str(inp), str(wide_deck), norays=deck_rays)
        log(f"[2/4] pass 1 run: {run_engine(exe, wide_deck, wide_res, engine, log)}")
        fit_ranges(wide_res, ranges)
        log(f"      card ranges fitted -> {ranges.name}")

    if _CANCEL.is_set():
        raise SystemExit("cancelled")
    log(f"[3/4] pass 2 deck (fitted cards): {viz_deck.name}")
    gen_deck.main(
        str(inp), str(viz_deck), str(ranges) if fit else None, norays=deck_rays
    )
    log(f"      pass 2 run: {run_engine(exe, viz_deck, hist_res, engine, log)}")

    if _CANCEL.is_set():
        raise SystemExit("cancelled")
    from .__main__ import run as viz_run

    log(f"[4/4] visualisation -> {out_html.name}")
    viz_run(str(viz_deck), str(out_html), rays, seed=seed, res=str(hist_res))
    log(f"done in {time.time() - t0:.1f} s")
    return out_html
