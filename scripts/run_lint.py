#!/usr/bin/env python3
from pathlib import Path
import re, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
report=ROOT/'reports'/'lint_report.txt'
verilator=shutil.which('verilator')
if not verilator:
    subprocess.run([sys.executable,'scripts/static_rtl_audit.py'],cwd=ROOT)
    report.write_text('VERILATOR LINT: TOOL UNAVAILABLE\nSee reports/static_rtl_audit.txt for the non-compiler source audit.\n')
    print(report.read_text(),end=''); raise SystemExit(2)
cmd=[verilator,'--lint-only','-Wall','-Wno-fatal','--timing','-Wno-DECLFILENAME',
     '--top-module','superscalar_core','-f','sim/rtl_filelist.f']
cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
text=cp.stdout+cp.stderr
warning_codes=re.findall(r'%Warning-([A-Z0-9_]+):',text)
allow={'UNUSEDSIGNAL','UNUSEDPARAM'}
unexpected=sorted(set(warning_codes)-allow)
summary=(f'\nLINT POLICY: warnings={len(warning_codes)}; allowed={sorted(allow)}; unexpected={unexpected}\n')
report.write_text(text+summary)
print(report.read_text(),end='')
if cp.returncode!=0:
    raise SystemExit(cp.returncode)
raise SystemExit(1 if unexpected else 0)
