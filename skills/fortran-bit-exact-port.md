# Skill (DRAFT — confirm after validation tests): bit-exact legacy Fortran port

Goal: port a legacy numeric Fortran program to Python so its output is
**byte-identical** to the original binary on the reference input. Hard rules
inherited from the source project: never change physical models; never change
the order of mathematical operations without a probe check.

## 0. Establish the numerics model first (decides everything)

1. Find the original compiler and its evaluation precision. Watcom/old x86
   compilers compute `REAL` expressions in **x87 extended (64-bit mantissa)**
   and round to float32 **only at each variable store**. Modern Python/numpy
   rounds at every operation → divergence after a few hundred ops.
2. `np.longdouble` on x86-64 is 80-bit storage but 53-bit effective (no x87
   extended semantics on most builds). Verify with a probe:
   `np.longdouble(1) + np.longdouble(2)**-64 > np.longdouble(1)` — False
   means it is NOT x87. Use `mpmath.mp.prec = 64` instead.
3. Emulate with three primitives (see `turtle2py/x87.py`):
   - `V(x)` — load: keep extended, no rounding;
   - `S(x)` — store: round to float32 (the only rounding point);
   - transcendentals (`sin/cos/exp`) take the **unrounded extended** argument
     when the compiler kept it in a register.
4. Literals in source are REAL*4 constants, not exact reals:
   `0.1` → `float32(0.1) = 0.100000001490116119384765625`. Round every
   literal through float32 at import time.
5. Constants computed at runtime (e.g. from a reader) inherit the reader's
   rounding chain — reproduce the chain, do not `float32(final_value)`.
6. Compiler register-allocation asymmetries are real semantics: e.g. one
   subexpression gets an unrounded extended argument, its sibling gets a
   REAL*4-spilled one. Encode each site exactly as probed; do not "clean up".

## 1. Ground truth by probe instrumentation

- Build the original with inserted `WRITE` dumps of intermediate state
  (`turtlepN.f` variants). Watcom env:
  `WATCOM=...; PATH=$WATCOM/binnt; WATCOM16=$WATCOM/binw; wfl386 file.f`.
  Inserted WRITEs must come after all COMMON/DATA statements; sources CRLF.
- **Inserted WRITEs perturb register allocation.** A probe that disagrees with
  the unmodified binary is an artifact of the probe, never a criterion. The
  only reference is the unmodified binary's output file.
- Dump per-stage ground truth (`.res` files), keep them as the check corpus;
  delete superseded ones.

## 2. Legacy record format (FORMAT) byte-exactness

- Render FORMAT semantics byte-exactly: carriage-control char written as a
  literal byte; `/` terminates record; Iw/Fw overflow → `*`*w; signed zero →
  ` 0.000`.
- Argument-exhaustion rules are compiler-specific — verify with tiny
  standalone probes (0 args prints literals fully; after ≥1 arg, WRITE ends
  at the next data descriptor; X/literals between exhaustion and it are
  dropped). Encode as a `consumed` flag + lookahead in the renderer.

## 3. Validation ladder (each step a kept record-diff script)

1. RNG stream vs dumped sequence (integer recurrence, exact).
2. Reader/tokenizer + first print section.
3. Setup/driver records.
4. Per-event kernels (scattering, bends, per-element state).
5. Small case (fast, seconds) — full output diff. Keep as regression.
6. **Intermediate case (minutes)** — same input with a reduced ray count;
   catches accumulating surfaces (histograms, matrices, loss counters) that
   the small case cannot reach. Generate its reference from the original
   binary; confirm it differs from the small/full references.
   **Real payoff (Turtle2Py, 2026-10-05):** the 100-ray case was fully
   bit-exact, yet the 100k case exposed 11 mismatches in histogram moment
   accumulation (`XMOM/XMOM2` online-update chain, `turtle.f:409-410`) —
   float64 drift of 1 ULP per F10.5 print. Fix: evaluate the update chain
   in x87 extended with store-only rounding and unrolled integer powers.
   Lesson: per-event bit-exactness does NOT imply accumulation-chain
   bit-exactness; any running-moment/running-sum in REAL must be probed
   at scale.
7. Full case — detached job; report record-by-record mismatch count.

Diff script pattern: split both files on the record terminator, compare
record-by-record, print `ref recs / py recs / mismatches` + first N diffs,
exit nonzero on any mismatch.

## 4. Long-run hygiene

- Interactive python tool times out (120 s) → run long jobs detached
  (`compute_job`), log to a file, wake-on-completion; never poll.
- A reduced-count input = full input with only the ray-count line changed.
- After each verified step: update the progress journal, delete regenerable
  snapshots (run outputs, caches, orphaned probe sources), keep ground-truth
  dumps and references.

## Evidence anchors (Turtle2Py)

x87 model: `turtle2py/x87.py`; FORMAT renderer: `turtle2py/formats.py`;
checks: `probe/{small_run,el_check,sc_check,setup_check,elements_check}.py`
all 0 mismatches; 100-ray case 2750/2750 bit-exact.
