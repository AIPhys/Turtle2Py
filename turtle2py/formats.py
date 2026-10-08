"""Watcom F77 FORMAT renderer reproducing test_ref.res byte-for-byte.

Verified conventions (2753 CRLF records in test_ref.res):
  * the leading carriage-control char is written LITERALLY as byte 0
    (1H1 -> b'1\r\n'; 1H0 -> b'0...'; 1H+ -> b'+...'; default = first char)
  * '/' terminates a record; a record with no output chars is b'\r\n'
  * descriptors beyond the end of the WRITE argument list are skipped
  * Iw / Fw.d overflow -> w asterisks
"""

from decimal import Decimal, ROUND_HALF_UP

CRLF = b"\r\n"
_TOK = None


def i_edit(v, w):
    s = str(int(v))
    return "*" * w if len(s) > w else s.rjust(w)


def f_edit(v, w, d):
    fv = float(v)
    if fv != fv:
        # Watcom Fw.d prints a NaN as '-nan' (the x87 default NaN is
        # negative, e.g. the 0/0 correlation of a zero-RMS summary block).
        return "-nan".rjust(w)
    if fv in (float("inf"), float("-inf")):
        s = "Infinity" if fv > 0 else "-Infinity"
        return "*" * w if len(s) > w else s.rjust(w)
    q = Decimal(1).scaleb(-d)
    dec = Decimal(float(v)).quantize(q, rounding=ROUND_HALF_UP)
    if dec == 0:
        # Watcom drops the sign when a value rounds to zero (negative zero
        # prints as ` 0.000`, not ` -0.000`).
        dec = abs(dec)
    s = format(dec, "f")
    if d == 0:
        s = s.split(".")[0]
    return "*" * w if len(s) > w else s.rjust(w)


def e_edit(v, w, d):
    s = "%.*fE%+03d" % (d, float(v))
    s = s.replace("E+", "E+").replace("E-0", "E-")
    return "*" * w if len(s) > w else s.rjust(w)


def g_edit(v, w, d):
    """Watcom Gw.d: d significant digits, rounded half-up on the exact
    binary value.  Fixed-point (F-style, trailing blanks, left-justified)
    when the decimal exponent is in [-1, d-1]; otherwise 0.xxx E-form
    (right-justified) with exponent shifted by one.  Trailing zeros kept.
    Overflow -> '*'*w."""
    dec = Decimal(float(v))
    sign = "-" if dec < 0 else ""
    dec = abs(dec)
    if dec == 0:
        s = "0." + "0" * d
        s = " " * (w - 4 - len(s)) + s + " " * 4
        return "*" * w if len(s) > w else s
    c = dec.normalize()
    exp = c.adjusted()
    m = c.scaleb(-exp).quantize(Decimal(1).scaleb(-(d - 1)), rounding=ROUND_HALF_UP)
    digits = str(m).replace(".", "")
    if len(digits) > d:
        digits = digits[0] + "0" * (d - 1)
        exp += 1
    if -1 <= exp <= d - 1:
        if exp >= 0:
            s = digits[: exp + 1] + "." + digits[exp + 1 :]
        else:
            s = "0." + digits
        s = sign + s
        # Watcom G fixed style: leading blanks, value, 4 trailing blanks
        # reserved for the (omitted) exponent field.
        s = " " * (w - 4 - len(s)) + s + " " * 4
        return "*" * w if len(s) > w else s
    s = "%s0.%sE%+03d" % (sign, digits, exp + 1)
    return "*" * w if len(s) > w else s.rjust(w)
    s = "%s0.%sE%+03d" % (sign, digits, exp + 1)
    return "*" * w if len(s) > w else s.rjust(w)


def a_edit(arg, w):
    if isinstance(arg, str):
        return (arg[:w] if w else arg).ljust(w)
    b = int(arg).to_bytes(4, "little", signed=True)
    return b[-w:].decode("latin-1") if w else b.decode("latin-1")


def _tokenize(f):
    toks = []
    i, n = 0, len(f)
    while i < n:
        c = f[i]
        if c == "(":
            j, depth = i + 1, 1
            while depth:
                if f[j] == "(":
                    depth += 1
                elif f[j] == ")":
                    depth -= 1
                    if not depth:
                        break
                j += 1
            toks.append(("(", f[i + 1 : j]))
            i = j + 1
            continue
        if c == "/":
            toks.append(("/", None))
            i += 1
            continue
        if c == "," or c == " ":
            i += 1
            continue
        k = i
        while k < n and f[k].isdigit():
            k += 1
        num = int(f[i:k]) if k > i else None
        if k >= n:
            break
        d = f[k]
        if d == "H":
            toks.append(("H", f[k + 1 : k + 1 + num]))
            i = k + 1 + num
            continue
        if d == "X":
            toks.append(("X", num or 1))
            i = k + 1
            continue
        if d in "Ii":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            toks.append(("I", int(f[k + 1 : m])))
            i = m
            continue
        if d in "FfEeGg":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            w = int(f[k + 1 : m])
            dd = 0
            if m < n and f[m] == ".":
                p = m + 1
                while p < n and f[p].isdigit():
                    p += 1
                dd = int(f[m + 1 : p])
                m = p
            toks.append((d.upper(), (w, dd)))
            i = m
            continue
        if d in "Aa":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            toks.append(("A", int(f[k + 1 : m]) if m > k + 1 else 0))
            i = m
            continue
        raise ValueError("FORMAT token at %d: %r" % (k, f[k : k + 12]))
    return toks


