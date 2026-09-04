from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'reference_model'))
sys.path.insert(0,str(ROOT/'scripts'))
from rv32im_model import RV32IM, load_hex
from issue_model import can_pair, issue_cycles
import riscv_encode as E
from gen_random_program import program

def test_all_directed_reference_programs_end_at_expected_trap():
    files=sorted((ROOT/'sw'/'hex').glob('[0-9][0-9]_*.hex'))
    assert len(files)>=26
    for p in files:
        words=load_hex(p)
        m=RV32IM(words).run()
        exp=json.loads(p.with_suffix('.expected.json').read_text())
        assert m.trap==exp['trap'], p.stem
        assert m.pc==int(exp['trap_pc'],16), p.stem
        assert len(m.commits)==exp['commits'], p.stem
        assert m.regs[0]==0

def test_division_corner_cases():
    words=[E.lui(1,0x80000000),E.addi(2,0,-1),E.div(3,1,2),E.rem(4,1,2),E.addi(5,0,0),E.div(6,1,5),E.rem(7,1,5),E.EBREAK]
    m=RV32IM(words).run()
    assert m.regs[3]==0x80000000
    assert m.regs[4]==0
    assert m.regs[6]==0xFFFFFFFF
    assert m.regs[7]==0x80000000

def test_branch_and_wrong_path():
    words=[E.addi(1,0,1),E.beq(1,1,8),E.addi(2,0,99),E.addi(2,0,7),E.EBREAK]
    m=RV32IM(words).run()
    assert m.regs[2]==7

def test_signed_unsigned_loads():
    words=[E.addi(1,0,512),E.addi(2,0,-128),E.sb(2,1,0),E.lb(3,1,0),E.lbu(4,1,0),E.EBREAK]
    m=RV32IM(words).run()
    assert m.regs[3]==0xFFFFFF80
    assert m.regs[4]==0x80

def test_dual_issue_pair_rules():
    assert can_pair(E.addi(1,0,1),E.addi(2,0,2))
    assert not can_pair(E.addi(1,0,1),E.addi(2,1,2)) # RAW
    assert not can_pair(E.addi(1,0,1),E.addi(1,0,2)) # WAW
    assert not can_pair(E.lw(1,2,0),E.addi(3,0,1))  # lane0 special baseline

def test_issue_model_independent_reaches_two():
    words=[]
    for k in range(50): words += [E.addi(1,0,k),E.addi(2,0,k)]
    r=issue_cycles(words)
    assert r['issue_ipc']==2.0

def test_random_reference_20_seeds():
    for seed in range(1,21):
        m=RV32IM(program(seed,50)).run()
        assert m.trap=='breakpoint' and m.regs[0]==0

def test_jalr_clears_low_bit():
    # target computed as x1+1 -> 12, low bit cleared
    words=[E.addi(1,0,11),E.jalr(2,1,1),E.addi(3,0,99),E.addi(3,0,7),E.EBREAK]
    m=RV32IM(words).run()
    assert m.regs[2]==8 and m.regs[3]==7

def test_misaligned_word_access_traps():
    words=[E.addi(1,0,513),E.lw(2,1,0),E.EBREAK]
    m=RV32IM(words).run()
    assert m.trap=='load_misaligned'
    words=[E.addi(1,0,513),E.addi(2,0,1),E.sw(2,1,0),E.EBREAK]
    m=RV32IM(words).run()
    assert m.trap=='store_misaligned'

def test_illegal_instruction_is_defined_trap():
    m=RV32IM([0xFFFFFFFF,E.EBREAK]).run()
    assert m.trap=='illegal'


def test_misaligned_control_transfer_traps_at_source_pc():
    m=RV32IM([E.jal(1,2),E.EBREAK]).run()
    assert m.trap=='instruction_misaligned' and m.pc==0 and m.regs[1]==0
    m=RV32IM([E.addi(1,0,6),E.jalr(2,1,0),E.EBREAK]).run()
    assert m.trap=='instruction_misaligned' and m.pc==4 and m.regs[2]==0
    m=RV32IM([E.addi(1,0,1),E.beq(1,1,2),E.EBREAK]).run()
    assert m.trap=='instruction_misaligned' and m.pc==4


def test_precise_trap_blocks_younger_architectural_state():
    words=[E.addi(1,0,640),E.addi(2,0,0x5a),0xffffffff,E.addi(3,0,99),E.sw(2,1,0),E.addi(4,0,77),E.EBREAK]
    m=RV32IM(words).run()
    assert m.trap=='illegal' and m.pc==8
    assert m.regs[1]==640 and m.regs[2]==0x5a
    assert m.regs[3]==0 and m.regs[4]==0
    assert all(not c.mem_write for c in m.commits)


def test_not_taken_branch_with_misaligned_target_does_not_trap():
    m=RV32IM([E.addi(1,0,1),E.bne(1,1,2),E.addi(2,0,34),E.EBREAK]).run()
    assert m.trap=='breakpoint' and m.regs[2]==34


def test_jalr_clears_bit0_before_ialign_check():
    m=RV32IM([E.addi(1,0,13),E.jalr(2,1,0),E.addi(3,0,99),E.addi(3,0,7),E.EBREAK]).run()
    assert m.trap=='breakpoint' and m.regs[2]==8 and m.regs[3]==7
