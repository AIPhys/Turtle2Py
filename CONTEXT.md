# Turtle2Py — compacted context

Compact distillation of `PROGRESS.md` (588 lines, kept as the detailed log) plus the
2026-10-05 session. Read `PROGRESS.md` for full derivations; this file is the resume point.

Working folder: `C:\AI\Turtle2Py`.

---

## 1. Goal

Python clone of **TURTLE** (`turtle.f`, 3195 lines, Watcom Fortran 77, `turtle.exe` PE32 i386)
— particle tracking, bit-equivalent output.

Mandatory artifacts: `ARCHITECTURE.md`, `PHYSICS_SPEC.md`, `SPEC.md`, `VALIDATION.md`,
package `turtle2py/`, `tests/` (pytest). **Hard constraints: do not change physical models;
do not change the order of mathematical operations without verification.**

---

## 2. Numerics model (the thing that decides bit-exactness)

- All tracking variables are default `REAL` = **REAL\*4 / float32**. `DOUBLE PRECISION`
  appears **only** inside `RANF` (turtle.f:3130–3165).
- Watcom computes in **x87 extended (64-bit mantissa)** and rounds to float32 **only at each
  variable store**. Emulated in `turtle2py/x87.py`: `V`, `S`, `K`, `P`, transcendentals take
  **unrounded extended** arguments (verified vs probe15 SD at I=272, ulp 0; a float32-rounded
  argument is off by 6 ULP).
- `np.longdouble` on this host is 53-bit, **not** x87 → use mpmath with `prec=64`
  (`turtle2py/io.py:34`, `_mpf`, `_f32m`).
- **Literals are REAL\*4 constants**, not exact values. Verified 2026-10-05: in `RDFLT`,
  `FF = 0.1` / `FF = 0.1 * FF` uses `float32(0.1) = 0.100000001490116119384765625`.
  Exact 0.1 prints `0.05210`, the reference prints `0.05211`.
- Constants must be float32-rounded: `PI=_c(6.2831853)`, `Z_TEMP=_c(11.037)`,
  `YY_MAX=_c(_c(0.001)*13.8745)`, `Y1_MAX=_c(_c(0.001)*2.1622)`.
- `PBEAM = 1.8881509304046631` (reader chain, hex `3ff1aeee`) — **not** `float32(1.888151)`
  = 1.8881510496139526. `P0 = 1.9028400182724`. `BLANK = 538976288` (`0x20202020`), not 32.
- Host: the managed `python` tool times out at 120 s → run long jobs via `bash python`.

---

## 3. Reference and validation policy

- **Only** `test_ref.res` (286438 B) is the reference; `test_ref2.res` is bit-identical
  (determinism proven). `small_ref.res` (286306 B) is the small-case reference.
- `turtle_out.res` is **NOT** a reference (~3800-line diff; old run used `raymax` x=0.8,
  dp/p=0.1).
- Regenerate reference (workdir `C:\AI\Turtle2Py`):
  `printf 'turtle_in.dat\r\ntest_ref.res\r\n' | ./turtle.exe`
- Watcom build: `export WATCOM='C:\WATCOM'; export PATH="$WATCOM/binnt:$PATH";
  export WATCOM16="$WATCOM/binw"; wfl386 turtlepN.f` (run from root:
  `printf 'turtle_in.dat\r\nprobeN.res\r\n' | ./probe/turtlepN.exe`).
  Probe sources are **CRLF**; inserted `WRITE` must come **after** all COMMON/DATA statements.

---

## 4. Checks and last measured numbers

| Command | Last result |
|---|---|
| `python -m pytest tests -q` | **20 passed** (2026-10-05) |
| `python probe/setup_check.py` | ref 2753 / py 382 recs, **mismatches 0** (2026-10-05) |
| `python probe/elements_check.py` | 198 / 198, **mismatches 0** (2026-10-05) |
| `python probe/ray_check.py` | ray 1 bit-exact vs `probe/groundtruth.txt` (rays 2–4 need RAYRUN) |
| `python probe/el_check.py` | EL 153/153, **mismatches 0** (2026-10-05) |
| `python probe/small_run.py` | ref 2750 / py 2750 recs, **mismatches 0** — small case bit-exact (2026-10-05) |
| `python probe/full_run.py` | full 5e6-ray run vs `test_ref.res` — in progress (job 2bef728d-fea) |

