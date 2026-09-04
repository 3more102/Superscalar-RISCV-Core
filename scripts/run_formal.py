#!/usr/bin/env python3
from pathlib import Path
import os, shutil, stat, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'reports'/'formal'/'formal_report.txt'
out.parent.mkdir(parents=True,exist_ok=True)
sby=shutil.which('sby'); yosys=shutil.which('yosys')
if not sby or not yosys:
    out.write_text('FORMAL: TOOL UNAVAILABLE (requires sby and yosys).\nFormal harnesses are present under formal/.\n')
    print(out.read_text(),end=''); raise SystemExit(2)
probe=subprocess.run([yosys,'-m','slang','-Q','-p','help read_slang'],cwd=ROOT,text=True,capture_output=True)
if probe.returncode!=0 or 'No such command' in (probe.stdout+probe.stderr):
    out.write_text('FORMAL: TOOL UNAVAILABLE (yosys-slang/read_slang frontend not available).\n')
    print(out.read_text(),end=''); raise SystemExit(2)
results=[]
with tempfile.TemporaryDirectory(prefix='sby-yosys-') as td:
    wrapper=Path(td)/'yosys'
    wrapper.write_text(f'#!/bin/sh\nexec "{yosys}" -m slang "$@"\n')
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    env=os.environ.copy()
    env['PATH']=td+os.pathsep+env.get('PATH','')
    for cfg in ['formal/issue.sby','formal/alu_branch.sby','formal/core.sby']:
        cp=subprocess.run([sby,'-f',cfg],cwd=ROOT,text=True,capture_output=True,env=env)
        results.append((cfg,cp.returncode,cp.stdout+cp.stderr))
with out.open('w') as f:
    for cfg,rc,text in results:
        f.write(f'=== {cfg} rc={rc} ===\n{text}\n')
print(out.read_text(),end='')
raise SystemExit(0 if all(rc==0 for _,rc,_ in results) else 1)
