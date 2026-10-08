"""Reader tests: RDELMT on turtle_in.dat vs the Fortran PRINT1 listing in
test_ref.res (the authoritative element list printed by turtle.exe)."""
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from turtle2py.io import CardReader, ElementReader, StopInput, unpack, _h

ROOT = Path(__file__).resolve().parents[1]


def _lines(name):
    return (ROOT / name).read_bytes().decode('latin-1').split('\n')


def read_all():
    r = CardReader(_lines('turtle_in.dat'))
    r.rdnext(2)
    r.rdskip()
    words, l = r.rdstrg(20)
    title = ''.join(unpack(w) for w in words[:l])
    norays, _ = r.rdfix()
    r.rdnext(-1)
    er = ElementReader(r)
    els = []
    while True:
        nword, flush = er.rdelmt()
        if nword == 0:
            break
        e = er.e
        els.append((int(e.datum[0]), e.nword, e.datum[:e.nword].copy(),
                    e.vary[:e.nvary].copy(), e.label))
    return title, norays, els


def ref_element_lines():
    pat = re.compile(r"^0 *(-?\d+)\.([^;]*);")
    out = []
    for l in _lines('test_ref.res')[4:]:
        m = pat.match(l)
        if m and (1 <= abs(int(m.group(1))) <= 21
                  or 50 <= abs(int(m.group(1))) <= 53
                  or abs(int(m.group(1))) == 60):
            out.append((int(m.group(1)), m.group(2)))
    return out


def test_title_and_norays():
    title, norays, _ = read_all()
    assert title.startswith('Carbon beam 2.04 GeV.c')
    assert norays == 5000000


def test_element_count_and_types():
    _, _, els = read_all()
    ref = ref_element_lines()
    assert len(els) == len(ref) == 198
    assert (sorted(Counter(t for t, *_ in els))
            == sorted(Counter(t for t, _ in ref)))


def test_beam_element():
    _, _, els = read_all()
    t, nword, datum, vary, label = els[0]
    assert (t, nword) == (1, 8)
    assert label == '    '
    np.testing.assert_allclose(datum,
                               [1, 0.5, 0.86803, 0.5, 0.86803, 0, 0, 1.88815],
                               rtol=0, atol=1e-6)


def test_vary_codes_parsed():
    """`50.1` is type 50 with vary code 1 -> VARY(2)=1 (NFL=1)."""
    _, _, els = read_all()
    dotted = [e for e in els if e[3][1:].size > 0 and e[3][1] != 0]
    assert dotted, 'no vary codes found'
    for t, nword, datum, vary, label in dotted:
        assert abs(t) in (50, 51, 52, 53, 16, 13)


def test_hconstants():
    assert _h('CM') == 19779          # 2HCM: 'C' low byte, 'M' next
    assert _h('P/10') == 808529744    # 4HP/10 = 0x30312F50
    assert unpack(_h('P/10')) == 'P/10'


def test_sentinel_stops():
    r = CardReader(['SENTINEL'])
    with pytest.raises(StopInput):
        r.rdnext(2)