Context state matches reference: `norays 5000000, i1 703, nhists 49, limno 1939, loss 0,
dkflag False` (`LEFT = 10000-1939 = 8061` = reference record 471).

---

## 5. Code state (`turtle2py/`)

| Module | State |
|---|---|
| `random.py` | **done, verified** — `G900`: `ranf()→float32`, `dranf()`, `g900gt()`, `g900st()`; `M=44485709377909`, `S0=48131768981101` |
| `state.py` | done — `Context` dataclass, all COMMON blocks, `ctx.idata = data.view(np.int32)` |
| `io.py` | **done, verified** — `CardReader` (`rdnext/rdfix/rdflt/rdstrg/rdpack/rdskip`), `ElementReader.rdelmt`, PRINT1 from RDELMT |
| `elements.py` | **done, verified** — `nu/reset/repeat/focus/quad/qstop/bstop/sext/solo/multi/hstun/hstval/bend`; `bstop/qstop` take `lflag` **already +1** |
| `formats.py` | **done, verified** — FORMAT expansion; Watcom argument-exhaustion semantics (WRITE ends, current record emitted; `/` with exhausted args → empty record) |
| `report.py` | done — PRINT1 (FORMAT 960 last edit `3H' ;`), signed-zero `f_edit` |
| `hist.py` | created, **untested** — `histo`, `entmat`, `ehist` (AMAX fix: ACROSS 0=0, entries 72=72) |
| `fields.py` | **SETUP + driver verified** (records 1..382 bit-exact) |
| `tracking.py` | **in progress** — `emit_my`, `scatt_my`, quad/focus/bend chains; RAYRUN main loop at `# ---CHUNK-B---` |
| `x87.py` | x87 emulation, validated vs probe13 QD and probe15 SD |

RNG facts: `DS = (DS*DM) mod 2**48`, `DR = DS/2**48`; Fortran split chain ≡ big-int multiply.
First 5 (DR / RANF / state after): 0.5801136485795872 / 0.5801136493682861 / 163287475723473;
0.9505127349807658 / 0.9505127072334290 / 267545549941893; 0.7863714253306036 /
0.7863714098930359 / 221343878630857; 0.2976202640037293 / 0.2976202666759491 / 83772656879069;
0.4536999002984920 / 0.4536998867988586 / 127705168870145. `RANF(X)` ignores its argument.
EMIT_MY uses 18 RANF calls for ray 1, 12 for rays 2+; 56 tracking calls between rays.

Reader gotchas (all fixed): `BLANK=538976288`; `RDPACK`/`UBUNCH` little-endian words;
`_vary` must return `separ`; exponent marker is `TABLE(15)` = **'F'** not 'E'; `RDSTRG`
returns a `BLANK`-prefilled array.

---

## 6. Resolved: per-element ray tracking (2026-10-05)

`probe/el_check.py` → EL 153/153, **mismatches 0**. `scatt_my` rewritten in the
x87 model (`a1=S(sig_r1*sig)`, `a2=S(sig_rr*sig)`; `del_x1/del_xx` extended
`cos(phi)`, `del_y1/del_yy` `S(sin(phi))`); `_bend_sector` sector path
bit-exact (probe16, 288/288).

**Probe-dump caveat (2026-10-05):** inserted WRITEs in `turtlep19/22/23.f`
perturb Watcom register allocation, so the BA/BB/SE dumps (probe19/22/23)
diverge from Python by 1–26 ULP **in the probes themselves**. The real
reference `small_ref.res` matches bit-for-bit → those probes are artifacts
and were deleted (`bend_check.py`, `se_check.py`, `probe19/22/23.res`,
`turtlep19/22/23.f`). Do not use them as criteria.

FORMAT argument-exhaustion semantics (Watcom, `probe/fmtgrp*.f`): after ≥1
argument is consumed, the WRITE ends at the next data descriptor of the
current record; X/literals between exhaustion and it are dropped; if no data
descriptor precedes `/`, literals print fully. Encoded in `formats.render`
(`consumed` flag + lookahead). APLIM FORMAT 910 prints per-aperture
`ISTOP(J,IAP)`, not the running `KSTOP` (TOTAL line uses `KSTOP`).

---

## 7. Key line pointers in `turtle.f`

