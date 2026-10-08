"""Click each camera button and capture the 3-D scene region; prove it moves."""

import os, sys, numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

html = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "viz.html")
url = "file:///" + html.replace("\\", "/")

with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"],
    )
    pg = b.new_page(viewport={"width": 1650, "height": 1500}, device_scale_factor=1)
    pg.goto(url)
    pg.wait_for_timeout(4500)
    # scene region in px: plotly y domain [0.825,1.0] is the TOP of the page
    W, H = 1658, 1508
    box = dict(x=0, y=int(0.0 * H), width=int(0.637 * W), height=int(0.175 * H))
    shots = {}
    for label in ["iso", "top", "side", "front"]:
        sel = f"text.updatemenu-item-text:has-text('{label}')"
        btn = pg.query_selector(sel)
        if btn is None:
            print(label, "BUTTON NOT FOUND")
            continue
        btn.click(force=True)
        pg.wait_for_timeout(1200)
        path = f"probe/cam_{label}.png"
        pg.screenshot(path=path, clip=box)
        shots[label] = np.asarray(Image.open(path).convert("L"), dtype=float)
    b.close()

labels = list(shots)
for i, a in enumerate(labels):
    for c in labels[i + 1 :]:
        d = np.abs(shots[a] - shots[c]).mean()
        print(f"{a} vs {c}: mean abs diff {d:.2f}")
