#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1]
checks=[
 ('tool detection',[sys.executable,'scripts/detect_tools.py'],{0}),
 ('directed generation',[sys.executable,'scripts/gen_directed_tests.py'],{0}),
 ('reference regression',[sys.executable,'scripts/run_reference_regression.py'],{0}),
 ('microarchitecture model',[sys.executable,'scripts/run_microarchitecture_regression.py'],{0}),
 ('divider algorithm stress',[sys.executable,'scripts/run_divider_stress.py'],{0}),
 ('front-end replay stress',[sys.executable,'scripts/run_frontend_replay_stress.py'],{0}),
 ('pytest Python models',[sys.executable,'-m','pytest','-q','tb/tests/test_reference.py','tb/tests/test_microarchitecture.py'],{0}),
 ('required ISA exercise',[sys.executable,'scripts/check_isa_coverage.py'],{0}),
 ('reference stimulus coverage',[sys.executable,'scripts/reference_functional_coverage.py'],{0}),
 ('static RTL audit',[sys.executable,'scripts/static_rtl_audit.py'],{0}),
 ('formal flow source audit',[sys.executable,'scripts/audit_formal_flow.py'],{0}),
 ('EDA/CI tool flow audit',[sys.executable,'scripts/audit_tool_flows.py'],{0}),
 ('RTL simulation',[sys.executable,'scripts/run_rtl_regression.py'],{0,2}),
 ('RTL functional coverage',[sys.executable,'scripts/analyze_rtl_coverage.py'],{0,2}),
 ('RTL performance compare',[sys.executable,'scripts/run_rtl_performance_compare.py'],{0,2}),
 ('Verilator lint',[sys.executable,'scripts/run_lint.py'],{0,2}),
 ('formal',[sys.executable,'scripts/run_formal.py'],{0,2}),
 ('Yosys synthesis',[sys.executable,'scripts/run_synthesis.py'],{0,2}),
]
strict_eda=os.environ.get('REQUIRE_EDA','0')=='1'
status=[]
for name,cmd,allowed in checks:
    print(f'\n=== {name} ===')
    p=subprocess.run(cmd,cwd=ROOT)
    if p.returncode==0: st='PASS'
    elif p.returncode==2 and not strict_eda: st='TOOL UNAVAILABLE'
    else: st='FAIL' if p.returncode!=2 else 'FAIL (REQUIRED TOOL UNAVAILABLE)'
    status.append((name,st,p.returncode))
    if p.returncode not in allowed:
        print(f'FAILED: {name} rc={p.returncode}')

print('\n=== ALL CHECKS SUMMARY ===')
for n,s,rc in status: print(f'{n:28s} {s}')
import json
status_name='check_status_strict.json' if strict_eda else 'check_status.json'
(ROOT/'reports'/status_name).write_text(json.dumps([
    {'check':n,'status':s,'returncode':rc} for n,s,rc in status
],indent=2)+'\n')
if not strict_eda:
    subprocess.run([sys.executable,'scripts/generate_final_summary.py'],cwd=ROOT)
if any(s.startswith('FAIL') for _,s,_ in status): raise SystemExit(1)