| What | Lines |
|---|---|
| `RANF` | 3130–3165 |
| `RAYRUN` | 1125–1581 |
| `SETUP` | 2554–3056 |
| `RDELMT` | 2134–2324 |
| `NU` | 1995–2028 |
| `EMIT_MY` | 251–371 |
| `SCATT_MY` | 1014–1123 |
| `BEND` | 1694–1863 |
| `FOCUS` | 1909–1934 |
| `HISTO` | 644–667 |
| `TRHIST` | 1583–1645 |
| `OUTMAT` | 871–1011 |
| `UBUNCH` | 3167–3195 |
| `RDFLT` | 2356–2405 |

RAYRUN flow (labels): 100 (NCT, P0=PBEAM, EMIT_MY, Z=0, LFLAG=0, IAP=0, NHIST=0, IP=0,
APB=0, MMAX=0, INEXT=-10) → 130 (I=1, IFLAG=.F., SET=.F.) → 200 dispatch
`(210,220,230,240,250,260,270,600,290,600,600,600,600,340,600,360,600,380,390,400,410), NTYPE`;
53→530, ≥50→500 → 210 (`IF(IDATA(I+8).NE.LFLAG) GO TO 600`; SCATT_MY; `P=P+DATA(I+7)`) →
590 (`Z=Z+DATA(I+1)`) → 600 (`I=I+NU(NTYPE)`, `IF(I.LE.I1) GO TO 200`) → 650/670 (aperture loss
+ HISTO/ENTMAT) → 690 (`EHIST`, `IF(NCT.LT.NORAYS) GO TO 100`). Driver:
`INITZE→SETUP→HEDING→ZERO→LEFT=10000-LIMNO→WRITE(NOUT,100)→RAYRUN→OHIST→APLIM`; input/output
file names read from stdin (FORMAT A40).

Input case: 5 000 000 rays; carbon 1.888151 GeV/c; Ti target 0.520566 cm; dipoles M28F…M33D;
quadruplet triplets Q1…Q7; `-50/-51/-52` histograms; file ends `53.1` then `SENTINEL`.
Reader yields 198 elements; type distribution `1:15, 2:20+2, 3:24+1, 4:10+1, 5:7+7, 6:12,
7:5+3, 13:1, 16:23+3, 50:21+6, 51:14+4, 52:14+4, 53:1` (`+N` = negative type, handled inline).

---

## 8. Files: keep vs trash

**Keep:** `turtle.f`, `turtle.exe`, `turtle_in.dat`, `turtle_small.dat`,
`test_ref.res`, `test_ref2.res`, `small_ref.res`, `PROGRESS.md`, `CONTEXT.md`,
`SPEC.md`, `PHYSICS_SPEC.md`, `ARCHITECTURE.md`, `VALIDATION.md`,
`turtle2py/`, `tests/`, `probe/*.py`, `probe/*.f`, `probe/groundtruth.txt`,
`probe5.res`, `probe6.res`, `probe13.res`, `probe16.res`, `probe17.res`,
`probe18.res`, `turtle_out.res` (historical, non-reference).

**Trash (deleted 2026-10-05):** `probe4/8/9/9b/10/11/12/14/19/20/21/22/23/24.res`,
`probe_out*.res`, `probe*_stdout.txt`, `*.err`, `probe/*.obj`, `probe/*.exe`,
`probe/*.log`, `scratch_py*.res`, `scratch_el75.res`, `small_py*.res`,
`.pytest_cache/`, superseded probes (`bend_check.py`, `se_check.py`,
`*_tree*.py`, `sector_*.py`, `turtlep4/8/9/10/11/12/14/19/20/21/22/23/24.f`).
`.openscience-approved-*.bak` are harness-owned (permission denied) — leave them.

**Trash (deleted 2026-10-05, 2nd pass):** `probe/turtle_in.dat` (md5-identical
duplicate of root), orphaned probe sources `turtlep2/3/7/15.f` (their `.res`
already gone), `small_py2/4/6.res`, `.pytest_cache/`.

---

## 9. Next steps

1. **Mid run (100k)** job `238768fc-ca7` (`probe/mid_run.py` vs `mid_ref.res`)
   after the x87 moment fix → fill §4a of `VALIDATION.md`.
2. Then **full run** `probe/full_run.py` vs `test_ref.res` (old job
   2bef728d-fea cancelled, no output) → fill §4.
3. If mismatches: localize by record (histograms/OUTMAT are the untested
   large surface; small case covers 100 rays only).
3. Untested paths: general bend (BD/ID/RD, non-sector), 15-element TEXT(3),
   decay-on (`DKFLAG`), 2D OUTMAT beyond the small case.
