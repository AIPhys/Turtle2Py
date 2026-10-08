"""Resumable full 5M-ray run: turtle_in.dat -> full_py.res, diff vs test_ref.res.

T2P_CKPT=full_py.ckpt T2P_CKPT_EVERY=100000 python -u probe/full_run2.py

If full_py.ckpt exists, the run resumes from it (loop state at label 690 is
exactly (nct, ctx); zero() writes no output, so the output stream is
reproducible from setup+heding+zero+rayrun).
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("T2P_CKPT", str(ROOT / "full_py.ckpt"))
os.environ.setdefault("T2P_CKPT_EVERY", "100000")

from turtle2py import fields, report
from turtle2py.io import CardReader, ElementReader
from turtle2py.random import G900
from turtle2py.state import Context
from turtle2py.tracking import load_ckpt

outp = ROOT / "full_py.res"
lines = (ROOT / "turtle_in.dat").read_bytes().decode("latin-1").split("\n")
reader = CardReader(lines)
er = ElementReader(reader)
out = fields.Out()
ctx = Context()
ctx.rng = G900()
fields.initze(ctx)
fields.setup(ctx, reader, er, out)
report.heding(ctx, out)
fields.zero(ctx)

nct0 = 0
if os.path.exists(os.environ["T2P_CKPT"]):
    nct0, ctx, obuf = load_ckpt(os.environ["T2P_CKPT"])
    if obuf is not None:
        out.buf = bytearray(obuf)
    print("resumed at nct =", nct0, "out bytes =", len(out.buf), flush=True)
else:
    out.write(
        fields.F.render(
            "/'0THE REST SPACE OF HIST STORAGE',I6,' CELLS'", [10000 - ctx.limno]
        )
    )

t0 = time.time()
from turtle2py import tracking

tracking.rayrun(ctx, nct0, out)
report.ohist(ctx, out)
report.aplim(ctx, out)
out.save(str(outp))
print(
    "run done in %.0f s (rays %d..%d)" % (time.time() - t0, nct0, ctx.norays),
    flush=True,
)

ref = (ROOT / "test_ref.res").read_bytes().split(b"\r\n")
py = outp.read_bytes().split(b"\r\n")
n = max(len(ref), len(py))
bad = 0
first = []
for i in range(n):
    a = ref[i] if i < len(ref) else b"<missing>"
    b = py[i] if i < len(py) else b"<missing>"
    if a != b:
        bad += 1
        if len(first) < 10:
            first.append((i + 1, a, b))
print("ref recs:", len(ref) - 1, "py recs:", len(py) - 1, "mismatches:", bad)
for i, a, b in first:
    print("MISMATCH rec", i)
    print("  ref", a[:120])
    print("  py ", b[:120])
sys.exit(1 if bad else 0)
