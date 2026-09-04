#!/usr/bin/env python3
"""Generate deterministic legal RV32IM stress programs (straight-line + memory)."""
from pathlib import Path
import argparse, random, sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'reference_model'))
import riscv_encode as E
from rv32im_model import RV32IM

OPS=['add','sub','xor','or','and','sll','srl','sra','slt','sltu','addi','xori','ori','andi','mul','div','rem']

def program(seed:int, n:int=120):
    r=random.Random(seed)
    w=[E.addi(28,0,1024), E.addi(1,0,1), E.addi(2,0,3), E.addi(3,0,-7)]
    for i in range(n):
        op=r.choice(OPS)
        rd=r.randint(4,27)
        # Inject dependency chains regularly; otherwise choose broad sources.
        if i % 5 == 0:
            rs1=max(1, rd-1)
        else:
            rs1=r.randint(1,27)
        rs2=r.randint(1,27)
        if op=='add': w.append(E.add(rd,rs1,rs2))
        elif op=='sub': w.append(E.sub(rd,rs1,rs2))
        elif op=='xor': w.append(E.xor(rd,rs1,rs2))
        elif op=='or': w.append(E.or_(rd,rs1,rs2))
        elif op=='and': w.append(E.and_(rd,rs1,rs2))
        elif op=='sll': w.append(E.sll(rd,rs1,rs2))
        elif op=='srl': w.append(E.srl(rd,rs1,rs2))
        elif op=='sra': w.append(E.sra(rd,rs1,rs2))
        elif op=='slt': w.append(E.slt(rd,rs1,rs2))
        elif op=='sltu': w.append(E.sltu(rd,rs1,rs2))
        elif op=='addi': w.append(E.addi(rd,rs1,r.randint(-128,127)))
        elif op=='xori': w.append(E.xori(rd,rs1,r.randint(-128,127)))
        elif op=='ori': w.append(E.ori(rd,rs1,r.randint(-128,127)))
        elif op=='andi': w.append(E.andi(rd,rs1,r.randint(-128,127)))
        elif op=='mul': w.append(E.mul(rd,rs1,rs2))
        elif op=='div': w.append(E.div(rd,rs1,rs2))
        elif op=='rem': w.append(E.rem(rd,rs1,rs2))
        if i % 17 == 0:
            off=(i % 8)*4
            w += [E.sw(rd,28,off), E.lw((rd % 24)+4,28,off)]
    w.append(E.EBREAK)
    return w

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=1); ap.add_argument('--count',type=int,default=120); ap.add_argument('--out'); args=ap.parse_args()
    words=program(args.seed,args.count)
    out=Path(args.out) if args.out else ROOT/'sw'/'hex'/f'random_seed_{args.seed}.hex'
    E.write_hex(out,words)
    m=RV32IM(words).run(max_steps=100000)
    meta={'seed':args.seed,'instructions_committed':len(m.commits),'trap':m.trap,'nonzero_regs':{f'x{i}':f'0x{x:08x}' for i,x in enumerate(m.regs) if x}}
    out.with_suffix('.expected.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))
if __name__=='__main__': main()
