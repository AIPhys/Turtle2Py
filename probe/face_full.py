"""Check label-220 chain (TANB, SECB, SB) with extended FACE arg vs port's rounded FACE."""
import numpy as np, mpmath as mp
mp.mp.prec = 64
def g(t): return float(t.replace('E','e'))
f32 = lambda v: np.float32(v)
rows = []
for line in open('probe31.res'):
    if not line.startswith('0W'): continue
    f = [line[1:][2+i*22:2+(i+1)*22].strip() for i in range(7)]
    rows.append([g(x) for x in f])
uniq = []
for r in rows:
    if r not in uniq: uniq.append(r)
print('unique', len(uniq))
bad_ext = bad_r32 = 0
with mp.workprec(80):
    for w2,u7,fc,tb,secb,tcor,sb in uniq:
        fe = mp.mpf(float(f32(w2))) * mp.mpf(float(f32(u7)))
        ff = mp.mpf(float(f32(fc)))
        tb_e = f32(mp.tan(fe)); secb_e = f32(mp.mpf(1.0)/mp.cos(fe))
        tb_r = f32(mp.tan(ff)); secb_r = f32(mp.mpf(1.0)/mp.cos(ff))
        if tb_e != f32(tb) or secb_e != f32(secb): bad_ext += 1
        if tb_r != f32(tb) or secb_r != f32(secb): bad_r32 += 1
print('extended FACE arg: bad', bad_ext, '/', len(uniq))
print('rounded   FACE arg: bad', bad_r32, '/', len(uniq))
