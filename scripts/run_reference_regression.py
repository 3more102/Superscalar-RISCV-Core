#!/usr/bin/env python3
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference_model'))
sys.path.insert(0,str(ROOT/'scripts'))
from rv32im_model import RV32IM, load_hex
from gen_random_program import program
from issue_model import issue_cycles
import riscv_encode as E

# Directed expectations are generated or retained beside each HEX image.
report=[]
for p in sorted((ROOT/'sw'/'hex').glob('[0-9][0-9]_*.hex')):
    try:
        words=load_hex(p)
        m=RV32IM(words).run()
        exp=json.loads(p.with_suffix('.expected.json').read_text())
        exp_trap=exp['trap']; exp_pc=int(exp['trap_pc'],16)
        ok=m.trap==exp_trap and m.pc==exp_pc and m.regs[0]==0 and len(m.commits)==exp['commits']
        report.append((p.stem,ok,f'commits={len(m.commits)} trap={m.trap} pc=0x{m.pc:08x} expected={exp_trap}@0x{exp_pc:08x}'))
    except Exception as ex:
        report.append((p.stem,False,str(ex)))

RANDOM_SEEDS=500
random_ok=0
random_commits=0
random_failures=[]
for seed in range(1,RANDOM_SEEDS+1):
    try:
        m=RV32IM(program(seed,80)).run(max_steps=100000)
        if m.trap=='breakpoint' and m.regs[0]==0:
            random_ok+=1
            random_commits += len(m.commits)
        else:
            random_failures.append((f'random_seed_{seed}',False,f'trap={m.trap}'))
    except Exception as ex:
        random_failures.append((f'random_seed_{seed}',False,str(ex)))

ind=[]
for k in range(100):
    rda=1+(2*k)%30; rdb=1+(2*k+1)%30
    ind += [E.addi(rda,0,k), E.xori(rdb,0,k)]
dep=[E.addi(1,0,1)]
for k in range(1,100): dep.append(E.addi(1,1,1))
perf={'independent':issue_cycles(ind),'dependency_chain':issue_cycles(dep)}

directed_pass=sum(1 for _,ok,_ in report if ok)
directed_failures=[x for x in report if not x[1]]
failures=directed_failures+random_failures
directed_commits=sum(
    int(msg.split('commits=')[1].split()[0])
    for _,ok,msg in report
    if ok and 'commits=' in msg
)
summary={
    'directed_pass':directed_pass,
    'directed_total':len(report),
    'random_pass':random_ok,
    'random_total':RANDOM_SEEDS,
    'directed_commits':directed_commits,
    'random_commits':random_commits,
    'reference_commits_checked':directed_commits+random_commits,
    'failures':failures,
    'issue_model':perf,
}
out_dir=ROOT/'reports'/'simulation'
out_dir.mkdir(parents=True,exist_ok=True)
(out_dir/'reference_regression.json').write_text(json.dumps(summary,indent=2)+'\n')

log_lines=[]
for name,ok,msg in report:
    log_lines.append(f'{name:28s} {"PASS" if ok else "FAIL":4s} {msg}')
for name,_,msg in random_failures:
    log_lines.append(f'{name:28s} FAIL {msg}')
log_lines += [
    f'DIRECTED REFERENCE TESTS    {directed_pass}/{len(report)} PASS',
    f'RANDOM REFERENCE SEEDS      {random_ok}/{RANDOM_SEEDS} PASS',
    f'REFERENCE COMMITS CHECKED   {directed_commits+random_commits}',
    f'ISSUE MODEL independent     IPC={perf["independent"]["issue_ipc"]:.3f} dual_cycles={perf["independent"]["dual_cycles"]}',
    f'ISSUE MODEL dependency-chain IPC={perf["dependency_chain"]["issue_ipc"]:.3f} dual_cycles={perf["dependency_chain"]["dual_cycles"]}',
]
log_text='\n'.join(log_lines)+'\n'
(out_dir/'reference_regression.log').write_text(log_text)
print(log_text,end='')

if failures or directed_pass != len(report) or random_ok != RANDOM_SEEDS:
    raise SystemExit(1)
