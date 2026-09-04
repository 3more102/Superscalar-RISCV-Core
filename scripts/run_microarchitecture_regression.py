#!/usr/bin/env python3
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
sys.path.insert(0,str(ROOT/'scripts'))
from rv32im_model import RV32IM, load_hex
from pipeline_model import simulate_dynamic, as_dict
from gen_random_program import program

outdir=ROOT/'reports'/'performance'; outdir.mkdir(parents=True,exist_ok=True)
rows=[]
for hp in sorted((ROOT/'sw'/'hex').glob('[0-9][0-9]_*.hex')):
    m=RV32IM(load_hex(hp)).run()
    dual=simulate_dynamic(m, enable_dual=True)
    single=simulate_dynamic(m, enable_dual=False)
    rows.append((hp.stem,dual,single))

# Stress many deterministic generated programs. This validates that the timing
# model terminates over a broad mix of RAW, memory and M-extension cases.
random_results=[]
random_speedups=[]
for seed in range(1,501):
    m=RV32IM(program(seed,120)).run()
    dual=simulate_dynamic(m, enable_dual=True)
    single=simulate_dynamic(m, enable_dual=False)
    assert dual.retired==len(m.commits)
    assert single.retired==len(m.commits)
    assert dual.total_cycles>0 and 0.0 <= dual.pipeline_ipc <= 2.0
    assert single.total_cycles>0 and 0.0 <= single.pipeline_ipc <= 1.0
    random_results.append(dual)
    random_speedups.append(single.total_cycles/dual.total_cycles)

report=[]
report.append('# Executable Microarchitecture Timing Model\n')
report.append('**Important:** these are cycle-model results, not SystemVerilog simulation measurements.\n')
report.append('| Program | Retired | Single cycles(model) | 2-wide cycles(model) | Speedup(model) | IPC(model) | Dual cycles | Load stalls | DIV stalls | Redirect bubbles |')
report.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for name,dual,single in rows:
    speedup=single.total_cycles/dual.total_cycles
    report.append(f'| {name} | {dual.retired} | {single.total_cycles} | {dual.total_cycles} | {speedup:.3f}x | {dual.pipeline_ipc:.3f} | {dual.dual_issue_cycles} | {dual.load_use_stalls} | {dual.divider_stall_cycles} | {dual.redirect_bubbles} |')
avg=sum(r.pipeline_ipc for r in random_results)/len(random_results)
avg_speedup=sum(random_speedups)/len(random_speedups)
report.append(f'\nRandom stress: **500/500 timing-model runs completed**, mean 2-wide model IPC **{avg:.3f}**, mean speedup over forced single-issue model **{avg_speedup:.3f}x**.')
(outdir/'microarchitecture_timing_model.md').write_text('\n'.join(report)+'\n')
(outdir/'microarchitecture_timing_model.json').write_text(json.dumps({
    'directed':{
        n:{'dual':as_dict(d),'single':as_dict(s),'speedup_model':s.total_cycles/d.total_cycles}
        for n,d,s in rows
    },
    'random_seeds':len(random_results),
    'random_mean_pipeline_ipc':avg,
    'random_mean_speedup_vs_single_model':avg_speedup,
    'disclaimer':'Executable timing model only; not RTL simulation.'
},indent=2))
for n,d,s in rows:
    print(f'{n:28s} retired={d.retired:4d} single={s.total_cycles:4d} dual={d.total_cycles:4d} speedup={s.total_cycles/d.total_cycles:.3f}x IPC={d.pipeline_ipc:.3f}')
print(f'RANDOM TIMING MODEL: {len(random_results)}/{len(random_results)} completed, mean IPC={avg:.3f}, mean speedup={avg_speedup:.3f}x')
