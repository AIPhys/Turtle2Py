"""Explicit context replacing the Fortran COMMON blocks of turtle.f.

Each dataclass field group maps 1:1 to a COMMON block (see ARCHITECTURE.md).
All floating point is np.float32 because the Watcom build uses default
REAL*4 (turtle.f declares REAL L,N,MASS,... and no DOUBLE PRECISION in the
tracking code; only the RNG internals are DOUBLE PRECISION).
"""
import numpy as np
from dataclasses import dataclass, field

F32 = np.float32


def _f(n, v=0.0):
    return np.full(n, v, dtype=np.float32)


@dataclass
class Context:
    # /BLOC1/ DATA(3001), I, I1  +  EQUIVALENCE(IDATA, DATA)
    data: np.ndarray = field(default_factory=lambda: _f(3002))
    i: int = 1
    i1: int = 0

    @property
    def idata(self):
        return self.data.view(np.int32)

    # /BLOC2/
    unit: np.ndarray = field(
        default_factory=lambda: np.array(
            [0.01, 0.001, 0.01, 0.001, 0.01, 0.01, 0.01745329,
             1.0, 1.0, 1.0, 1.0], dtype=np.float32))
    name: list = field(default_factory=lambda:
                       ['CM  ', 'MR  ', 'CM  ', 'MR  ', 'CM  ', 'PC  ',
                        'DEG ', 'M   ', 'KG  ', 'GEVA', 'GEVC'])
    nom: list = field(default_factory=lambda:
                      ['   X', "  X'", '   Y', "  Y'", 'JUNK', 'DP/P',
                       'JUNK', '   Z', 'JUNK', 'JUNK', '   P'])
    nom1: list = field(default_factory=lambda: ['   R', '  XI', ' PSI', 'ZETA'])

    # /BLOC3/
    nin: int = 5
    nout: int = 6
    nol: int = 7

    # /BLOC4/
    raymax: np.ndarray = field(default_factory=lambda: _f(7))
    pbeam: np.float32 = F32(0.0)
    p0: np.float32 = F32(0.0)
    norays: int = 0

    # /BLOC5/
    sec: bool = False
    cap: list = field(default_factory=lambda: [False, False, False])
    mpa: bool = False

    # /BLOC6/
    nhists: int = 0
    nhist: int = 0
    limno: int = 0

    # /BLOC7/
    mtype: np.ndarray = field(default_factory=lambda: np.zeros(101, np.int32))
    nentry: np.ndarray = field(default_factory=lambda: np.zeros(101, np.int32))
    ncoor: np.ndarray = field(default_factory=lambda: np.zeros(101, np.int32))
    intvls: np.ndarray = field(default_factory=lambda: np.zeros(101, np.int32))
    begin: np.ndarray = field(default_factory=lambda: _f(101))
    end: np.ndarray = field(default_factory=lambda: _f(101))
    step: np.ndarray = field(default_factory=lambda: _f(101))
    zhist: np.ndarray = field(default_factory=lambda: _f(101))

    # /BLOC8/
    mtable: np.ndarray = field(default_factory=lambda: np.zeros(10001, np.float32))

    # /BLOC9/
    l: np.float32 = F32(0.0)
    h: np.float32 = F32(0.0)
    n: np.float32 = F32(0.0)
    bdb: np.float32 = F32(0.0)

    # /BLOC10/
    apb: np.ndarray = field(default_factory=lambda: _f(3))
    layl: np.float32 = F32(0.5)
    layx: np.float32 = F32(0.0)
    rab1: np.float32 = F32(0.0)
    rab2: np.float32 = F32(0.0)
    face: np.float32 = F32(0.0)

    # /BLOC11/
    qap: np.ndarray = field(default_factory=lambda: _f(4))
    ellips: bool = False
    hyper: bool = False

    # /BLOC12/
    value: np.ndarray = field(default_factory=lambda: _f(101))
    xmom: np.ndarray = field(default_factory=lambda: _f(101))
    xmom2: np.ndarray = field(default_factory=lambda: _f(101))
    nflag: np.ndarray = field(default_factory=lambda: np.zeros(101, np.int32))
    set_: np.ndarray = field(default_factory=lambda: np.zeros(101, bool))
    kflag: np.ndarray = field(default_factory=lambda: np.zeros(101, np.int32))
    iflag: np.ndarray = field(default_factory=lambda: np.zeros((3, 9), bool))
    zflag: np.ndarray = field(default_factory=lambda: _f(10, -1.0))
    ymom: np.ndarray = field(default_factory=lambda: _f(101))
    ymom2: np.ndarray = field(default_factory=lambda: _f(101))
    corr: np.ndarray = field(default_factory=lambda: _f(101))

    # /BLOC13/
    ray: np.ndarray = field(default_factory=lambda: _f(7))
    rayc: np.ndarray = field(default_factory=lambda: _f(7))
    rayn: np.ndarray = field(default_factory=lambda: _f(7))
    p: np.float32 = F32(0.0)
    pc: np.float32 = F32(0.0)
    pn: np.float32 = F32(0.0)
    fld: np.float32 = F32(0.0)
    mass: np.float32 = F32(0.0)
    massc: np.float32 = F32(0.0)
    massn: np.float32 = F32(0.0)
    fc: np.float32 = F32(0.0)
    fn: np.float32 = F32(0.0)
    pstar: np.float32 = F32(0.0)
    zmax: np.float32 = F32(0.0)
    dkflag: bool = False
    z: np.float32 = F32(0.0)

    # /BLOC14/
    mmax: int = 0
    gtop: np.float32 = F32(0.0)
    db: np.ndarray = field(default_factory=lambda: _f(21))
    cosm: np.ndarray = field(default_factory=lambda: _f(21))
    sinm: np.ndarray = field(default_factory=lambda: _f(21))

    # /BLOC15/
    ll: np.float32 = F32(0.0)
    kh2: np.float32 = F32(0.0)
    kv2: np.float32 = F32(0.0)
    kh: np.float32 = F32(0.0)
    kv: np.float32 = F32(0.0)
    khl: np.float32 = F32(0.0)
    kvl: np.float32 = F32(0.0)
    ray2: np.ndarray = field(default_factory=lambda: _f(7))
    rh: np.ndarray = field(default_factory=lambda: _f(4))
    rv: np.ndarray = field(default_factory=lambda: _f(4))

    # /BLOC16/
    kpart: list = field(default_factory=lambda: ['RAYS', 'RAYS', 'RAYS'])
    istop: np.ndarray = field(default_factory=lambda: np.zeros((3, 501), np.int32))

    # /BLOC17/
    ip: int = 0
    ic: np.ndarray = field(default_factory=lambda: np.zeros(5, np.int32))
    is_: np.ndarray = field(default_factory=lambda: np.zeros(5, np.int32))

    # /BLOC18/
    loss: int = 0
    nblk: np.ndarray = field(default_factory=lambda: np.zeros(11, np.int32))
    kflg: np.ndarray = field(default_factory=lambda: np.zeros(11, np.int32))
    xstrt: np.ndarray = field(default_factory=lambda: _f(11))
    xend: np.ndarray = field(default_factory=lambda: _f(11))
    lthx: np.ndarray = field(default_factory=lambda: np.zeros(11, np.int32))
    xbin: np.ndarray = field(default_factory=lambda: _f(11))
    nunx: np.ndarray = field(default_factory=lambda: np.zeros(11, np.int32))
    ystrt: np.ndarray = field(default_factory=lambda: _f(11))
    yend: np.ndarray = field(default_factory=lambda: _f(11))
    lthy: np.ndarray = field(default_factory=lambda: np.zeros(11, np.int32))
    ybin: np.ndarray = field(default_factory=lambda: _f(11))
    nuny: np.ndarray = field(default_factory=lambda: np.zeros(11, np.int32))

    # G900 RNG (RANF/DRANF in turtle.f); not a COMMON block, kept with state
    rng: object = None
