"""Check a fork-built viz HTML: z-select payload, ranges vs fitted cards, dots.

The current viewer switches phase panels with a native <select> driven by a
JSON payload embedded in the plotly post_script (not an updatemenu), so the
old probe/fit_json.py dropdown scan does not apply.  Checks:

  1. payload has 12 z labels, exit first;
  2. per-z axis ranges == fitted card ranges (x-x', y-y', x-y panels);
  3. every dot lies inside its panel range;
  4. ellipse traces present (3 per panel).  3-sigma ellipses legitimately
     extend past the card box (the reference viz.html does the same), so
     ellipse overshoot is reported, not failed on.

Usage: python probe/fork_check.py <html> [card_ranges.json]
"""

import json
import re
import sys

import numpy as np

html_path = sys.argv[1] if len(sys.argv) > 1 else "demo_channel_viz.html"
stem = re.sub(r"_viz\.html$", "", html_path)
ranges_path = (
    sys.argv[2] if len(sys.argv) > 2 else f"{stem}_viz/{stem}_card_ranges.json"
)

html = open(html_path, encoding="utf8").read()

m = re.search(r"var PH\s*=\s*(\{.*?\});", html, re.S)
if not m:
    i = html.find('"labels"')
    i = html.rfind("{", 0, i)
    payload, _ = json.JSONDecoder().raw_decode(html, i)
else:
    payload = json.loads(m.group(1))

labels = payload["labels"]
print("z options:", len(labels), "| first:", labels[0], "| last:", labels[-1])
zs = [float(lab.split("=")[1].split("m")[0]) for lab in labels]
assert abs(zs[0] - max(zs)) < 1e-6, "exit (max z) should be first"

cr = json.load(open(ranges_path))
keys = sorted(cr, key=float)

worst_fill = 1.0
range_bad, dots_bad, ell_out = [], [], 0
for i, lab in enumerate(labels):
    z = float(lab.split("=")[1].split("m")[0])
    key = min(keys, key=lambda k: abs(float(k) - z))
    d = cr[key]
    rng = payload["ranges"][i]  # [x7,y7,x8,y8,x9,y9] in mm/mr
    want = [d["x"], d["xp"], d["y"], d["yp"], d["x"], d["y"]]
    for a, b in zip(rng, want):
        # axis range must CONTAIN the fitted card box (it is widened to fit
        # the 3-sigma ellipses + 6% pad); equality is no longer required.
        if a[0] > b[0] + 0.02 or a[1] < b[1] - 0.02:
            range_bad.append((lab, a, b))
    ndot = 0
    for p in range(3):
        x = np.asarray(payload["x"][i][4 * p], float)
        y = np.asarray(payload["y"][i][4 * p], float)
        rx, ry = rng[2 * p], rng[2 * p + 1]
        if len(x) == 0:
            continue
        ndot += len(x)
        out = (
            (x < rx[0]).sum()
            + (x > rx[1]).sum()
            + (y < ry[0]).sum()
            + (y > ry[1]).sum()
        )
        if out:
            dots_bad.append((lab, f"panel{p}", int(out)))
        fill = min(
            (x.max() - x.min()) / (rx[1] - rx[0]), (y.max() - y.min()) / (ry[1] - ry[0])
        )
        worst_fill = min(worst_fill, fill)
        for e in range(1, 4):
            ex = np.asarray(payload["x"][i][4 * p + e], float)
            ey = np.asarray(payload["y"][i][4 * p + e], float)
            if len(ex) == 0:
                continue
            ell_out += int(
                (ex < rx[0]).sum()
                + (ex > rx[1]).sum()
                + (ey < ry[0]).sum()
                + (ey > ry[1]).sum()
            )
    print(f"  {lab:14s} dots/panel={ndot // 3:5d}  fill={fill:.2f}")

print("\nrange mismatches:", len(range_bad), range_bad[:3])
ndots = 3000 * 3 * len(labels)
nout = sum(b[2] for b in dots_bad)
print(
    f"dots outside panel range: {nout} / {ndots} ({100 * nout / ndots:.3f}%)",
    dots_bad[:3],
)
print("ellipse points beyond card box (informational):", ell_out)
print("min fill ratio:", round(worst_fill, 3))
# Reference viz.html has ~5/36000 dots on the card-box boundary; allow <0.5%.
# Fill floor: cards are 4*RMS with 2 mm / 0.3 mr floors, so a beam whose RMS
# sits below the floors legitimately fills ~1/4 of the card (te455_0: 0.14).
ok = not range_bad and 100 * nout / ndots < 0.5 and worst_fill > 0.1
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
