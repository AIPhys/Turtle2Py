"""Quantify the ladder: spectral amplitude of dot coordinates at the coarse
19-bin cell frequency.  Bins dots into 190 fine bins, detrends, FFTs, and
reports the amplitude at 19 cycles/axis (the ladder frequency) relative to
the mean amplitude over all frequencies.  ~1.0 = no ladder.
"""

import os
import sys

import numpy as np
from playwright.sync_api import sync_playwright

html = os.path.abspath(sys.argv[1])
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path=EDGE,
        args=[
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--disable-gpu-sandbox",
            "--no-sandbox",
        ],
    )
    pg = b.new_page(viewport={"width": 1650, "height": 1500}, device_scale_factor=1)
    pg.goto("file:///" + html.replace("\\", "/"))
    pg.wait_for_timeout(5000)
    info = pg.evaluate("""() => {
      const gd = document.querySelector('.js-plotly-plot');
      const out = [];
      gd.data.forEach((t,i) => {
        if (t.type === 'scatter' && t.mode === 'markers' && i >= 18) {
          const fd = gd._fullData[i];
          out.push({i, x: Array.from(fd.x), y: Array.from(fd.y)});
        }
      });
      return out;
    }""")
    b.close()

NB = 190
for t in info:
    for ax in ("x", "y"):
        v = np.array(t[ax], dtype=float)
        if len(v) < 10:
            continue
        lo, hi = v.min(), v.max()
        h, _ = np.histogram(v, bins=NB, range=(lo, hi))
        h = h.astype(float)
        h -= h.mean()
        F = np.abs(np.fft.rfft(h))
        k = 19  # coarse cell frequency
        ratio = F[k] / (F[1:].mean() + 1e-12)
        print(
            f"trace {t['i']} {ax}: ladder amp @{k} bins = {F[k]:.1f} "
            f"vs mean {F[1:].mean():.1f}  ratio={ratio:.2f}"
        )
