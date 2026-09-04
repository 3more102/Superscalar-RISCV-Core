#!/usr/bin/env python3
"""Cycle-oriented performance / issue model for the baseline 2-wide core.

This model intentionally mirrors the documented conservative microarchitecture:
* two-entry fetch/replay buffer
* lane1 supports only simple ALU/LUI/AUIPC
* same-pair RAW/WAW is blocked
* EX/MEM/WB forwarding removes ordinary inter-cycle ALU stalls
* a dependent consumer waits one extra cycle behind an EX load
* DIV/REM blocks EX for DIV_LATENCY and a dependent consumer waits one more cycle
* taken branch/JAL/JALR uses static-not-taken and incurs the RTL front-end redirect refill

It is an independent executable timing model, NOT a SystemVerilog simulation result.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

MASK32=0xFFFFFFFF
EBREAK=0x00100073

@dataclass
class Meta:
    pc:int
    instr:int
    rs1:int=0
    rs2:int=0
    rd:int=0
    rs1_used:bool=False
    rs2_used:bool=False
    rd_write:bool=False
    lane1:bool=False
    special:bool=True
    is_load:bool=False
    is_store:bool=False
    is_branch:bool=False
    is_jal:bool=False
    is_jalr:bool=False
    is_div:bool=False
    is_mul:bool=False
    is_system:bool=False
    illegal:bool=False

    def depends_on(self, rd:int)->bool:
        if rd==0:
            return False
        return (self.rs1_used and self.rs1==rd) or (self.rs2_used and self.rs2==rd)


def decode_meta(pc:int, ins:int)->Meta:
    opc=ins & 0x7f
    rd=(ins>>7)&31; f3=(ins>>12)&7; rs1=(ins>>15)&31; rs2=(ins>>20)&31; f7=(ins>>25)&0x7f
    m=Meta(pc=pc,instr=ins,rs1=rs1,rs2=rs2,rd=rd,illegal=False)

    if opc in (0x37,0x17): # LUI/AUIPC
        m.rd_write=True; m.lane1=True; m.special=False
    elif opc==0x13: # OP-IMM
        legal = f3 in (0,2,3,4,6,7) or (f3==1 and f7==0) or (f3==5 and f7 in (0,0x20))
        m.rs1_used=True; m.rd_write=True; m.lane1=legal; m.special=not legal; m.illegal=not legal
    elif opc==0x33: # OP/M
        m.rs1_used=m.rs2_used=m.rd_write=True
        if f7==0x01 and f3 in range(8):
            m.special=True
            if f3 in (0,1,2,3): m.is_mul=True
            else: m.is_div=True
        else:
            legal=(f7==0 and f3 in range(8)) or (f7==0x20 and f3 in (0,5))
            m.lane1=legal; m.special=not legal; m.illegal=not legal
    elif opc==0x03:
        legal=f3 in (0,1,2,4,5)
        m.rs1_used=True; m.rd_write=True; m.is_load=True; m.special=True; m.illegal=not legal
    elif opc==0x23:
        legal=f3 in (0,1,2)
        m.rs1_used=m.rs2_used=True; m.is_store=True; m.special=True; m.illegal=not legal
    elif opc==0x63:
        legal=f3 in (0,1,4,5,6,7)
        m.rs1_used=m.rs2_used=True; m.is_branch=True; m.special=True; m.illegal=not legal
    elif opc==0x6f:
        m.rd_write=True; m.is_jal=True; m.special=True
    elif opc==0x67:
        legal=f3==0
        m.rs1_used=True; m.rd_write=True; m.is_jalr=True; m.special=True; m.illegal=not legal
    elif opc==0x73:
        legal=ins in (0x00000073,0x00100073)
        m.is_system=True; m.special=True; m.illegal=not legal
    else:
        m.special=True; m.illegal=True
    return m


def pair_reason(a:Meta,b:Meta)->str:
    if b.pc != ((a.pc+4)&MASK32):
        return 'structural'
    if a.rd_write and a.rd:
        if b.depends_on(a.rd): return 'raw'
        if b.rd_write and b.rd and b.rd==a.rd: return 'waw'
    if a.special or not a.lane1 or b.special or not b.lane1:
        return 'structural'
    return 'pair'

@dataclass
class TimingResult:
    retired:int=0
    total_cycles:int=0
    issue_events:int=0
    dual_issue_cycles:int=0
    single_issue_cycles:int=0
    no_issue_cycles:int=0
    raw_pair_blocks:int=0
    waw_pair_blocks:int=0
    structural_pair_blocks:int=0
    load_use_stalls:int=0
    divider_stall_cycles:int=0
    redirect_bubbles:int=0
    branch_count:int=0
    mispredict_count:int=0
    issue_ipc:float=0.0
    pipeline_ipc:float=0.0


def build_dynamic_stream(model)->list[Meta]:
    stream=[decode_meta(c.pc,c.instr) for c in model.commits]
    # Architectural traps do not retire, but the trapping instruction still flows
    # through the RTL pipeline and determines halt latency.
    if model.halted:
        stream.append(decode_meta(model.pc, model.fetch()))
    return stream


def simulate_dynamic(model, div_latency:int=8, enable_dual:bool=True)->TimingResult:
    stream=build_dynamic_stream(model)
    retired=len(model.commits)
    if not stream:
        return TimingResult(retired=retired)

    # Cycle 1 fills the initially empty two-entry fetch buffer; first issue can
    # occur at cycle 2.  Cycle indices are aligned to perf_cycles semantics.
    cycle=2
    i=0
    dual=single=noissue=rawb=wawb=structb=loadst=divst=redirb=brcnt=misp=0
    last_load_issue=-10**9; last_load_rd=0
    div_release_cycle=-1; div_rd=0; div_dependent_extra_cycle=-1

    while i < len(stream):
        cur=stream[i]
        cur_is_trap = model.halted and (i == len(stream)-1)

        # Blocking divider owns EX. An independent instruction can issue on the
        # release cycle; a consumer of the DIV result waits one more cycle because
        # the RTL conservatively treats the DIV in EX as a source-wait hazard.
        if cycle < div_release_cycle:
            noissue += 1; divst += 1; cycle += 1; continue
        if cycle == div_release_cycle and cur.depends_on(div_rd):
            noissue += 1; divst += 1; cycle += 1
            div_release_cycle=-1; div_rd=0
            continue
        if cycle >= div_release_cycle and div_release_cycle >= 0:
            div_release_cycle=-1; div_rd=0

        # One-cycle load-use stall. Independent instructions are allowed through.
        if cycle == last_load_issue + 1 and cur.depends_on(last_load_rd):
            noissue += 1; loadst += 1; cycle += 1
            continue

        nxt=stream[i+1] if i+1 < len(stream) else None
        reason=pair_reason(cur,nxt) if nxt is not None else 'structural'
        pair=(enable_dual and nxt is not None and reason=='pair')
        if pair:
            dual += 1; i += 2
        else:
            single += 1; i += 1
            if nxt is not None:
                if reason=='raw': rawb += 1
                elif reason=='waw': wawb += 1
                elif reason=='structural': structb += 1

        issue_cycle=cycle

        if cur.is_load and cur.rd_write and cur.rd:
            last_load_issue=issue_cycle; last_load_rd=cur.rd
        else:
            # Keep prior load tag only for its immediately following cycle.
            if issue_cycle > last_load_issue + 1:
                last_load_rd=0

        if cur.is_div:
            # Derived from div_unit + core control: with LATENCY=N, an independent
            # younger instruction can issue N+2 cycles after the DIV issue edge.
            div_release_cycle=issue_cycle + div_latency + 2
            div_rd=cur.rd if cur.rd_write else 0

        if (cur.is_branch or cur.is_jal or cur.is_jalr) and not cur_is_trap:
            brcnt += 1
            # The reference dynamic path tells us whether a conditional branch
            # redirected. JAL/JALR always redirect under static-not-taken.
            next_pc = stream[i].pc if i < len(stream) else None
            redirect = cur.is_jal or cur.is_jalr or (cur.is_branch and next_pc is not None and next_pc != ((cur.pc+4)&MASK32))
            if redirect:
                misp += 1
                # After branch issue: one cycle resolving/clearing, one cycle to
                # refill the empty buffer; target can issue on the third cycle.
                noissue += 2; redirb += 2; cycle += 3
                continue

        cycle += 1

    # Trapping EBREAK/ECALL becomes visible in WB and sets halted three cycles
    # after its issue edge in this pipeline. Since cycle points one past the last
    # issue for the ordinary case, add two more cycles => final_issue + 3.
    total_cycles=cycle + 2
    events=dual+single
    issue_instr=retired # architectural instructions only for comparable IPC
    return TimingResult(
        retired=retired,total_cycles=total_cycles,issue_events=events,
        dual_issue_cycles=dual,single_issue_cycles=single,no_issue_cycles=noissue,
        raw_pair_blocks=rawb,waw_pair_blocks=wawb,structural_pair_blocks=structb,
        load_use_stalls=loadst,divider_stall_cycles=divst,redirect_bubbles=redirb,
        branch_count=brcnt,mispredict_count=misp,
        issue_ipc=(retired/events if events else 0.0),
        pipeline_ipc=(retired/total_cycles if total_cycles else 0.0)
    )


def as_dict(r:TimingResult):
    return asdict(r)
