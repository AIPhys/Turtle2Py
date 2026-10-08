import base64, json, re, sys, collections
from playwright.sync_api import sync_playwright

HTML = sys.argv[1] if len(sys.argv) > 1 else "viz.html"
TARGETS = sys.argv[2:] or ["z = 97.47 m", "z = 24.18 m", "z = 12.50 m", "z = 0.00 m"]
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

PANELS = {"x-x'": "xaxis7", "y-y'": "xaxis8", "x-y": "xaxis9"}


def ink_stats(png_bytes, rect):
    # decode PNG via PIL
    import io
    from PIL import Image

    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    x0, y0, x1, y1 = [int(v) for v in rect]
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, im.width), min(y1, im.height)
    crop = im.crop((x0, y0, x1, y1))
    W, H = crop.size
    px = crop.load()
    rows = [0] * H
    cols = [0] * W
    total = 0
    for yy in range(H):
        for xx in range(W):
            r, g, b = px[xx, yy]
            # ink = saturated color (not white/gray gridlines/axis)
            mx, mn = max(r, g, b), min(r, g, b)
            if mx < 235 and (mx - mn) > 25:
                rows[yy] += 1
                cols[xx] += 1
                total += 1
    rrows = sum(1 for v in rows if v > 0)
    rcols = sum(1 for v in cols if v > 0)
    rr = [i for i, v in enumerate(rows) if v > 0]
    cc = [i for i, v in enumerate(cols) if v > 0]
    rb = (rr[0] / H, rr[-1] / H) if rr else (0, 0)
    cb = (cc[0] / W, cc[-1] / W) if cc else (0, 0)
    return dict(
        total=total,
        row_frac=rrows / H,
        col_frac=rcols / W,
        row_bbox=(round(rb[0], 3), round(rb[1], 3)),
        col_bbox=(round(cb[0], 3), round(cb[1], 3)),
    )


with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path=EDGE,
        args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"],
    )
    pg = b.new_page(viewport=dict(width=1650, height=1500))
    import os

    pg.goto("file:///" + os.path.abspath(HTML).replace("\\", "/"))
    pg.wait_for_selector(".js-plotly-plot", timeout=30000)
    pg.wait_for_timeout(2500)

    geo = pg.evaluate("""() => {
        const gd = document.querySelector('.js-plotly-plot');
        const r = gd.getBoundingClientRect();
        const L = gd._fullLayout;
        const S = L._size;
        const out = {rect: {x:r.x, y:r.y, w:r.width, h:r.height},
                     size: {w: S.w, h: S.h, l: S.l, t: S.t},
                     dom: {}};
        for (const k of ['xaxis7','xaxis8','xaxis9'])
            out.dom[k] = L[k].domain;
        return out;
    }""")
    print("geo:", json.dumps(geo))

    def panel_rect(ax):
        d = geo["dom"][ax]
        s = geo["size"]
        left = geo["rect"]["x"] + s["l"]
        top = geo["rect"]["y"] + s["t"]
        w, h = s["w"], s["h"]
        return [
            left + d[0] * w,
            top + (1 - d[1]) * h,
            left + d[1] * w,
            top + (1 - d[0]) * h,
        ]

    # open dropdown
    hdr = pg.locator("text=/z = .* m/").first
    hdr.click()
    pg.wait_for_timeout(600)

    for label in TARGETS:
        opt = pg.locator(f"text='{label}'").last
        bb = opt.bounding_box()
        if not bb:
            print(label, "NOT FOUND")
            continue
        pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        pg.wait_for_timeout(1200)
        state = pg.evaluate("""() => {
            const gd = document.querySelector('.js-plotly-plot');
            const L = gd._fullLayout;
            const hdr = [...document.querySelectorAll('.u-inlay text')].map(t=>t.textContent).filter(s=>s.includes('z ='));
            return {hdr, r7: L.xaxis7.range, r8: L.xaxis8.range, r9: L.xaxis9.range,
                    ry7: L.yaxis7.range, ry8: L.yaxis8.range, ry9: L.yaxis9.range};
        }""")
        print(label, "STATE", json.dumps(state))
        shot = pg.screenshot(full_page=True)
        res = {}
        for name, ax in PANELS.items():
            res[name] = ink_stats(shot, panel_rect(ax))
        print(label, json.dumps(res))
        with open(
            f"probe/fit_{label.split('=')[1].strip().replace(' ', 'p').replace('.', 'p')}.png",
            "wb",
        ) as f:
            f.write(shot)
        # reopen dropdown for next pick
        pg.locator("text=/z = .* m/").first.click()
        pg.wait_for_timeout(500)

    b.close()