def _expand(f):
    """Flatten a FORMAT into a list of (kind, payload) with repeats applied."""
    out = []
    i, n = 0, len(f)
    while i < n:
        c = f[i]
        if c == "," or c == " ":
            i += 1
            continue
        if c == "/":
            out.append(("/", None))
            i += 1
            continue
        if c == "'":
            j = i + 1
            buf = []
            while j < n:
                if f[j] == "'":
                    if j + 1 < n and f[j + 1] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(f[j])
                j += 1
            out.append(("H", "".join(buf)))
            i = j + 1
            continue
        if c == "(":
            j, depth = i + 1, 1
            while depth:
                if f[j] == "(":
                    depth += 1
                elif f[j] == ")":
                    depth -= 1
                    if not depth:
                        break
                j += 1
            inner = _expand(f[i + 1 : j])
            i = j + 1
            k = i
            while k < n and f[k].isdigit():
                k += 1
            rep = int(f[i:k]) if k > i else 1
            if k > i:
                i = k
            out.extend(inner * rep)
            continue
        k = i
        while k < n and f[k].isdigit():
            k += 1
        num = int(f[i:k]) if k > i else None
        if k >= n:
            break
        d = f[k]
        if d == "(":
            j, depth = k + 1, 1
            while depth:
                if f[j] == "(":
                    depth += 1
                elif f[j] == ")":
                    depth -= 1
                    if not depth:
                        break
                j += 1
            out.extend(_expand(f[k + 1 : j]) * (num or 1))
            i = j + 1
            continue
        if d == "H":
            out.append(("H", f[k + 1 : k + 1 + num]))
            i = k + 1 + num
            continue
        if d == "X":
            out.append(("X", num or 1))
            i = k + 1
            continue
        if d in "Ii":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            out.extend([("I", int(f[k + 1 : m]))] * (num or 1))
            i = m
            continue
        if d in "FfEeGg":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            w = int(f[k + 1 : m])
            dd = 0
            if m < n and f[m] == ".":
                p = m + 1
                while p < n and f[p].isdigit():
                    p += 1
                dd = int(f[m + 1 : p])
                m = p
            out.extend([(d.upper(), (w, dd))] * (num or 1))
            i = m
            continue
        if d in "Aa":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            w = int(f[k + 1 : m]) if m > k + 1 else 0
            out.extend([("A", w)] * (num or 1))
            i = m
            continue
        if d in "Ll":
            m = k + 1
            while m < n and f[m].isdigit():
                m += 1
            w = int(f[k + 1 : m]) if m > k + 1 else 1
            out.extend([("L", w)] * (num or 1))
            i = m
            continue
        raise ValueError("FORMAT token at %d: %r" % (k, f[k : k + 12]))
    return out


def render(fmt, args):
    """Return the bytes of one WRITE statement (records joined by CRLF)."""
    toks = _expand(fmt)
    flat = []
    for a in args:
        if isinstance(a, (list, tuple)) or (
            hasattr(a, "ndim")
            and getattr(a, "ndim", 1) > 0
            and not isinstance(a, (str, bytes))
        ):
            flat.extend(list(a))
        else:
            flat.append(a)
    args = flat
    recs = []
    cur = []
    terminated = False
    consumed = False
    for ti, (kind, pay) in enumerate(toks):
        if kind == "/":
            recs.append("".join(cur))
            cur = []
            if not args:
                # Watcom: at a record boundary with the argument list
                # exhausted, the WRITE ends.  A next record that needs a data
                # edit is emitted empty (FORMAT 940 of PRINT1 -> the blank
                # record after the data; FORMAT 9104 -> the blank record after
                # the data).  A literal-only next record is rendered in full
                # (TRHIST `1X,28(1H=)`), then the WRITE ends.
                has_data = False
                for k2, p2 in toks[ti + 1 :]:
                    if k2 == "/":
                        break
                    if k2 in "IFEA":
                        has_data = True
                        break
                if has_data:
                    recs.append("")
                    terminated = True
                    break
            continue
        if not args and consumed:
            # Watcom (probe/fmtgrp.exe, probe/fmtgrp2.exe, turtle.f FORMAT 110
            # and APLIM FORMAT 900): once the argument list is exhausted, the
            # WRITE ends at the next data edit descriptor of the current
            # record, and every X/literal between the exhaustion point and
            # that descriptor is dropped (FORMAT 900 `3(8X,A4)` with one
            # argument -> no trailing spaces; FORMAT 110 `...,A4,' FROM THE
            # TARGET'` with all arguments consumed -> the literal prints).
            data_left = False
            for k2, p2 in toks[ti:]:
                if k2 == "/":
                    break
                if k2 in "IFEA":
                    data_left = True
                    break
            if data_left:
                if cur:
                    recs.append("".join(cur))
                terminated = True
                break
        if kind == "H":
            cur.append(pay)
        elif kind == "X":
            cur.append(" " * pay)
        elif kind == "I":
            consumed = True
            cur.append(i_edit(args.pop(0), pay))
        elif kind == "F":
            consumed = True
            cur.append(f_edit(args.pop(0), *pay))
        elif kind == "E":
            consumed = True
            cur.append(e_edit(args.pop(0), *pay))
        elif kind == "G":
            consumed = True
            cur.append(g_edit(args.pop(0), *pay))
        elif kind == "A":
            consumed = True
            cur.append(a_edit(args.pop(0), pay))
        elif kind == "L":
            consumed = True
            v = "T" if args.pop(0) else "F"
            cur.append(v.rjust(pay))
    if not terminated:
        recs.append("".join(cur))
    out = bytearray()
    for r in recs:
        out += r.encode("latin-1")
        out += CRLF
    return bytes(out)
