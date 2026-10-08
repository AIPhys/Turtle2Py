"""Element model: parse an input deck into a flat, z-annotated element list.

Reuses the port's CardReader / ElementReader (turtle2py.io) so the card
grammar, labels and NU word counts are the same ones the reference uses,
but produces plain Python records for drawing.  No x87, no tracking.

Units (as in the deck): lengths and x,y in cm; x',y' in mr; dp/p in PC;
z reported in cm (the reference APLIM prints the same numbers labelled M).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..io import CardReader, ElementReader
from ..random import G900
from ..state import Context
from .. import elements as el

UNIT = [0.01, 0.001, 0.01, 0.001, 0.01, 0.01, 0.01745329, 1.0, 1.0, 1.0, 1.0]
NAME = ["CM", "MR", "CM", "MR", "CM", "PC", "DEG", "M", "KG", "GEVA", "GEVC"]

# APLIM (turtle.f:116-166) dispatch: which types advance z, which are apertures
DISP = {3: 50, 4: 30, 5: 30, 6: 30, 9: 60, 11: 50, 18: 50, 19: 50}

TYPE_NAME = {
    1: "BEAM",
    2: "FACE",
    3: "DRIFT",
    4: "BEND",
    5: "QUAD",
    6: "SLIT",
    7: "SHIFT",
    8: "MISALIGN",
    9: "REPEAT",
    10: "CONSTRAINT",
    11: "ACCEL",
    12: "ELLIPSE",
    13: "CAP",
    14: "MATRIX",
    15: "UNITS",
    16: "PARAMS",
    17: "SEC",
    18: "SEXT",
    19: "SOLO",
    20: "ROTATE",
    21: "FOIL",
}

SUBTYPE_NAME = {
    4: "bend aperture x",
    5: "bend aperture y",
    6: "BDB",
    7: "LAYL",
    8: "LAYX",
    9: "ZMAX",
    11: "reference momentum P0",
    12: "RAB1",
    13: "RAB2",
    100: "elliptic quad aperture",
    101: "hyperbolic quad aperture",
}


@dataclass
class Element:
    index: int  # word index into IDATA/DATA (1-based)
    nword: int
    typ: int  # |TYPE|
    name: str  # BEAM / DRIFT / BEND ...
    label: str
    z0: float  # cm, entrance
    z1: float  # cm, exit
    length: float  # cm
    datum: list = field(default_factory=list)
    info: dict = field(default_factory=dict)
    text: str = ""

    @property
    def is_aperture(self) -> bool:
        return self.typ in (4, 5, 6)


def _nu_shim(ctx: Context, i: int, typ: int) -> int:
    ctx.i = i
    return el.nu(ctx, typ)


def parse_deck(path: str):
    """Return (elements, meta) for an input deck."""
    lines = open(path, "rb").read().decode("latin-1").split("\n")
    reader = CardReader(lines)
    er = ElementReader(reader)
    ctx = Context()
    ctx.rng = G900()

    from ..fields import initze, setup, Out

    out = Out()
    initze(ctx)
    setup(ctx, reader, er, out)

    meta = {
        "norays": int(ctx.norays),
        "pbeam": float(ctx.pbeam),
        "p0": float(ctx.p0),
        "raymax": [float(v) for v in ctx.raymax[1:7]],
        "nhists": int(ctx.nhists),
        "dkflag": bool(ctx.dkflag),
        "sec": bool(ctx.sec),
        "unit": list(UNIT),
        "name": list(NAME),
        "comment": lines[0].strip() if lines else "",
    }

    # Re-read the deck card by card to recover labels (SETUP discards them).
    reader2 = CardReader(lines)
    er2 = ElementReader(reader2)
    er2.sntnl = False
    ctx2 = Context()
    ctx2.rng = G900()
    initze(ctx2)
    # SETUP state that NU depends on
    ctx2.sec = ctx.sec
    # Advance past the header (title + ray count) exactly as SETUP label 10 does.
    reader2.rdnext(2)
    reader2.rdskip()
    reader2.rdstrg(20)
    reader2.rdskip()
    reader2.rdfix()
    reader2.rdnext(-1)

    elements: list[Element] = []
    zc = 0.0  # cm
    i = 1
    ap_index = 0
    beam = None
    while True:
        nword, flush = er2.rdelmt()
        nword = er2.e.nword
        if nword == 0:
            break
        if flush:
            continue
        e = er2.e
        typ = e.ntype
        if float(e.datum[0]) < 0.0:
            continue  # SETUP ignores negative cards
        if typ == 0:
            i += 1
            continue
        datum = [float(v) for v in e.datum[: max(nword, 1)]]
        label = e.label.strip()
        tgt = DISP.get(typ, 90) if 1 <= typ <= 21 else 90
        z0 = zc
        length = 0.0
        # APLIM (turtle.f:116-166): label 30 falls through to 50, so types
        # 3,4,5,11,18,19 all advance ZC by DATA(I+1); slit (6) does not.
        if tgt in (30, 50) and typ != 6:
            length = float(e.datum[1])
            zc += length
        info: dict = {}
        text = ""
        if typ == 1:
            beam = e
            info["raymax"] = [float(e.datum[j]) for j in range(1, 7)]
            info["pbeam"] = float(e.datum[7])
            text = "source beam definition (emittance + momentum spread)"
        elif typ == 3:
            text = "drift space"
        elif typ == 4:
            ap_index += 1
            h = float(e.datum[2])
            n = float(e.datum[3])
            info["H_card"] = h
            info["N"] = n
            info["rho0"] = float(e.datum[4])
            info["aperture_x"] = float(ctx.apb[1])
            info["aperture_y"] = float(ctx.apb[2])
            text = "sector/rectangular bending magnet"
        elif typ == 5:
            ap_index += 1
            g = float(e.datum[2])
            r = float(e.datum[3])
            info["G_card"] = g
            info["R"] = r
            info["gradient_kg_m"] = g / (r * UNIT[0] * 33.356) if r else 0.0
            text = "quadrupole magnet"
        elif typ == 6:
            ap_index += 1
            info["iff"] = int(e.datum[1]) % 100
            info["ifg"] = int(e.datum[3])
            info["lo"] = float(e.datum[2])
            info["hi"] = float(e.datum[4])
            text = "slit / collimator"
        elif typ == 7:
            text = "coordinate shift"
        elif typ == 2:
            text = "pole-face rotation"
        elif typ == 13:
            text = "aperture capture switch (13 10 -> apertures active)"
        elif typ == 16:
            nm = int(e.datum[1])
            info["subtype"] = nm
            info["value"] = float(e.datum[2])
            text = "parameter card: " + SUBTYPE_NAME.get(abs(nm), str(nm))
            if abs(nm) in (4, 5):
                ctx.apb[abs(nm) - 3] = float(e.datum[2])
        elif typ >= 50:
            text = "histogram card"
            info["ncoor"] = int(e.datum[1])
            info["begin"] = float(e.datum[2])
            info["end"] = float(e.datum[3])
            info["step"] = float(e.datum[4])
        rec = Element(
            index=i,
            nword=nword,
            typ=typ,
            name=TYPE_NAME.get(typ, str(typ)),
            label=label,
            z0=z0,
            z1=zc,
            length=length,
            datum=datum,
            info=info,
            text=text,
        )
        elements.append(rec)
        i += _nu_shim(ctx2, i, typ)
        if i > ctx.i1:
            break
    meta["zmax"] = zc
    meta["napertures"] = ap_index
    return elements, meta


def element_table(elements: list[Element]) -> list[dict]:
    """Flat dict rows for the viewer table / element description panel."""
    rows = []
    for e in elements:
        d = {
            "i": e.index,
            "type": e.typ,
            "name": e.name,
            "label": e.label,
            "z0": round(e.z0, 4),
            "z1": round(e.z1, 4),
            "length": round(e.length, 4),
            "text": e.text,
        }
        for k, v in e.info.items():
            d[k] = round(v, 6) if isinstance(v, float) else v
        rows.append(d)
    return rows
