"""Generate a visualisation deck: strip positive histogram cards, insert 2-D
phase histogram pairs (x-x', y-y') at ~12 z POIs, reduced ray count.

Line-based: the original deck's physical lines are preserved (Turtle reads
80-char cards; multi-line cards must stay intact).  Only pure histogram-card
lines are removed and short histogram lines are inserted after boundary lines.

Card semantics (turtle.f SETUP label 450):
  51 k n a b dx  -> X axis of a 2-D histogram (n=1 x CM, 2 x' MR)
  52 k n a b dx  -> Y axis of a 2-D histogram (n=3 y CM, 4 y' MR)
  INTVL = (b-a)/dx; NA = min(INTVL,100); Y card reserves (NA+1)*(INTVL+1)+5
  cells from MTABLE(10000).  No flag -> histogram fills at the card's z.
"""

import json
import re
import sys

NORAYS = 10000
NPOI = 12
HALF = 12.0  # card half-range, cm / mr (fallback when no ranges file)
NBIN = 15  # bins per axis (MTABLE budget: 12 POIs * 3 pairs * 261 = 9396)
NBIN_XY = 15  # x-y panel at every POI


def load_ranges(path):
    """Per-POI fitted card ranges from a pass-1 .res: {z_m: {x,xp,y,yp}} in mm/mr.

    Returns sorted [(z_cm, dict)]; cards are in cm (x,y) and mr (x',y').
    The .res prints z in cm (UNIT(8) M label), same units as the deck z.
    """
    r = json.load(open(path))
    return sorted((float(k), v) for k, v in r.items())


def range_for(rr, z_cm):
    return min(rr, key=lambda kv: abs(kv[0] - z_cm))[1]


ADVANCE = {3, 4, 5, 11, 18, 19}  # APLIM: z += datum[1]

NUM = re.compile(r"[-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?")


def split_cards(line: str):
    """Split one physical line into card bodies (text between ';' separators)."""
    out = []
    buf = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c == "/":
            j = line.find("/", i + 1)
            if j == -1:
                buf.append(line[i:])
                i = n
            else:
                buf.append(line[i : j + 1])
                i = j + 1
            continue
        if c == ";":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    if "".join(buf).strip():
        out.append("".join(buf))
    return out


def card_type(body: str):
    """Return (typ, signed, nfl, datum) for a card body; None if not numeric."""
    txt = re.sub(r"/[^/]*/", " ", body).replace(";", " ")
    toks = NUM.findall(txt)
    if not toks:
        return None
    t = float(toks[0])
    if t == 0:
        return None
    typ = int(abs(t))
    nfl = 0
    if abs(t - typ) > 1e-6:
        nfl = int(round(abs(round(t, 2) - typ) * 10))
    datum = [float(x) for x in toks[1:]]
    return typ, t, nfl, datum


def main(inp="turtle_in.dat", out="turtle_viz.dat", ranges=None, norays=None):
    """norays: ray count written to line 2 of the output deck.  None keeps the
    input deck's own line-2 value (the deck's ray count)."""
    text = open(inp, "rb").read().decode("latin-1")
    lines = text.split("\n")
    if norays is None:
        try:
            norays = int(lines[1].strip())
        except (IndexError, ValueError):
            norays = NORAYS

    # z after each line; identify histogram-card lines.
    z = 0.0
    line_z = []
    line_hist = []
    for li, line in enumerate(lines):
        adv = 0.0
        is_hist = False
        for body in split_cards(line):
            info = card_type(body)
            if info is None:
                continue
            typ, t, nfl, datum = info
            sign = 1 if t > 0 else -1
            if sign > 0 and typ in (50, 51, 52, 53):
                is_hist = True
            if sign > 0 and typ in ADVANCE and len(datum) >= 1:
                adv += datum[0]
        z += adv
        line_z.append(z)
        line_hist.append(is_hist)
    zmax = z

    # Histogram cards are illegal before the beam card (SETUP flushes the run).
    beam_li = next(
        li
        for li, line in enumerate(lines)
        if any(
            (lambda i: i and i[0] == 1 and i[1] > 0)(card_type(b))
            for b in split_cards(line)
        )
    )
    # POI targets: uniform grid incl. 0 and zmax, snapped to line boundaries
    # at/after the beam card.
    targets = [zmax * k / (NPOI - 1) for k in range(NPOI)]
    poi = []
    for tgt in targets:
        li = min(range(beam_li, len(lines)), key=lambda k: abs(line_z[k] - tgt))
        poi.append((line_z[li], li))
    seen = set()
    poi = [p for p in poi if not (p[1] in seen or seen.add(p[1]))]

    rr = load_ranges(ranges) if ranges else None

    def card(ncoord, lo, hi, nbin, typ):
        """Histogram axis card: typ 51=horizontal, 52=vertical; ncoord 1=x,2=x',3=y,4=y'.

        lo/hi in mm (x,y) or mr (x',y'); cards take cm for x,y, mr for x',y'.
        """
        unit = 0.1 if ncoord in (1, 3) else 1.0  # cm axes: mm -> cm
        a, b = lo * unit, hi * unit
        dx = (b - a) / nbin
        return f" {typ} {ncoord} {a:.6f} {b:.6f} {dx:.10f};"

    inserts = {}
    for za, li in poi:
        if rr:
            d = range_for(rr, za)
            body = (
                card(1, d["x"][0], d["x"][1], NBIN, 51)
                + "\n"
                + card(2, d["xp"][0], d["xp"][1], NBIN, 52)
                + "\n"
                + card(3, d["y"][0], d["y"][1], NBIN, 51)
                + "\n"
                + card(4, d["yp"][0], d["yp"][1], NBIN, 52)
                + "\n"
                + card(1, d["x"][0], d["x"][1], NBIN_XY, 51)
                + "\n"
                + card(3, d["y"][0], d["y"][1], NBIN_XY, 52)
            )
        else:
            s = 2 * HALF / NBIN
            body = (
                f" 51 1 {-HALF} {HALF} {s:.10f};\n"
                f" 52 2 {-HALF} {HALF} {s:.10f};\n"
                f" 51 3 {-HALF} {HALF} {s:.10f};\n"
                f" 52 4 {-HALF} {HALF} {s:.10f};\n"
                f" 51 1 {-HALF} {HALF} {s:.10f};\n"
                f" 52 3 {-HALF} {HALF} {s:.10f};"
            )
        inserts[li] = inserts.get(li, "") + body + "\n"

    out_lines = []
    for li, line in enumerate(lines):
        if li == 1:
            out_lines.append(str(norays))
        elif line_hist[li]:
            pass  # strip positive histogram card lines
        else:
            out_lines.append(line)
        if li in inserts:
            out_lines.append(inserts[li].rstrip("\n"))
    open(out, "wb").write("\n".join(out_lines).encode("latin-1"))

    print(f"zmax={zmax:.3f} cm  POIs={len(poi)}")
    for za, li in poi:
        print(f"  z={za:9.3f} cm after line {li}")
    cells = len(poi) * 2 * ((NBIN + 1) * (NBIN + 1) + 5)
    print(f"MTABLE cells used: {cells} / 10000")


if __name__ == "__main__":
    main(*sys.argv[1:])
