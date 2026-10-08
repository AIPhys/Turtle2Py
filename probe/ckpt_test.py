"""Verify checkpoint/resume: run small case with ckpt every 10 rays,
resume from ckpt, compare to small_ref.res."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CK = str(ROOT / "ckpt_test.ckpt")
os.environ["T2P_CKPT"] = CK
os.environ["T2P_CKPT_EVERY"] = "10"
from turtle2py import fields, report
from turtle2py.io import CardReader, ElementReader
from turtle2py.random import G900
from turtle2py.state import Context
from turtle2py import tracking

def run(outp, resume):
    lines = (ROOT / "turtle_small.dat").read_bytes().decode("latin-1").split("\n")
    reader = CardReader(lines); er = ElementReader(reader)
    out = fields.Out(); ctx = Context(); ctx.rng = G900()
    fields.initze(ctx); fields.setup(ctx, reader, er, out)
    report.heding(ctx, out); fields.zero(ctx)
    nct0 = 0
    if resume:
        nct0, ctx, obuf = tracking.load_ckpt(CK)
        ctx.norays = 100  # half-run saved norays=50
        if obuf is not None: out.buf = bytearray(obuf)
        print("resumed at", nct0, "obuf", len(obuf) if obuf else None)
    else:
        out.write(fields.F.render("/'0THE REST SPACE OF HIST STORAGE',I6,' CELLS'", [10000 - ctx.limno]))
    tracking.rayrun(ctx, nct0, out)
    report.ohist(ctx, out); report.aplim(ctx, out)
    out.save(outp)

if sys.argv[1] == "full":
    if os.path.exists(CK): os.remove(CK)
    run(str(ROOT / "ckpt_full.res"), False)
elif sys.argv[1] == "half":
    if os.path.exists(CK): os.remove(CK)
    # run 50 rays: monkeypatch norays
    lines = (ROOT / "turtle_small.dat").read_bytes().decode("latin-1").split("\n")
    reader = CardReader(lines); er = ElementReader(reader)
    out = fields.Out(); ctx = Context(); ctx.rng = G900()
    fields.initze(ctx); fields.setup(ctx, reader, er, out)
    report.heding(ctx, out); fields.zero(ctx)
    ctx.norays = 50
    out.write(fields.F.render("/'0THE REST SPACE OF HIST STORAGE',I6,' CELLS'", [10000 - ctx.limno]))
    tracking.rayrun(ctx, 0, out)
    print("stopped at nct=50, ckpt exists:", os.path.exists(CK))
else:
    run(str(ROOT / "ckpt_res.res"), True)
