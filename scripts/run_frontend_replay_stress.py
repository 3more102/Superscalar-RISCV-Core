#!/usr/bin/env python3
from pathlib import Path
import random,sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
from frontend_replay_model import Frontend

CYCLES=100000
rng=random.Random(0xC0FFEE)
f=Frontend(0); expected=0; issued=0; dual=0; single=0; redirects=0; idle=0
for cycle in range(CYCLES):
    if not f.invariant(): raise SystemExit(f'FAIL invariant before cycle {cycle}')
    if cycle>5 and rng.random()<0.002:
        target=(rng.randrange(0,16384)*4)&0xffffffff
        f.step(redirect=target); expected=target; redirects+=1
        continue
    if not f.buf_v0:
        f.step(); idle+=1
    else:
        do0=rng.random()<0.82
        do1=do0 and f.buf_v1 and rng.random()<0.55
        b0,b1=f.buf_pc0,f.buf_pc1
        got=f.step(issue0=do0,issue1=do1)
        exp=[]
        if do0:
            if b0!=expected: raise SystemExit(f'FAIL slot0 cycle={cycle} got=0x{b0:x} exp=0x{expected:x}')
            exp.append(expected); expected=(expected+4)&0xffffffff; issued+=1
        if do1:
            if b1!=expected: raise SystemExit(f'FAIL slot1 cycle={cycle} got=0x{b1:x} exp=0x{expected:x}')
            exp.append(expected); expected=(expected+4)&0xffffffff; issued+=1
        if got!=exp: raise SystemExit(f'FAIL emitted sequence cycle={cycle} got={got} exp={exp}')
        if do1: dual+=1
        elif do0: single+=1
        else: idle+=1
    if not f.invariant(): raise SystemExit(f'FAIL invariant after cycle {cycle}')
result={'cycles':CYCLES,'issued_instructions':issued,'dual_issue_cycles':dual,'single_issue_cycles':single,'redirects':redirects,'idle_or_refill_cycles':idle,'seed':'0xC0FFEE','status':'PASS'}
out=ROOT/'reports'/'simulation'/'frontend_replay_stress.json'; out.write_text(json.dumps(result,indent=2)+'\n')
print(f'FRONT-END REPLAY STRESS: {CYCLES}/{CYCLES} cycles PASS; issued={issued} redirects={redirects}')
