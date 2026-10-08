"""Compare the SETUP block of turtle2py with test_ref.res records 1..382."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turtle2py.state import Context
from turtle2py.random import G900
from turtle2py.io import CardReader, ElementReader
from turtle2py import fields

ROOT = Path(__file__).resolve().parents[1]
ref = (ROOT / "test_ref.res").read_bytes().split(b"\r\n")

lines = (ROOT / "turtle_in.dat").read_bytes().decode("latin-1").split("\n")
reader = CardReader(lines)
er = ElementReader(reader)
out = fields.Out()
ctx = Context()
ctx.rng = G900()
fields.initze(ctx)
fields.setup(ctx, reader, er, out)
py = out.buf.split(b"\r\n")
# SETUP ends at record 382 (0SENTINEL); record 383 is the HEDING header,
# which this harness does not produce, so compare only the SETUP block.
n = min(len(ref), len(py), 382)
bad = 0
for i in range(n):
    if ref[i] != py[i]:
        bad += 1
        if bad <= 8:
            print("MISMATCH rec", i + 1)
            print(" ref", ref[i])
            print(" py ", py[i])
print("ref recs:", len(ref) - 1, " py recs:", len(py) - 1, "mismatches:", bad)
print(
    "ctx: norays",
    ctx.norays,
    "i1",
    ctx.i1,
    "nhists",
    ctx.nhists,
    "limno",
    ctx.limno,
    "loss",
    ctx.loss,
    "dkflag",
    ctx.dkflag,
)
sys.exit(1 if bad else 0)
