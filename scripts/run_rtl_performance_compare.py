#!/usr/bin/env python3
from pathlib import Path
import shutil,subprocess,sys,re
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports'/'performance'; REPORT.mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,'scripts/gen_perf_programs.py'],cwd=ROOT,check=True)
files=[str(ROOT/l.strip()) for l in (ROOT/'sim/filelist.f').read_text().splitlines() if l.strip()]
verilator=shutil.which('verilator'); iverilog=shutil.which('iverilog'); vvp=shutil.which('vvp')
if not verilator and not (iverilog and vvp):
    text='# RTL Performance Comparison\n\nRTL PERFORMANCE: TOOL UNAVAILABLE (requires Verilator or Icarus).\n'
    (REPORT/'rtl_performance_comparison.md').write_text(text); print(text,end=''); raise SystemExit(2)

def build(dual:bool):
    tag='dual' if dual else 'single'
    if verilator:
        obj=ROOT/'sim'/f'obj_perf_{tag}'
        cmd=[verilator,'--binary','--timing','--assert','-Wall','-Wno-fatal','--top-module','tb_superscalar_core',
             f'-GDUAL_ENABLE={1 if dual else 0}','--Mdir',str(obj),*files]
        cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        (REPORT/f'rtl_perf_compile_{tag}.log').write_text(cp.stdout+cp.stderr)
        if cp.returncode: raise RuntimeError(f'Verilator compile {tag} failed; see report')
        return [str(obj/'Vtb_superscalar_core')],'Verilator'
    simv=ROOT/'sim'/f'perf_{tag}.vvp'
    cmd=[iverilog,'-g2012','-Wall',f'-Ptb_superscalar_core.DUAL_ENABLE={1 if dual else 0}','-o',str(simv),*files]
    cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    (REPORT/f'rtl_perf_compile_{tag}.log').write_text(cp.stdout+cp.stderr)
    if cp.returncode: raise RuntimeError(f'Icarus compile {tag} failed; see report')
    return [vvp,str(simv)],'Icarus'

HALT=re.compile(r'HALT cause=\d+ pc=[0-9a-fA-F]+ cycles=(\d+) retired=(\d+) dual=(\d+) single=(\d+) IPC=([0-9.eE+-]+)')
def run(binary,tag,program):
    stem=program.stem
    trace=REPORT/f'rtl_perf_{tag}_{stem}_trace.csv'; cov=REPORT/f'rtl_perf_{tag}_{stem}_coverage.txt'
    cp=subprocess.run([*binary,f'+HEX={program}',f'+TRACE={trace}',f'+COVERAGE={cov}'],cwd=ROOT,text=True,capture_output=True)
    (REPORT/f'rtl_perf_{tag}_{stem}.log').write_text(cp.stdout+cp.stderr)
    if cp.returncode: raise RuntimeError(f'{tag}/{stem} simulator rc={cp.returncode}')
    m=HALT.search(cp.stdout+cp.stderr)
    if not m: raise RuntimeError(f'{tag}/{stem}: HALT performance line not found')
    cyc,ret,dc,sc,ipc=m.groups()
    return dict(cycles=int(cyc),retired=int(ret),dual_cycles=int(dc),single_cycles=int(sc),ipc=float(ipc))

try:
    dual_bin,backend=build(True); single_bin,_=build(False)
    rows=[]
    for hp in sorted((ROOT/'sw/perf').glob('*.hex')):
        d=run(dual_bin,'dual',hp); s=run(single_bin,'single',hp)
        if d['retired']!=s['retired']: raise RuntimeError(f'{hp.stem}: retired count differs')
        speed=s['cycles']/d['cycles'] if d['cycles'] else 0.0
        rows.append((hp.stem,s,d,speed))
except Exception as e:
    text=f'# RTL Performance Comparison\n\nFAIL: {e}\n'
    (REPORT/'rtl_performance_comparison.md').write_text(text); print(text,end=''); raise SystemExit(1)

lines=['# RTL Performance Comparison','',f'Backend: **{backend}**','',
       '| Program | Retired | Single cycles | 2-wide cycles | Single IPC | 2-wide IPC | RTL speedup | Dual-issue cycles |',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
for n,s,d,sp in rows:
    lines.append(f'| {n} | {d["retired"]} | {s["cycles"]} | {d["cycles"]} | {s["ipc"]:.3f} | {d["ipc"]:.3f} | {sp:.3f}x | {d["dual_cycles"]} |')
lines += ['','These are RTL simulator measurements from identical programs with only `ENABLE_DUAL_ISSUE` changed.']
out='\n'.join(lines)+'\n'; (REPORT/'rtl_performance_comparison.md').write_text(out); print(out,end='')
