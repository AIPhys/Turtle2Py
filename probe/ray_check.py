"""Check tracking.emit_my rays 1-4 against Fortran ground truth (probe/groundtruth.txt)."""
import sys, re, numpy as np
sys.path.insert(0,'.')
from turtle2py.state import Context
from turtle2py.random import G900
from turtle2py import tracking
f32=np.float32
unit=[0.01,0.001,0.01,0.001,0.01,0.01]
work=[0.5,0.86803,0.5,0.86803,0.0,0.0]
ctx=Context()
for b,(w,u) in enumerate(zip(work,unit),1):
    ctx.raymax[b]=f32(f32(w)*f32(u))
ctx.pbeam=f32(1.8881509304046631)
rng=G900()
gt={}
for ln in open('probe/groundtruth.txt'):
    m=re.match(r'RAY\s+(\d+)\s+(.*)',ln)
    if m: gt[int(m.group(1))]=[float(v) for v in m.group(2).split()]
bad=0
for n in sorted(gt):
    tracking.emit_my(ctx,rng)
    want=gt[n]; got=[float(ctx.ray[j]) for j in range(1,7)]+[float(ctx.p)]
    ok=all(f32(w)==f32(v) for w,v in zip(want,got))
    print(f'RAY {n}: {"OK" if ok else "MISMATCH"}')
    if not ok:
        bad+=1
        for j,(w,v) in enumerate(zip(want,got),1):
            print(f'   {j}: want {w!r} got {v!r}{"" if f32(w)==f32(v) else "  <-- diff"}')
print('mismatches:',bad)
sys.exit(1 if bad else 0)
