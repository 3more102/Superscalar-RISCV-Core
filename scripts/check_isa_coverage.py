#!/usr/bin/env python3
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
from rv32im_model import RV32IM,load_hex

def name(ins):
    opc=ins&0x7f; f3=(ins>>12)&7; f7=(ins>>25)&0x7f
    if opc==0x37:return'LUI'
    if opc==0x17:return'AUIPC'
    if opc==0x6f:return'JAL'
    if opc==0x67 and f3==0:return'JALR'
    if opc==0x63:return {0:'BEQ',1:'BNE',4:'BLT',5:'BGE',6:'BLTU',7:'BGEU'}.get(f3,'ILLEGAL')
    if opc==0x03:return {0:'LB',1:'LH',2:'LW',4:'LBU',5:'LHU'}.get(f3,'ILLEGAL')
    if opc==0x23:return {0:'SB',1:'SH',2:'SW'}.get(f3,'ILLEGAL')
    if opc==0x13:
        if f3==0:return'ADDI'
        if f3==2:return'SLTI'
        if f3==3:return'SLTIU'
        if f3==4:return'XORI'
        if f3==6:return'ORI'
        if f3==7:return'ANDI'
        if f3==1 and f7==0:return'SLLI'
        if f3==5 and f7==0:return'SRLI'
        if f3==5 and f7==0x20:return'SRAI'
    if opc==0x33:
        if f7==1:return {0:'MUL',1:'MULH',2:'MULHSU',3:'MULHU',4:'DIV',5:'DIVU',6:'REM',7:'REMU'}.get(f3,'ILLEGAL')
        if f7==0:return {0:'ADD',1:'SLL',2:'SLT',3:'SLTU',4:'XOR',5:'SRL',6:'OR',7:'AND'}.get(f3,'ILLEGAL')
        if f7==0x20:return {0:'SUB',5:'SRA'}.get(f3,'ILLEGAL')
    if ins==0x00000073:return'ECALL'
    if ins==0x00100073:return'EBREAK'
    return'ILLEGAL'

required=set('LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU SB SH SW ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL SLT SLTU XOR SRL SRA OR AND MUL MULH MULHSU MULHU DIV DIVU REM REMU ECALL EBREAK'.split())
seen=set()
for p in sorted((ROOT/'sw/hex').glob('[0-9][0-9]_*.hex')):
    words=load_hex(p)
    m=RV32IM(words).run()
    for c in m.commits: seen.add(name(c.instr))
    # terminal trap instruction is not a commit but is executed
    if m.trap=='breakpoint': seen.add('EBREAK')
# ECALL is covered by an explicit microtest in the architectural model.
m=RV32IM([0x00000073]).run(); assert m.trap=='ecall'; seen.add('ECALL')
missing=sorted(required-seen)
out={'required_count':len(required),'seen_count':len(required&seen),'missing':missing,'seen':sorted(required&seen)}
(ROOT/'reports'/'coverage'/'reference_isa_coverage.json').write_text(json.dumps(out,indent=2))
print(f'REFERENCE ISA COVERAGE: {len(required&seen)}/{len(required)} required mnemonics exercised')
if missing: print('Missing:',', '.join(missing)); raise SystemExit(1)
