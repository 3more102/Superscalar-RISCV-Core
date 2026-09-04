#!/usr/bin/env python3
"""Aggregate actual RTL simulation coverage evidence from directed runs.

Requires successful RTL traces/status/coverage files produced by
run_rtl_regression.py. Unlike reference_functional_coverage.py, this gate is
intended to be RTL evidence and therefore refuses to run without an HDL
simulator in the environment.
"""
from pathlib import Path
import csv, json, shutil
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports'/'simulation'
COVDIR=ROOT/'reports'/'coverage'

if not (shutil.which('verilator') or (shutil.which('iverilog') and shutil.which('vvp'))):
    out=COVDIR/'rtl_functional_coverage.md'
    out.write_text('# RTL Functional Coverage\n\n**TOOL UNAVAILABLE** — requires executed Verilator/Icarus RTL regression.\n')
    print('RTL FUNCTIONAL COVERAGE: TOOL UNAVAILABLE')
    raise SystemExit(2)

BR={0:'BEQ',1:'BNE',4:'BLT',5:'BGE',6:'BLTU',7:'BGEU'}
LOAD={0:'LB',1:'LH',2:'LW',4:'LBU',5:'LHU'}
STORE={0:'SB',1:'SH',2:'SW'}
MOPS={0:'MUL',1:'MULH',2:'MULHSU',3:'MULHU',4:'DIV',5:'DIVU',6:'REM',7:'REMU'}
TRAP={0:'instruction_misaligned',2:'illegal',3:'breakpoint',4:'load_misaligned',6:'store_misaligned',11:'ecall'}
branch={n:{'taken':0,'not_taken':0} for n in BR.values()}
loads={n:0 for n in LOAD.values()}; stores={n:0 for n in STORE.values()}; mops={n:0 for n in MOPS.values()}
store_lanes={'SB_lane0':0,'SB_lane1':0,'SB_lane2':0,'SB_lane3':0,'SH_lane0':0,'SH_lane2':0}
illegal_variants={k:False for k in ['jalr_funct3','branch_funct3','load_funct3','store_funct3','shift_encoding','op_encoding','system']}
traps={n:0 for n in TRAP.values()}
events={k:0 for k in ['dual_issue','single_issue','pair_raw','pair_waw','structural_block','redirect','forward_ex','forward_mem','forward_wb','load_use_stall','divider_stall']}

def kv(path):
    d={}
    for line in path.read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1); d[k.strip()]=v.strip()
    return d

def commits(path):
    rows=[]
    with path.open(newline='') as f:
        for r in csv.DictReader(f):
            rows.append({'pc':int(r['pc'],16),'instr':int(r['instr'],16),'mem_we':bool(int(r['mem_we'])),'mem_addr':int(r['mem_addr'],16)})
    return rows

hexes=sorted((ROOT/'sw'/'hex').glob('[0-9][0-9]_*.hex'))
missing=[]
for hp in hexes:
    name=hp.stem
    tp=REPORT/f'{name}_trace.csv'; sp=REPORT/f'{name}_status.txt'; cp=COVDIR/f'{name}_coverage.txt'
    if not tp.exists() or not sp.exists() or not cp.exists():
        missing.append(name); continue
    st=kv(sp); cv=kv(cp); cs=commits(tp)
    cause=int(st['trap_cause'],0)
    if cause in TRAP: traps[TRAP[cause]]+=1
    if cause==2:
        for tag in illegal_variants:
            if tag in name: illegal_variants[tag]=True
    trap_pc=int(st['trap_pc'],16)
    for i,c in enumerate(cs):
        ins=c['instr']; opc=ins&0x7f; f3=(ins>>12)&7; f7=(ins>>25)&0x7f
        if opc==0x63 and f3 in BR:
            next_pc=cs[i+1]['pc'] if i+1<len(cs) else trap_pc
            taken=next_pc != ((c['pc']+4)&0xffffffff)
            branch[BR[f3]]['taken' if taken else 'not_taken'] += 1
        elif opc==0x03 and f3 in LOAD: loads[LOAD[f3]]+=1
        elif opc==0x23 and f3 in STORE:
            stores[STORE[f3]]+=1
            if c['mem_we']:
                lane=c['mem_addr'] & 3
                if f3==0: store_lanes[f'SB_lane{lane}']+=1
                elif f3==1 and lane in (0,2): store_lanes[f'SH_lane{lane}']+=1
        elif opc==0x33 and f7==1 and f3 in MOPS: mops[MOPS[f3]]+=1
    for k in ['dual_issue','single_issue','pair_raw','pair_waw','structural_block','redirect','forward_ex','forward_mem','forward_wb']:
        events[k]+=int(cv.get(k,'0'),0)
    events['load_use_stall']+=int(st.get('load_use_stalls','0'),0)
    events['divider_stall']+=int(st.get('divider_stalls','0'),0)

if missing:
    print('RTL FUNCTIONAL COVERAGE: missing regression outputs for '+', '.join(missing))
    raise SystemExit(1)

checks={}
for n,v in branch.items():
    checks[f'{n}_taken']=v['taken']>0; checks[f'{n}_not_taken']=v['not_taken']>0
for n,c in loads.items(): checks[f'load_{n}']=c>0
for n,c in stores.items(): checks[f'store_{n}']=c>0
for n,c in store_lanes.items(): checks[f'store_lane_{n}']=c>0
for n,c in mops.items(): checks[f'm_{n}']=c>0
for n,c in traps.items(): checks[f'trap_{n}']=c>0
for n,c in events.items(): checks[f'event_{n}']=c>0
for n,ok in illegal_variants.items(): checks[f'illegal_{n}']=ok

result={'label':'RTL SIMULATION FUNCTIONAL COVERAGE','directed_programs':len(hexes),
        'branch_outcomes':branch,'loads':loads,'stores':stores,'store_lanes':store_lanes,'m_ops':mops,'traps':traps,'events':events,'illegal_reserved_encodings':illegal_variants,
        'covered_points':sum(checks.values()),'total_points':len(checks),'checks':checks,
        'all_required_points_covered':all(checks.values())}
(COVDIR/'rtl_functional_coverage.json').write_text(json.dumps(result,indent=2)+'\n')
md=['# RTL Simulation Functional Coverage','',f'Directed programs: **{len(hexes)}**  ',
    f'Coverage points: **{result["covered_points"]}/{result["total_points"]}**','',
    '| Branch | Taken | Not taken |','|---|---:|---:|']
for n,v in branch.items(): md.append(f'| {n} | {v["taken"]} | {v["not_taken"]} |')
md += ['', 'Loads: '+', '.join(f'{k}={v}' for k,v in loads.items()),
       '', 'Stores: '+', '.join(f'{k}={v}' for k,v in stores.items()),
       '', 'Store lanes: '+', '.join(f'{k}={v}' for k,v in store_lanes.items()),
       '', 'M ops: '+', '.join(f'{k}={v}' for k,v in mops.items()),
       '', 'Traps: '+', '.join(f'{k}={v}' for k,v in traps.items()),
       '', 'Events: '+', '.join(f'{k}={v}' for k,v in events.items()),
       '', 'Reserved illegal encodings: '+', '.join(f'{k}={v}' for k,v in illegal_variants.items()),'']
(COVDIR/'rtl_functional_coverage.md').write_text('\n'.join(md)+'\n')
print(f'RTL FUNCTIONAL COVERAGE: {result["covered_points"]}/{result["total_points"]} points')
for k,ok in checks.items(): print(f'{k:34s} {"COVERED" if ok else "MISSING"}')
raise SystemExit(0 if result['all_required_points_covered'] else 1)
