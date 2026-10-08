"""Compare the reader's PRINT1 stream (turtle2py) with the element listing
records in test_ref.res, record by record."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from turtle2py.io import CardReader, ElementReader, unpack

ROOT = Path(__file__).resolve().parents[1]
ref = (ROOT / "test_ref.res").read_bytes().split(b"\r\n")
pat = re.compile(rb"^0 *(-?\d+)\.([^;]*);")
ref_els = [r for r in ref if pat.match(r)]

lines = (ROOT / "turtle_in.dat").read_bytes().decode("latin-1").split("\n")
r = CardReader(lines)
r.rdnext(2)
r.rdskip()
words, l = r.rdstrg(20)
r.rdfix()
r.rdnext(-1)
er = ElementReader(r)
ours = []
while True:
    nword, flush = er.rdelmt()
    if nword == 0:
        break
    for m in er.msg:
        ours.extend(m.split(b"\r\n")[:-1])
    er.msg = []
ours = [r for r in ours if pat.match(r)]

print("ref element records:", len(ref_els))
print("py  element records:", len(ours))
bad = 0
for i, (a, b) in enumerate(zip(ref_els, ours)):
    if a != b:
        bad += 1
        if bad <= 5:
            print("MISMATCH", i)
            print(" ref", a)
            print(" py ", b)
print("mismatches:", bad)
sys.exit(1 if (bad or len(ref_els) != len(ours)) else 0)
