import json, base64, re, sys
import numpy as np

html = open("viz.html", encoding="utf8").read()
i = html.find("Plotly.newPlot")
i = html.index("[", i)
dec = json.JSONDecoder()
data, end = dec.raw_decode(html, i)
j = html.index("{", end)
layout, _ = dec.raw_decode(html, j)


def dec_arr(t):
    if isinstance(t, dict) and "bdata" in t:
        dtype = np.dtype(t["dtype"])
        return np.frombuffer(base64.b64decode(t["bdata"]), dtype=dtype)
    return np.asarray(t, dtype=float)


dd = [u for u in layout.get("updatemenus", []) if u.get("type") == "dropdown"][0]
print("buttons:", len(dd["buttons"]))
print("initial ranges:")
for ax in ["xaxis7", "yaxis7", "xaxis8", "yaxis8", "xaxis9", "yaxis9"]:
    print("  ", ax, layout[ax].get("range"))

print(
    "\nper-button containment (all data inside range; fill = data span / range span):"
)
worst = []
for b in dd["buttons"]:
    args, largs = b["args"]
    lab = b["label"]
    out = []
    for ax, ay in [("xaxis7", "yaxis7"), ("xaxis8", "yaxis8"), ("xaxis9", "yaxis9")]:
        tax, tay = ax.replace("xaxis", "x"), ay.replace("yaxis", "y")
        inside = True
        span_d = 0.0
        for k, tr in enumerate(data):
            if tr.get("xaxis", "x") == tax and tr.get("yaxis", "y") == tay:
                xa = args.get(f"trace{k}.x", tr.get("x"))
                ya = args.get(f"trace{k}.y", tr.get("y"))
                x = dec_arr(xa)
                y = dec_arr(ya)
                if len(x) == 0:
                    continue
                rx = largs.get(f"{ax}.range")
                ry = largs.get(f"{ay}.range")
                outp = (
                    (x.min() < rx[0])
                    or (x.max() > rx[1])
                    or (y.min() < ry[0])
                    or (y.max() > ry[1])
                )
                inside = inside and not outp
                span_d = max(
                    span_d,
                    (x.max() - x.min()) / (rx[1] - rx[0]),
                    (y.max() - y.min()) / (ry[1] - ry[0]),
                )
        out.append((ax, inside, round(span_d, 3)))
    bad = [o for o in out if not o[1]]
    fills = [o[2] for o in out]
    print(
        f"  {lab:14s} fills={fills}  {'OUTSIDE:' + str(bad) if bad else 'all inside'}"
    )
    worst.append(min(fills))
print("\nmin fill ratio across buttons:", min(worst))
