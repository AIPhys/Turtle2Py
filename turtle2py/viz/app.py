"""Turtle2Py Viz — production GUI (no CLI needed).

    python -m turtle2py.viz.app          (or double-click viz_app.pyw)

Pick any Turtle input deck (e.g. a modified channel config), press Run:
the two-pass histogram pipeline runs and the interactive HTML opens in the
browser, with the same panels as viz.html (3-D beamline, element table,
top/side views, envelopes, rays lost, phase-space panels with the z select).

Runs in a worker thread; the log pane shows each step; Cancel stops the
Turtle run in flight.  Inputs, options and the last output are remembered in
viz_app.json beside this file.
"""

from __future__ import annotations

import json
import queue
import sys
import threading
import time
import tkinter as tk
import webbrowser
from importlib.util import find_spec as importlib_find_spec
from pathlib import Path
from tkinter import filedialog, ttk

from .fork import cancel, fork

ROOT = Path(__file__).resolve().parents[2]
CFG = Path(__file__).with_name("viz_app.json")

INK = "#1b1b1b"
MUTED = "#6a6a6a"
ACCENT = "#1f6fb5"
BG = "#fbfbfa"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.q: queue.Queue = queue.Queue()
        self.busy = False
        self.last_html: Path | None = None
        root.title("Turtle2Py Viz")
        root.geometry("900x640")
        root.minsize(760, 520)
        root.configure(bg=BG)
        self.cfg = self._load_cfg()
        self._style()
        self._build()
        root.after(80, self._pump)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------------- config
    def _load_cfg(self) -> dict:
        try:
            return json.loads(CFG.read_text(encoding="utf8"))
        except Exception:
            return {}

    def _save_cfg(self):
        try:
            CFG.write_text(
                json.dumps(
                    {
                        "input": self.var_in.get(),
                        "rays": self.var_rays.get(),
                        "seed": self.var_seed.get(),
                        "engine": self.var_engine.get(),
                        "fit": self.var_fit.get(),
                        "last_html": str(self.last_html) if self.last_html else "",
                    },
                    indent=1,
                ),
                encoding="utf8",
            )
        except Exception:
            pass

    # ---------------------------------------------------------------- style
    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=INK, font=("Segoe UI", 10))
        s.configure("Muted.TLabel", foreground=MUTED)
        s.configure("Title.TLabel", font=("Segoe UI", 15, "bold"), foreground=INK)
        s.configure("TButton", font=("Segoe UI", 10), padding=6)
        s.configure("Run.TButton", font=("Segoe UI", 11, "bold"), foreground="white")
        s.map(
            "Run.TButton",
            background=[("active", "#155a94")],
            configure=[("!disabled", {"background": ACCENT})],
        )
        s.configure("TCheckbutton", background=BG, font=("Segoe UI", 10))
        s.configure("TEntry", padding=4)
        s.configure("TNotebook.Tab", font=("Segoe UI", 10))

    # ---------------------------------------------------------------- layout
    def _build(self):
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Turtle2Py Viz", style="Title.TLabel").pack(side="left")
        ttk.Label(
            top,
            text="deck  →  Turtle histograms  →  interactive HTML",
            style="Muted.TLabel",
        ).pack(side="left", padx=12, pady=(6, 0))

        row = ttk.Frame(self.root)
        row.pack(fill="x", padx=8)
        ttk.Label(row, text="Input deck:").pack(side="left")
        self.var_in = tk.StringVar(value=self.cfg.get("input", ""))
        e = ttk.Entry(row, textvariable=self.var_in)
        e.pack(side="left", fill="x", expand=True, padx=6)
        e.bind("<KeyRelease>", lambda *_: self._sync_run())
        ttk.Button(row, text="Browse…", command=self._browse).pack(side="left")

        opt = ttk.Frame(self.root)
        opt.pack(fill="x", padx=8, pady=(6, 0))
        self.var_rays = tk.StringVar(value=str(self.cfg.get("rays", "20000")))
        self.var_seed = tk.StringVar(value=str(self.cfg.get("seed", "12345")))
        self.var_engine = tk.StringVar(value=self.cfg.get("engine", "auto"))
        self.var_fit = tk.BooleanVar(value=bool(self.cfg.get("fit", True)))
        for lab, var, w in (("rays", self.var_rays, 8), ("seed", self.var_seed, 8)):
            ttk.Label(opt, text=lab).pack(side="left")
            ttk.Entry(opt, textvariable=var, width=w).pack(side="left", padx=(3, 12))
        ttk.Label(opt, text="engine").pack(side="left")
        ttk.Combobox(
            opt,
            textvariable=self.var_engine,
            width=6,
            state="readonly",
            values=["auto", "exe", "py"],
        ).pack(side="left", padx=(3, 12))
        ttk.Checkbutton(
            opt,
            text="fit card ranges to the beam (2 passes)",
            variable=self.var_fit,
        ).pack(side="left")

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=8, pady=(8, 4))
        self.b_run = ttk.Button(
            btns, text="Run", style="Run.TButton", command=self._run
        )
        self.b_run.pack(side="left")
        self.b_cancel = ttk.Button(
            btns, text="Cancel", command=self._cancel, state=["disabled"]
        )
        self.b_cancel.pack(side="left", padx=6)
        self.b_open = ttk.Button(
            btns, text="Open result", command=self._open, state=["disabled"]
        )
        self.b_open.pack(side="left")
        self.b_dir = ttk.Button(btns, text="Open folder", command=self._open_dir)
        self.b_dir.pack(side="left", padx=6)
        self.var_status = tk.StringVar(value="ready")
        ttk.Label(btns, textvariable=self.var_status, style="Muted.TLabel").pack(
            side="right"
        )

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        logtab = ttk.Frame(self.nb)
        self.nb.add(logtab, text="  log  ")
        bar = ttk.Scrollbar(logtab)
        self.log = tk.Text(
            logtab,
            wrap="word",
            bg="#15171a",
            fg="#dfe6ee",
            insertbackground="#dfe6ee",
            font=("Consolas", 10),
            relief="flat",
            state="disabled",
            height=24,
            yscrollcommand=bar.set,
        )
        bar.configure(command=self.log.yview)
        self.log.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.log.tag_config("ok", foreground="#7fd18a")
        self.log.tag_config("warn", foreground="#e8c37a")
        self.log.tag_config("dim", foreground="#8b97a5")

        self.pane = ttk.Frame(self.nb)
        self.nb.add(self.pane, text="  preview  ")
        self.var_prev = tk.StringVar(
            value="run the pipeline to see the beam summary here"
        )
        ttk.Label(self.pane, textvariable=self.var_prev, justify="left").pack(
            anchor="nw", padx=12, pady=10
        )
        self._sync_run()
        self._check_deps()

    # ---------------------------------------------------------------- actions
    def _check_deps(self):
        """Name the interpreter and flag a missing viewer dependency up front."""
        import sys

        missing = [m for m in ("numpy", "plotly") if importlib_find_spec(m) is None]
        if missing:
            self._log(
                f"this Python ({sys.executable}) has no {', '.join(missing)} — "
                "the run will fail at the visualisation step.  Install it "
                f'(`"{sys.executable}" -m pip install {" ".join(missing)}`) '
                "or launch via viz_app.bat, which picks a Python that has them.",
                "warn",
            )

    def _browse(self):
        p = filedialog.askopenfilename(
            title="Turtle input deck",
            initialdir=Path(self.var_in.get()).parent if self.var_in.get() else ROOT,
            filetypes=[("Turtle decks", "*.dat"), ("all files", "*.*")],
        )
        if p:
            self.var_in.set(str(Path(p).resolve()))
            self._sync_run()

    def _sync_run(self):
        ok = (
            bool(self.var_in.get().strip())
            and Path(self.var_in.get().strip()).is_file()
        )
        self.b_run.state(["disabled"] if not (ok and not self.busy) else ["!disabled"])

    def _log(self, msg: str, tag: str = ""):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _run(self):
        inp = Path(self.var_in.get().strip()).resolve()
        if not inp.is_file():
            self._log(f"input deck not found: {inp}", "warn")
            return
        try:
            rays = int(self.var_rays.get())
            seed = int(self.var_seed.get())
        except ValueError:
            self._log("rays and seed must be integers", "warn")
            return
        engine, fit = self.var_engine.get(), self.var_fit.get()
        self.busy = True
        self.b_run.state(["disabled"])
        self.b_cancel.state(["!disabled"])
        self.b_open.state(["disabled"])
        self.var_status.set("running…")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._log(f"deck: {inp}", "dim")
        self._save_cfg()
        threading.Thread(
            target=self._worker, args=(inp, rays, seed, engine, fit), daemon=True
        ).start()

    def _worker(self, inp, rays, seed, engine, fit):
        t0 = time.time()
        try:
            html = fork(
                inp,
                rays=rays,
                seed=seed,
                engine=engine,
                fit=fit,
                log=lambda m: self.q.put(("log", m, "ok" if m.startswith("[") else "")),
            )
            self.q.put(("done", str(html.resolve()), ""))
        except SystemExit as exc:
            self.q.put(("fail", str(exc), "warn"))
        except Exception as exc:  # surface real tracebacks in the log pane
            import traceback

            self.q.put(("log", traceback.format_exc(limit=6), "warn"))
            self.q.put(("fail", f"{type(exc).__name__}: {exc}", "warn"))
        finally:
            self.q.put(("time", f"{time.time() - t0:.1f} s", "dim"))

    def _cancel(self):
        killed = cancel()
        self._log(
            "cancel requested: Turtle run terminated, pipeline will stop"
            if killed
            else "cancel requested: pipeline will stop at the next step",
            "warn",
        )

    def _open(self):
        if self.last_html and Path(self.last_html).is_file():
            webbrowser.open(Path(self.last_html).resolve().as_uri())

    def _open_dir(self):
        p = Path(self.var_in.get()).resolve().parent if self.var_in.get() else ROOT
        if p.is_dir():
            webbrowser.open(p.as_uri())

    def _on_close(self):
        self._save_cfg()
        self.root.destroy()

    # ---------------------------------------------------------------- pump
    def _pump(self):
        try:
            while True:
                kind, msg, tag = self.q.get_nowait()
                try:
                    self._handle(kind, msg, tag)
                except Exception as exc:
                    self._log(f"[ui] {type(exc).__name__}: {exc}", "warn")
        except queue.Empty:
            pass
        self.root.after(80, self._pump)

    def _handle(self, kind, msg, tag):
        if kind == "log":
            self._log(msg, tag)
        elif kind == "done":
            self.last_html = Path(msg)
            self.var_status.set("done")
            self._log(f"html: {self.last_html}", "ok")
            self.b_open.state(["!disabled"])
            self.var_prev.set(self._summary(self.last_html))
            webbrowser.open(self.last_html.as_uri())
        elif kind == "fail":
            self.var_status.set("failed")
            self._log(msg, "warn")
        elif kind == "time":
            self._log(f"elapsed {msg}", "dim")
            self.busy = False
            self.b_cancel.state(["disabled"])
            self._sync_run()

    def _summary(self, html: Path) -> str:
        try:
            from .model import parse_deck
            from .resparse import parse_res

            stem = (
                html.stem[: -len("_viz")] if html.stem.endswith("_viz") else html.stem
            )
            work = html.parent / f"{stem}_viz"
            deck = work / f"{stem}_viz.dat"
            res = work / f"{stem}_hist.res"
            if not deck.is_file():
                deck = html.parent / f"{stem}.dat"
            _, meta = parse_deck(str(deck))
            hs = parse_res(str(res)) if res.is_file() else []
            return (
                f"{html.name}\n"
                f"{meta['comment'][:70]}\n"
                f"Pbeam = {meta['pbeam']:.6f} GeV/c · zmax = {meta['zmax']:.2f} m · "
                f"{meta['norays']} rays in the viz deck\n"
                f"{len(hs)} Turtle histograms parsed from {res.name}"
            )
        except Exception:
            return html.name


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
