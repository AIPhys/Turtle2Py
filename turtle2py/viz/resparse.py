"""Parse Turtle .res 2-D histogram blocks (OUTMAT, turtle.f:871).

Fixed-column layout (all FORMAT strings are fixed width):
  axis rule  FORMAT(1H ,20X,'I*',110A1)  -> prefix 23, content NA+10
  body row   FORMAT(1H ,F8.3,' TO',F8.3,' I ',110A1) -> prefix 23,
             grid chars at 23..23+NA-1, row total (4 DIGITAL digits) at
             23+NA+5 .. 23+NA+8
  col sums   FORMAT(1H ,20X,'I ',110A1)  -> digits at 23..23+NA-1
  TOTALS     FORMAT(1H ,12X,'TOTALS',2X,'I ',110A1) -> digits at 23..,
             grand total at 23+NA+5..+8
Grid cells encoded by BCDWR (turtle.f:1675): 0 -> ' ', 1..35 -> TABLE[n],
>35 -> '*'.  DIGITAL blanks leading zeros.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TABLE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CODE = {c: i for i, c in enumerate(TABLE)}
CODE["*"] = 36
CODE["&"] = 36  # BCDWR saturation: SEMI(4) = '&' (turtle.f:1690, BLOC42)
CODE[" "] = 0

AXIS_RE = re.compile(
    r"^\s*(HORIZONTAL|VERTICAL) AXIS\s+(\S+)\s+IN\s+(\S+)\s+([\d.]+) M\s+FROM THE TARGET"
    r"(?:, FLAG AT\s+([\d.]+) M)?\s*$"
)
ROW_RE = re.compile(r"^\s*(-?[\d.]+)\s+TO\s+(-?[\d.]+)\s+I\s")
NUM_RE = re.compile(r"-?\d+\.\d+")


@dataclass
class PhaseHist:
    z_m: float
    hname: str
    hunit: str
    vname: str
    vunit: str
    xmin: float
    xmax: float
    nx: int
    ymin: float
    ymax: float
    ny: int
    grid: list = field(default_factory=list)  # grid[iy][ix], iy=0 lowest y
    row_tot: list = field(default_factory=list)
    col_tot: list = field(default_factory=list)
    grand: int = 0
    total: int = 0
    across: tuple = (0, 0)
    down: tuple = (0, 0)
    center_x: float = 0.0
    rms_x: float = 0.0
    center_y: float = 0.0
    rms_y: float = 0.0
    corr: float = 0.0


def _digits4(s: str) -> int:
    return int("".join(c if c in TABLE else "0" for c in s[-4:]))


def reconstruct_grid(h: PhaseHist) -> list:
    """Estimate cell counts from the saturated grid + exact row totals.

    BCDWR caps printed cells at 36, so the printed grid underestimates dense
    cells; Turtle's printed column sums are DIGITAL-capped (sum ~ grand/10)
    and cannot be used as a marginal.  Row totals are exact, so each row is
    scaled to its exact total, keeping the printed within-row shape (blank
    cells are truly zero).  Returns grid[iy][ix] as floats.
    """
    g = [[float(c) for c in row] for row in h.grid]
    rt = [float(v) for v in h.row_tot]
    out = []
    for iy, row in enumerate(g):
        s = sum(row)
        t = rt[iy] if iy < len(rt) else 0.0
        if s > 0 and t > 0:
            f = t / s
            out.append([c * f for c in row])
        else:
            out.append(row)
    return out


def parse_res(path: str) -> list[PhaseHist]:
    lines = [
        ln.rstrip("\r") for ln in open(path, "rb").read().decode("latin-1").split("\n")
    ]
    # Fortran carriage control: leading '0'/'1' on print lines
    lines = [ln[1:] if ln[:1] in "01" else ln for ln in lines]
    out: list[PhaseHist] = []
    i = 0
    n = len(lines)
    while i < n:
        if not re.match(r"^[01]?\s*HISTOGRAM NO", lines[i]):
            i += 1
            continue
        caps = {}
        j = i + 1
        while j < min(i + 6, n):
            m = AXIS_RE.match(lines[j])
            if m:
                caps[m.group(1)] = (m, j)
            j += 1
        if "HORIZONTAL" not in caps or "VERTICAL" not in caps:
            i += 1
            continue
        z_m = float(caps["HORIZONTAL"][0].group(4))
        j = caps["VERTICAL"][1] + 1

        # A real body starts with a blank line, then the X label line
        # FORMAT(1H0/16X,11F10.3) -> at least two numbers.  Caption-only
        # headers (HEDING) are followed directly by the next header.
        if lines[j].strip():
            i = j
            continue
        labels = [float(x) for x in NUM_RE.findall(lines[j + 1])]
        if len(labels) < 2:
            i = j
            continue
        k = j + 2

        # axis rule line: FORMAT(1H ,20X,'I*',110A1) -> 'I' at col 21, then
        # NA+10 chars ending in the closing 'I'.  Derive NA from the closing I.
        na = None
        while k < n:
            ln = lines[k]
            p = ln.find("I*")
            if p != -1:
                q = ln.find("I", p + 2)
                if q != -1:
                    na = q - (p + 2) - 1
                    k += 1
                    break
            k += 1
        if not na or na <= 0:
            i = j
            continue
        base = p  # column of 'I' in the rule line == body 'I' column

        rows = []
        g0 = base + 2  # grid chars start (after 'I ')
        t0 = g0 + na + 5  # 4-digit row total (after blank + 'I')
        while k < n:
            m = ROW_RE.match(lines[k])
            if not m:
                break
            ln = lines[k]
            grid = ln[g0 : g0 + na]
            tot = _digits4(ln[t0 : t0 + 4])
            rows.append((float(m.group(1)), float(m.group(2)), grid, tot))
            k += 1
        if not rows:
            i = j
            continue
        ny = len(rows)
        grid = [[CODE.get(c, 0) for c in r[2]] for r in rows]
        row_tot = [r[3] for r in rows]

        colrows = []
        grand = 0
        while k < n:
            ln = lines[k]
            p = ln.find("I ")
            # TOTALS grand line: 'I ' sits one column right of the rule line
            # (FORMAT 13X,'TOTALS',2X,'I ' vs 21X,'I*'), so accept p >= base.
            if "TOTALS" in ln and p >= base:
                grand = _digits4(ln[p + 2 + na + 5 : p + 2 + na + 9])
                k += 1
                break
            if p == base:
                seg = ln[g0 : g0 + na]
                if all(c in TABLE or c == " " for c in seg):
                    colrows.append(seg)
            k += 1
        # 4 DIGITAL rows (thousands..units); leading-zero rows are blank.
        col_tot = [0] * na
        for row in colrows[:4]:
            for ix, c in enumerate(row):
                col_tot[ix] = col_tot[ix] * 10 + (CODE[c] if c in TABLE else 0)

        total = 0
        across = down = (0, 0)
        while k < n:
            mm = re.search(r"TOTAL NUMBER OF ENTRIES =\s*(\d+)", lines[k])
            if mm:
                total = int(mm.group(1))
                ac = re.search(r"ACROSS\s+(\d+)\s+(\d+)", lines[k + 2])
                dn = re.search(r"DOWN\s+(\d+)\s+(\d+)", lines[k + 3])
                if ac:
                    across = (int(ac.group(1)), int(ac.group(2)))
                if dn:
                    down = (int(dn.group(1)), int(dn.group(2)))
                k += 4
                break
            k += 1
        stats = []
        seen_corr = False
        while k < n and not seen_corr:
            if re.match(r"^\s*HISTOGRAM NO", lines[k]):
                break
            mm = re.search(
                r"CENTER =\s*(-?[\d.]+)\s+RMS HALF WIDTH =\s*(-?[\d.]+)", lines[k]
            )
            if mm:
                stats.append((float(mm.group(1)), float(mm.group(2))))
            mm = re.search(r"CORRELATION =\s*(-?nan|-?[\d.]+)", lines[k], re.I)
            if mm:
                stats.append((float(mm.group(1)), 0.0))
                seen_corr = True
            k += 1
        cx = rx = cy = ry = corr = 0.0
        if len(stats) >= 3:
            cx, rx = stats[0]
            cy, ry = stats[1]
            corr = stats[2][0]

        da = (labels[1] - labels[0]) / 10.0 if len(labels) > 1 else 0.0
        xmin = labels[0]
        out.append(
            PhaseHist(
                z_m=z_m,
                hname=caps["HORIZONTAL"][0].group(2),
                hunit=caps["HORIZONTAL"][0].group(3),
                vname=caps["VERTICAL"][0].group(2),
                vunit=caps["VERTICAL"][0].group(3),
                xmin=xmin,
                xmax=xmin + na * da,
                nx=na,
                ymin=rows[0][0],
                ymax=rows[-1][1],
                ny=ny,
                grid=grid,
                row_tot=row_tot,
                col_tot=col_tot,
                grand=grand,
                total=total,
                across=across,
                down=down,
                center_x=cx,
                rms_x=rx,
                center_y=cy,
                rms_y=ry,
                corr=corr,
            )
        )
        i = k
    return out
