#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import riscv_encode as E
OUT=ROOT/'sw'/'perf'; OUT.mkdir(parents=True,exist_ok=True)
# 200 independent simple ALU instructions. Registers may repeat across distant
# instructions, but each adjacent pair is independent and lane1-eligible.
ind=[]
for k in range(100):
    r0=1+(2*k)%30; r1=1+(2*k+1)%30
    ind += [E.addi(r0,0,(k&0x7ff)), E.xori(r1,0,(k*3)&0x7ff)]
ind.append(E.EBREAK)
E.write_hex(OUT/'independent_200.hex',ind)
# Strict RAW chain: no adjacent pair may dual issue.
dep=[E.addi(1,0,1)]
for _ in range(99): dep.append(E.addi(1,1,1))
dep.append(E.EBREAK)
E.write_hex(OUT/'dependency_100.hex',dep)
print(f'Generated {OUT/"independent_200.hex"} and {OUT/"dependency_100.hex"}')
