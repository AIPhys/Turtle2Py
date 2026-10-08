"""Screenshot viz.html with Playwright + system Edge.

Usage: python shot.py [html] [png] [w] [h] [fullpage]
"""

import os
import sys
from playwright.sync_api import sync_playwright

html = sys.argv[1] if len(sys.argv) > 1 else "viz.html"
png = sys.argv[2] if len(sys.argv) > 2 else "shot.png"
w = int(sys.argv[3]) if len(sys.argv) > 3 else 1650
h = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
full = len(sys.argv) > 5 and sys.argv[5] == "full"

with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        args=[
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--disable-gpu-sandbox",
            "--no-sandbox",
        ],
    )
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    url = "file:///" + os.path.abspath(html).replace("\\", "/")
    pg.goto(url)
    pg.wait_for_timeout(4500)
    pg.screenshot(path=png, full_page=full)
    b.close()
print("wrote", png)
