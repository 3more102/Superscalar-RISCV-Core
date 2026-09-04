#!/usr/bin/env python3
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'reference_model'))
import riscv_encode as E
from rv32im_model import RV32IM

H=ROOT/'sw'/'hex'; H.mkdir(parents=True,exist_ok=True)
R=ROOT/'reports'/'simulation'; R.mkdir(parents=True,exist_ok=True)

programs={
'01_alu':[
 E.addi(1,0,5), E.addi(2,0,-3), E.add(3,1,2), E.sub(4,1,2),
 E.and_(5,1,2), E.or_(6,1,2), E.xor(7,1,2), E.slli(8,1,3),
 E.srli(9,2,1), E.srai(10,2,1), E.slt(11,2,1), E.sltu(12,2,1),
 E.slti(13,2,0), E.sltiu(14,1,6), E.andi(15,2,0xff), E.ori(16,1,0x40),
 E.xori(17,1,-1), E.lui(18,0x80000000), E.addi(19,0,-1), E.slli(20,19,31),
 E.slli(21,1,0), E.srl(22,19,1), E.sra(23,19,1),
 E.EBREAK],
'02_dual_issue':[
 E.addi(1,0,1), E.addi(2,0,2),
 E.addi(3,0,3), E.addi(4,0,4),
 E.add(10,1,2), E.xor(11,3,4),
 E.sub(12,4,1), E.or_(13,2,3),
 E.and_(14,10,13), E.sll(15,11,1),
 E.EBREAK],
'03_dependencies':[
 E.addi(1,0,10), E.addi(2,0,3),
 E.add(5,1,2), E.sub(6,5,2), E.xor(7,6,1), E.and_(8,7,5), E.or_(9,8,2),
 E.EBREAK],
'04_forwarding':[
 E.addi(1,0,7), E.addi(2,0,9),
 E.add(3,1,2), E.addi(20,0,1),
 E.sub(4,3,1), E.addi(21,0,2),
 E.xor(5,4,2), E.addi(22,0,3),
 E.EBREAK],
'05_branches':[
 E.addi(1,0,1), E.addi(2,0,1),
 E.beq(1,2,8), E.addi(3,0,99),
 E.addi(3,0,7), E.bne(1,2,8),
 E.addi(4,0,8), E.blt(0,1,8),
 E.addi(5,0,99), E.addi(5,0,5),
 E.bgeu(1,2,8), E.addi(6,0,99), E.addi(6,0,6),
 E.bge(2,1,8), E.addi(7,0,99), E.addi(7,0,7),
 E.bltu(1,2,8), E.addi(8,0,8),
 E.EBREAK],
'06_jumps':[
 E.jal(1,8), E.addi(3,0,99),
 E.addi(3,0,7), E.auipc(2,0), E.addi(2,2,12), E.jalr(4,2,0),
 E.addi(5,0,9), E.EBREAK],
'07_load_store':[
 E.addi(1,0,256), E.addi(2,0,-1), E.sw(2,1,0), E.lw(3,1,0),
 E.addi(4,0,0x7f), E.sb(4,1,4), E.lb(5,1,4), E.lbu(6,1,4),
 E.addi(7,0,-128), E.sb(7,1,5), E.lb(8,1,5), E.lbu(9,1,5),
 E.addi(10,0,-2), E.sh(10,1,6), E.lh(11,1,6), E.lhu(12,1,6),
 E.EBREAK],
'08_mul':[
 E.addi(1,0,-7), E.addi(2,0,9), E.mul(3,1,2), E.mulh(4,1,2),
 E.mulhsu(5,1,2), E.mulhu(6,1,2), E.EBREAK],
'09_div':[
 E.addi(1,0,-20), E.addi(2,0,3), E.div(3,1,2), E.rem(4,1,2),
 E.divu(5,1,2), E.remu(6,1,2), E.addi(7,0,0), E.div(8,1,7), E.rem(9,1,7),
 E.lui(10,0x80000000), E.addi(11,0,-1), E.div(12,10,11), E.rem(13,10,11), E.EBREAK],
'10_random_mix':[
 E.addi(1,0,12), E.addi(2,0,5), E.add(3,1,2), E.mul(4,1,2),
 E.xori(5,3,0x55), E.sub(6,4,2), E.slli(7,5,2), E.and_(8,6,7),
 E.addi(9,0,320), E.sw(8,9,0), E.lw(10,9,0), E.div(11,10,2), E.rem(12,10,2), E.EBREAK],
'11_stress_dependencies':[
 E.addi(1,0,2), E.addi(2,0,3), E.add(5,1,2), E.sub(6,5,2), E.xor(7,6,1),
 E.and_(8,7,5), E.or_(9,8,2), E.sll(10,9,1), E.slt(11,10,9), E.add(12,11,10), E.EBREAK],
'12_branch_flush':[
 E.addi(1,0,0), E.addi(2,0,5),
 E.addi(1,1,1), E.blt(1,2,-4),
 E.addi(3,0,42), E.beq(1,2,8), E.addi(4,0,99), E.addi(4,0,7), E.EBREAK]
,
'13_waw_pairing':[
 E.addi(5,0,1), E.addi(5,0,2), E.addi(6,0,3), E.addi(6,0,4), E.EBREAK],
'14_x0_invariant':[
 E.addi(0,0,123), E.lui(0,0x12345000), E.addi(1,0,7), E.add(0,1,1), E.addi(2,0,9), E.EBREAK],
'15_misaligned_load':[
 E.addi(1,0,257), E.lw(2,1,0), E.addi(3,0,99), E.EBREAK],
'16_misaligned_store':[
 E.addi(1,0,257), E.addi(2,0,0x55), E.sw(2,1,0), E.addi(3,0,99), E.EBREAK],
'17_ecall':[
 E.addi(1,0,17), E.ECALL, E.addi(2,0,99), E.EBREAK],
'18_illegal':[
 E.addi(1,0,18), 0xffffffff, E.addi(2,0,99), E.EBREAK],
'19_structural_replay':[
 E.addi(1,0,512), E.addi(2,0,0x34), E.sw(2,1,0),
 E.addi(3,0,1), E.lw(4,1,0),
 E.addi(5,0,5), E.mul(6,2,5),
 E.addi(7,0,7), E.beq(7,7,8), E.addi(8,0,99), E.addi(8,0,8), E.EBREAK],
'20_div_corner_unsigned':[
 E.addi(1,0,-1), E.addi(2,0,2), E.divu(3,1,2), E.remu(4,1,2),
 E.addi(5,0,0), E.divu(6,1,5), E.remu(7,1,5), E.EBREAK],
'21_branch_outcomes':[
 E.addi(1,0,1), E.addi(2,0,2),
 # BEQ taken / not-taken
 E.beq(1,1,8), E.addi(20,0,99), E.addi(20,0,1),
 E.beq(1,2,8), E.addi(21,0,2), E.addi(22,0,22),
 # BNE taken / not-taken
 E.bne(1,2,8), E.addi(20,0,99), E.addi(20,0,3),
 E.bne(1,1,8), E.addi(21,0,4), E.addi(22,0,22),
 # BLT taken / not-taken
 E.blt(1,2,8), E.addi(20,0,99), E.addi(20,0,5),
 E.blt(2,1,8), E.addi(21,0,6), E.addi(22,0,22),
 # BGE taken / not-taken
 E.bge(2,1,8), E.addi(20,0,99), E.addi(20,0,7),
 E.bge(1,2,8), E.addi(21,0,8), E.addi(22,0,22),
 # BLTU taken / not-taken
 E.bltu(1,2,8), E.addi(20,0,99), E.addi(20,0,9),
 E.bltu(2,1,8), E.addi(21,0,10), E.addi(22,0,22),
 # BGEU taken / not-taken
 E.bgeu(2,1,8), E.addi(20,0,99), E.addi(20,0,11),
 E.bgeu(1,2,8), E.addi(21,0,12), E.addi(22,0,22),
 E.EBREAK],
'22_forwarding_paths':[
 # EX forwarding: same-pair RAW forces slot1 replay, then consumes EX result.
 E.addi(1,0,5), E.add(2,1,0),
 # MEM forwarding: one lane0-special store delays the consumer one issue cycle.
 E.addi(3,0,7), E.sw(0,0,0), E.add(4,3,0),
 # WB forwarding: two lane0-special stores delay the consumer two issue cycles.
 E.addi(5,0,9), E.sw(0,0,4), E.sw(0,0,8), E.add(6,5,0),
 E.EBREAK],
'23_misaligned_jal':[
 E.jal(1,2), E.addi(2,0,99), E.EBREAK],
'24_misaligned_jalr':[
 E.addi(1,0,6), E.jalr(2,1,0), E.addi(3,0,99), E.EBREAK],
'25_misaligned_branch':[
 E.addi(1,0,1), E.beq(1,1,2), E.addi(2,0,99), E.EBREAK],
'26_precise_trap':[
 # All instructions after the illegal opcode are younger and must never commit
 # or create a memory side effect after the trap becomes architectural.
 E.addi(1,0,640), E.addi(2,0,0x5a), 0xffffffff,
 E.addi(3,0,99), E.sw(2,1,0), E.addi(4,0,77), E.EBREAK],
'27_illegal_jalr_funct3':[E.i_type(0,0,1,1,0x67), E.EBREAK],
'28_illegal_branch_funct3':[E.b_type(4,0,0,2), E.EBREAK],
'29_illegal_load_funct3':[E.i_type(0,0,3,1,0x03), E.EBREAK],
'30_illegal_store_funct3':[E.s_type(0,1,0,3,0x23), E.EBREAK],
'31_illegal_shift_encoding':[E.i_type((0x01<<5)|1,1,1,2,0x13), E.EBREAK],
'32_illegal_op_encoding':[E.r_type(0x10,2,1,0,3,0x33), E.EBREAK],
'33_illegal_system':[0x00200073, E.EBREAK],
'34_not_taken_misaligned_branch':[
 E.addi(1,0,1), E.bne(1,1,2), E.addi(2,0,34), E.EBREAK],
'35_jalr_bit0_clear':[
 E.addi(1,0,13), E.jalr(2,1,0), E.addi(3,0,99), E.addi(3,0,7), E.EBREAK],
'36_overflow_wrap':[
 E.lui(1,0x80000000), E.addi(2,1,-1), E.addi(3,2,1),
 E.add(4,2,2), E.addi(5,0,-1), E.sub(6,1,5), E.EBREAK],
'37_shift_mask':[
 E.addi(1,0,1), E.addi(2,0,32), E.sll(3,1,2),
 E.addi(4,0,63), E.sll(5,1,4), E.lui(6,0x80000000),
 E.sra(7,6,2), E.srl(8,6,4), E.sra(9,6,4), E.EBREAK],
'38_signed_unsigned_extremes':[
 E.lui(1,0x80000000), E.addi(2,0,-1), E.addi(7,0,1),
 E.slt(3,1,2), E.sltu(4,1,2), E.slt(5,2,1), E.sltu(6,2,1),
 E.blt(1,7,8), E.addi(8,0,99), E.addi(8,0,8),
 E.bltu(1,7,8), E.addi(9,0,9), E.EBREAK],
'39_byte_lanes':[
 E.addi(1,0,768), E.addi(2,0,0x11), E.sb(2,1,0),
 E.addi(3,0,0x22), E.sb(3,1,1), E.addi(4,0,0x33), E.sb(4,1,2),
 E.addi(5,0,0x80), E.sb(5,1,3), E.lw(6,1,0), E.lb(7,1,3), E.lbu(8,1,3), E.EBREAK],
'40_halfword_upper_lane':[
 E.addi(1,0,800), E.addi(2,0,0x123), E.sh(2,1,0),
 E.lui(3,0x00008000), E.addi(3,3,1), E.sh(3,1,2),
 E.lh(4,1,2), E.lhu(5,1,2), E.lw(6,1,0), E.EBREAK],
'41_mul_corners':[
 E.lui(1,0x80000000), E.addi(2,0,-1),
 E.mul(3,1,2), E.mulh(4,1,2), E.mulhu(5,1,2), E.mulhsu(6,1,2),
 E.mul(7,2,2), E.mulh(8,2,2), E.mulhu(9,2,2), E.mulhsu(10,2,2), E.EBREAK]

}

summary={}
for name,words in programs.items():
    path=H/f'{name}.hex'; E.write_hex(path,words)
    m=RV32IM(words).run()
    exp={
      'trap':m.trap,
      'trap_pc':f'0x{m.pc:08x}',
      'commits':len(m.commits),
      'regs':{f'x{i}':f'0x{v:08x}' for i,v in enumerate(m.regs) if v},
    }
    (H/f'{name}.expected.json').write_text(json.dumps(exp,indent=2))
    summary[name]=exp
print(f'Generated {len(programs)} directed programs in {H}')
print(json.dumps({k:{'commits':v['commits'],'trap':v['trap']} for k,v in summary.items()},indent=2))
