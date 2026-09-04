#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess, sys, csv, json, os
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
from rv32im_model import RV32IM, load_hex
sys.path.insert(0,str(ROOT/'scripts'))
from gen_random_program import program as random_program
import riscv_encode as E

REPORT=ROOT/'reports'/'simulation'; REPORT.mkdir(parents=True,exist_ok=True)
iverilog=shutil.which('iverilog'); vvp=shutil.which('vvp'); verilator=shutil.which('verilator')
files=[str(ROOT/line.strip()) for line in (ROOT/'sim'/'filelist.f').read_text().splitlines() if line.strip()]

backend=None
sim_command=None
# Prefer Verilator for this SystemVerilog-heavy design (packages/packed structs);
# use Icarus as the lightweight fallback.
if verilator:
    backend='verilator'
    objdir=ROOT/'sim'/'obj_dir'
    cmd=[verilator,'--binary','--timing','--assert','-Wall','-Wno-fatal',
         '--top-module','tb_superscalar_core','--Mdir',str(objdir),*files]
    cp=subprocess.run(cmd,text=True,capture_output=True,cwd=ROOT)
    (REPORT/'verilator_compile.log').write_text(cp.stdout+cp.stderr)
    if cp.returncode:
        print(cp.stdout,cp.stderr); raise SystemExit(cp.returncode)
    simv=objdir/'Vtb_superscalar_core'
    sim_command=[str(simv)]
elif iverilog and vvp:
    backend='iverilog'
    simv=ROOT/'sim'/'superscalar_tb.vvp'
    cmd=[iverilog,'-g2012','-Wall','-o',str(simv),*files]
    cp=subprocess.run(cmd,text=True,capture_output=True,cwd=ROOT)
    (REPORT/'iverilog_compile.log').write_text(cp.stdout+cp.stderr)
    if cp.returncode:
        print(cp.stdout,cp.stderr); raise SystemExit(cp.returncode)
    sim_command=[vvp,str(simv)]
else:
    msg='RTL SIMULATION: TOOL UNAVAILABLE (requires Verilator or Icarus Verilog)\n'
    (REPORT/'rtl_regression.log').write_text(msg)
    print(msg.strip()); raise SystemExit(2)


def rtl_trace(path):
    rows=[]
    with open(path,newline='') as f:
        for r in csv.DictReader(f):
            rows.append({
              'pc':int(r['pc'],16),'instr':int(r['instr'],16),'rd_we':bool(int(r['rd_we'])),'rd':int(r['rd']),
              'rd_value':int(r['rd_value'],16),'mem_write':bool(int(r['mem_we'])),'mem_addr':int(r['mem_addr'],16),'mem_data':int(r['mem_data'],16)
            })
    return rows

TRAP_CAUSE = {
    'instruction_misaligned': 0,
    'illegal': 2,
    'breakpoint': 3,
    'load_misaligned': 4,
    'store_misaligned': 6,
    'ecall': 11,
}

def expected(words):
    m=RV32IM(words).run()
    commits=[dict(pc=c.pc,instr=c.instr,rd_we=c.rd_we,rd=c.rd,rd_value=c.rd_value,mem_write=c.mem_write,mem_addr=c.mem_addr,mem_data=c.mem_data) for c in m.commits]
    return commits,m

def read_status(path):
    d={}
    for line in Path(path).read_text().splitlines():
        if '=' not in line: continue
        k,v=line.split('=',1)
        d[k.strip()]=v.strip()
    return d

def compare(a,b):
    if len(a)!=len(b): return False,f'commit count rtl={len(a)} ref={len(b)}'
    for i,(x,y) in enumerate(zip(a,b)):
        for k in ('pc','instr','rd_we','rd','rd_value','mem_write'):
            if x[k]!=y[k]: return False,f'commit {i} field {k}: rtl={x[k]} ref={y[k]}'
        if x['mem_write']:
            for k in ('mem_addr','mem_data'):
                if x[k]!=y[k]: return False,f'commit {i} field {k}: rtl={x[k]} ref={y[k]}'
    return True,'match'

DIRECTED_GLOB='[0-9][0-9]_*.hex'
RANDOM_SEEDS=50
results=[]

def run_one(name, hp, words, coverage=True):
    trace=REPORT/f'{name}_trace.csv'
    cov=ROOT/'reports'/'coverage'/f'{name}_coverage.txt'
    status=REPORT/f'{name}_status.txt'
    args=[*sim_command,f'+HEX={hp}',f'+TRACE={trace}',f'+COVERAGE={cov}',f'+STATUS={status}']
    run=subprocess.run(args,text=True,capture_output=True,cwd=ROOT)
    (REPORT/f'{name}.log').write_text(run.stdout+run.stderr)
    if run.returncode:
        return False,f'simulator rc={run.returncode}'
    exp_trace,m=expected(words)
    ok,msg=compare(rtl_trace(trace),exp_trace)
    if not ok:
        return ok,msg
    if not status.exists():
        return False,'missing RTL status file'
    st=read_status(status)
    try:
        rtl_cause=int(st['trap_cause'],0)
        rtl_pc=int(st['trap_pc'],16)
        rtl_retired=int(st['retired'],0)
    except (KeyError,ValueError) as e:
        return False,f'bad RTL status: {e}'
    exp_cause=TRAP_CAUSE.get(m.trap)
    if exp_cause is None:
        return False,f'unmapped reference trap {m.trap}'
    if rtl_cause != exp_cause:
        return False,f'trap cause rtl={rtl_cause} ref={exp_cause} ({m.trap})'
    if rtl_pc != m.pc:
        return False,f'trap pc rtl=0x{rtl_pc:08x} ref=0x{m.pc:08x}'
    if rtl_retired != len(exp_trace):
        return False,f'retired counter rtl={rtl_retired} ref={len(exp_trace)}'
    return True,f'match trap={m.trap}@0x{m.pc:08x}'

for hp in sorted((ROOT/'sw'/'hex').glob(DIRECTED_GLOB)):
    ok,msg=run_one(hp.stem,hp,load_hex(hp))
    results.append(('directed',hp.stem,ok,msg))

rnd_dir=ROOT/'sim'/'generated_random'; rnd_dir.mkdir(parents=True,exist_ok=True)
for seed in range(1,RANDOM_SEEDS+1):
    words=random_program(seed,80)
    hp=rnd_dir/f'random_seed_{seed:04d}.hex'
    E.write_hex(hp,words)
    ok,msg=run_one(hp.stem,hp,words,coverage=False)
    results.append(('random',hp.stem,ok,msg))

with open(REPORT/'rtl_regression.log','w') as f:
    f.write(f'Backend: {backend}\n')
    for kind,n,ok,msg in results:
        f.write(f'{kind:8s} {n:28s} {"PASS" if ok else "FAIL":4s} {msg}\n')
    directed=[r for r in results if r[0]=='directed']
    randoms=[r for r in results if r[0]=='random']
    f.write(f'DIRECTED {sum(r[2] for r in directed)}/{len(directed)} PASS\n')
    f.write(f'RANDOM   {sum(r[2] for r in randoms)}/{len(randoms)} PASS\n')
    f.write(f'TOTAL    {sum(r[2] for r in results)}/{len(results)} PASS\n')
print((REPORT/'rtl_regression.log').read_text(),end='')
if not all(r[2] for r in results): raise SystemExit(1)
