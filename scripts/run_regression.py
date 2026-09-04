#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, shutil
ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
    p=subprocess.run(cmd,cwd=ROOT); return p.returncode

rc_ref=run([sys.executable,'scripts/gen_directed_tests.py'])
if rc_ref==0: rc_ref=run([sys.executable,'scripts/run_reference_regression.py'])
print('\n=== RTL regression ===')
rc_rtl=run([sys.executable,'scripts/run_rtl_regression.py'])
print('\n=== Summary ===')
print('Reference model:','PASS' if rc_ref==0 else 'FAIL')
print('RTL simulation:','PASS' if rc_rtl==0 else ('TOOL UNAVAILABLE' if rc_rtl==2 else 'FAIL'))
if rc_ref!=0 or rc_rtl not in (0,2): raise SystemExit(1)
