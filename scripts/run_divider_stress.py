#!/usr/bin/env python3
from pathlib import Path
import random, sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
from divider_algorithm import restoring, s32

PAIRS=5000
OPS=('div','divu','rem','remu')
rng=random.Random(0x5EED)
checked=0
for _ in range(PAIRS):
    a=rng.getrandbits(32); b=rng.getrandbits(32)
    for op in OPS:
        got=restoring(a,b,op,8)
        if b==0:
            exp=0xffffffff if op in ('div','divu') else a
        elif op in ('div','rem') and a==0x80000000 and b==0xffffffff:
            exp=0x80000000 if op=='div' else 0
        elif op=='divu':
            exp=a//b
        elif op=='remu':
            exp=a%b
        else:
            aa=s32(a); bb=s32(b)
            q=abs(aa)//abs(bb); q=-q if (aa<0)^(bb<0) else q
            exp=q if op=='div' else aa-q*bb
        if got!=(exp&0xffffffff):
            raise SystemExit(f'FAIL a=0x{a:08x} b=0x{b:08x} op={op} got=0x{got:08x} exp=0x{exp&0xffffffff:08x}')
        checked+=1
result={'operand_pairs':PAIRS,'operations_per_pair':len(OPS),'comparisons':checked,'seed':'0x5EED','status':'PASS'}
out=ROOT/'reports'/'simulation'/'divider_stress.json'; out.write_text(json.dumps(result,indent=2)+'\n')
print(f'DIVIDER ALGORITHM STRESS: {checked}/{PAIRS*len(OPS)} PASS')
