from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'reference_model'))
sys.path.insert(0,str(ROOT/'scripts'))
from rv32im_model import RV32IM
from pipeline_model import simulate_dynamic
import riscv_encode as E


def run(words):
    return simulate_dynamic(RV32IM(words).run())


def test_independent_alu_dual_issue_visible():
    w=[]
    for k in range(20):
        w += [E.addi(1,0,k), E.addi(2,0,k+1)]
    w += [E.EBREAK]
    r=run(w)
    assert r.dual_issue_cycles >= 20
    assert r.raw_pair_blocks == 0


def test_same_pair_raw_replays_slot1():
    w=[E.addi(1,0,1),E.addi(2,1,2),E.addi(3,2,3),E.EBREAK]
    r=run(w)
    assert r.raw_pair_blocks >= 1
    assert r.dual_issue_cycles == 0


def test_load_use_adds_one_bubble():
    w=[E.addi(1,0,256),E.addi(2,0,7),E.sw(2,1,0),E.lw(3,1,0),E.add(4,3,2),E.EBREAK]
    r=run(w)
    assert r.load_use_stalls == 1


def test_taken_branch_adds_redirect_refill_bubbles():
    w=[E.addi(1,0,1),E.beq(1,1,8),E.addi(2,0,99),E.addi(2,0,7),E.EBREAK]
    r=run(w)
    assert r.mispredict_count == 1
    assert r.redirect_bubbles == 2


def test_not_taken_branch_no_redirect_bubbles():
    w=[E.addi(1,0,1),E.bne(1,1,8),E.addi(2,0,7),E.EBREAK]
    r=run(w)
    assert r.mispredict_count == 0
    assert r.redirect_bubbles == 0


def test_divider_blocks_front_end():
    w=[E.addi(1,0,20),E.addi(2,0,3),E.div(3,1,2),E.addi(4,0,9),E.EBREAK]
    r=run(w)
    assert r.divider_stall_cycles >= 8


def test_iterative_divider_algorithm_randomized():
    from divider_algorithm import restoring, s32
    import random
    rng=random.Random(0x5eed)
    for _ in range(5000):
        a=rng.getrandbits(32); b=rng.getrandbits(32)
        for op in ('div','divu','rem','remu'):
            got=restoring(a,b,op,8)
            if b==0:
                exp=0xffffffff if op in ('div','divu') else a
            elif op in ('div','rem') and a==0x80000000 and b==0xffffffff:
                exp=0x80000000 if op=='div' else 0
            elif op=='divu': exp=a//b
            elif op=='remu': exp=a%b
            else:
                aa=s32(a); bb=s32(b); q=abs(aa)//abs(bb); q=-q if (aa<0)^(bb<0) else q
                exp=(q if op=='div' else aa-q*bb)&0xffffffff
            assert got==(exp&0xffffffff), (hex(a),hex(b),op,hex(got),hex(exp&0xffffffff))


def test_frontend_replay_queue_random_stress_no_drop_or_duplicate():
    from frontend_replay_model import Frontend
    import random
    rng=random.Random(0xC0FFEE)
    f=Frontend(0)
    expected_pc=0
    issued_count=0
    redirects=0
    for cycle in range(50000):
        assert f.invariant()
        # Redirect only to aligned addresses and never issue in the same cycle,
        # matching redirect_valid -> stall0/stall1 in the RTL.
        if cycle>5 and rng.random()<0.002:
            target=(rng.randrange(0,4096)*4)&0xffffffff
            f.step(redirect=target)
            expected_pc=target
            redirects+=1
            continue
        if not f.buf_v0:
            got=f.step()
        else:
            do0=rng.random()<0.82
            do1=do0 and f.buf_v1 and rng.random()<0.55
            before0=f.buf_pc0; before1=f.buf_pc1
            got=f.step(issue0=do0,issue1=do1)
            if do0:
                assert before0==expected_pc
                expected_pc=(expected_pc+4)&0xffffffff
                issued_count+=1
            if do1:
                assert before1==expected_pc
                expected_pc=(expected_pc+4)&0xffffffff
                issued_count+=1
        assert f.invariant()
    assert issued_count>10000 and redirects>20


def test_arithmetic_wrap_and_variable_shift_corner_values():
    w=[E.lui(1,0x80000000),E.addi(2,1,-1),E.addi(3,2,1),E.add(4,2,2),
       E.addi(5,0,1),E.addi(6,0,32),E.sll(7,5,6),E.addi(8,0,63),E.sll(9,5,8),
       E.srl(10,1,8),E.sra(11,1,8),E.EBREAK]
    m=RV32IM(w).run()
    assert m.regs[2]==0x7fffffff
    assert m.regs[3]==0x80000000
    assert m.regs[4]==0xfffffffe
    assert m.regs[7]==1                 # shift amount 32 -> low 5 bits = 0
    assert m.regs[9]==0x80000000        # shift amount 63 -> 31
    assert m.regs[10]==1
    assert m.regs[11]==0xffffffff


def test_store_byte_lanes_and_upper_halfword_lane():
    w=[E.addi(1,0,768),E.addi(2,0,0x11),E.sb(2,1,0),E.addi(3,0,0x22),E.sb(3,1,1),
       E.addi(4,0,0x33),E.sb(4,1,2),E.addi(5,0,0x80),E.sb(5,1,3),E.lw(6,1,0),
       E.lb(7,1,3),E.lbu(8,1,3),E.EBREAK]
    m=RV32IM(w).run()
    assert m.regs[6]==0x80332211
    assert m.regs[7]==0xffffff80 and m.regs[8]==0x80

    w=[E.addi(1,0,800),E.addi(2,0,0x123),E.sh(2,1,0),E.lui(3,0x00008000),
       E.addi(3,3,1),E.sh(3,1,2),E.lh(4,1,2),E.lhu(5,1,2),E.lw(6,1,0),E.EBREAK]
    m=RV32IM(w).run()
    assert m.regs[4]==0xffff8001 and m.regs[5]==0x00008001
    assert m.regs[6]==0x80010123


def test_multiply_high_word_corner_values():
    w=[E.lui(1,0x80000000),E.addi(2,0,-1),E.mul(3,1,2),E.mulh(4,1,2),
       E.mulhu(5,1,2),E.mulhsu(6,1,2),E.mulh(7,2,2),E.mulhu(8,2,2),E.mulhsu(9,2,2),E.EBREAK]
    m=RV32IM(w).run()
    assert m.regs[3]==0x80000000
    assert m.regs[4]==0x00000000
    assert m.regs[5]==0x7fffffff
    assert m.regs[6]==0x80000000
    assert m.regs[7]==0x00000000
    assert m.regs[8]==0xfffffffe
    assert m.regs[9]==0xffffffff
