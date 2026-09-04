#!/usr/bin/env python3
"""Executable stimulus/architectural coverage over directed programs.

This is intentionally labelled REFERENCE/STIMULUS coverage. It proves that the
checked program corpus exercises required architectural situations, but it does
not replace simulator functional/code coverage of the SystemVerilog RTL.
"""
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
from rv32im_model import RV32IM, load_hex
from pipeline_model import simulate_dynamic

BR={0:'BEQ',1:'BNE',4:'BLT',5:'BGE',6:'BLTU',7:'BGEU'}
LOAD={0:'LB',1:'LH',2:'LW',4:'LBU',5:'LHU'}
STORE={0:'SB',1:'SH',2:'SW'}
MOPS={0:'MUL',1:'MULH',2:'MULHSU',3:'MULHU',4:'DIV',5:'DIVU',6:'REM',7:'REMU'}

branch={n:{'taken':0,'not_taken':0} for n in BR.values()}
loads={n:0 for n in LOAD.values()}
stores={n:0 for n in STORE.values()}
store_lanes={'SB_lane0':0,'SB_lane1':0,'SB_lane2':0,'SB_lane3':0,'SH_lane0':0,'SH_lane2':0}
mops={n:0 for n in MOPS.values()}
traps={n:0 for n in ['instruction_misaligned','breakpoint','illegal','load_misaligned','store_misaligned','ecall']}
issue={'dual_issue':0,'raw_block':0,'waw_block':0,'structural_block':0,'load_use_stall':0,'divider_stall':0,'redirect_bubble':0}
programs=0
illegal_variants={
 'jalr_funct3':False,'branch_funct3':False,'load_funct3':False,'store_funct3':False,
 'shift_encoding':False,'op_encoding':False,'system':False,
}

for hp in sorted((ROOT/'sw'/'hex').glob('[0-9][0-9]_*.hex')):
    m=RV32IM(load_hex(hp)).run(); programs += 1
    for tag in illegal_variants:
        if tag in hp.stem and m.trap=='illegal': illegal_variants[tag]=True
    if m.trap in traps: traps[m.trap]+=1
    cs=m.commits
    for i,c in enumerate(cs):
        ins=c.instr; opc=ins&0x7f; f3=(ins>>12)&7; f7=(ins>>25)&0x7f
        if opc==0x63 and f3 in BR:
            nxt=cs[i+1].pc if i+1<len(cs) else m.pc
            taken=nxt != ((c.pc+4)&0xffffffff)
            branch[BR[f3]]['taken' if taken else 'not_taken'] += 1
        elif opc==0x03 and f3 in LOAD:
            loads[LOAD[f3]] += 1
        elif opc==0x23 and f3 in STORE:
            stores[STORE[f3]] += 1
            if c.mem_write:
                lane=c.mem_addr & 3
                if f3==0:
                    store_lanes[f'SB_lane{lane}'] += 1
                elif f3==1 and lane in (0,2):
                    store_lanes[f'SH_lane{lane}'] += 1
        elif opc==0x33 and f7==1 and f3 in MOPS:
            mops[MOPS[f3]] += 1
    t=simulate_dynamic(m,enable_dual=True)
    issue['dual_issue'] += t.dual_issue_cycles
    issue['raw_block'] += t.raw_pair_blocks
    issue['waw_block'] += t.waw_pair_blocks
    issue['structural_block'] += t.structural_pair_blocks
    issue['load_use_stall'] += t.load_use_stalls
    issue['divider_stall'] += t.divider_stall_cycles
    issue['redirect_bubble'] += t.redirect_bubbles

checks={}
for n,v in branch.items():
    checks[f'{n}_taken']=v['taken']>0
    checks[f'{n}_not_taken']=v['not_taken']>0
for n,c in loads.items(): checks[f'load_{n}']=c>0
for n,c in stores.items(): checks[f'store_{n}']=c>0
for n,c in store_lanes.items(): checks[f'store_lane_{n}']=c>0
for n,c in mops.items(): checks[f'm_{n}']=c>0
for n,c in traps.items(): checks[f'trap_{n}']=c>0
for n,c in issue.items(): checks[f'issue_{n}']=c>0
for n,ok in illegal_variants.items(): checks[f'illegal_{n}']=ok

result={
 'label':'REFERENCE/STIMULUS COVERAGE — not RTL simulator functional/code coverage',
 'programs':programs,'branch_outcomes':branch,'loads':loads,'stores':stores,'store_lanes':store_lanes,'m_ops':mops,
 'traps':traps,'issue_model_events':issue,'illegal_reserved_encodings':illegal_variants,'checks':checks,
 'covered_points':sum(checks.values()),'total_points':len(checks),
 'all_required_points_covered':all(checks.values())
}
outdir=ROOT/'reports'/'coverage';outdir.mkdir(parents=True,exist_ok=True)
(outdir/'reference_functional_coverage.json').write_text(json.dumps(result,indent=2)+'\n')
md=['# Reference / Stimulus Functional Coverage','',
    '> This is executable architectural/stimulus coverage, **not RTL simulator code/functional coverage**.','',
    f'Programs analyzed: **{programs}**',f'Coverage points: **{result["covered_points"]}/{result["total_points"]}**','',
    '## Branch outcome matrix','', '| Branch | Taken | Not taken |','|---|---:|---:|']
for n,v in branch.items(): md.append(f'| {n} | {v["taken"]} | {v["not_taken"]} |')
md += ['', '## Load/store types','', 'Loads: '+', '.join(f'{k}={v}' for k,v in loads.items()),
       '', 'Stores: '+', '.join(f'{k}={v}' for k,v in stores.items()),
       '', 'Store byte-enable lanes: '+', '.join(f'{k}={v}' for k,v in store_lanes.items()),
       '', '## M extension','', ', '.join(f'{k}={v}' for k,v in mops.items()),
       '', '## Trap classes','', ', '.join(f'{k}={v}' for k,v in traps.items()),
       '', '## Reserved illegal encodings','', ', '.join(f'{k}={v}' for k,v in illegal_variants.items()),
       '', '## Superscalar timing-model event stimuli','', ', '.join(f'{k}={v}' for k,v in issue.items()),'']
(outdir/'reference_functional_coverage.md').write_text('\n'.join(md)+'\n')
print(f'REFERENCE/STIMULUS FUNCTIONAL COVERAGE: {result["covered_points"]}/{result["total_points"]} points')
for k,ok in checks.items(): print(f'{k:32s} {"COVERED" if ok else "MISSING"}')
raise SystemExit(0 if result['all_required_points_covered'] else 1)
