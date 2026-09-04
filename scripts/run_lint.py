#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
report=ROOT/'reports'/'lint_report.txt'
verilator=shutil.which('verilator')
if not verilator:
    subprocess.run([sys.executable,'scripts/static_rtl_audit.py'],cwd=ROOT)
    report.write_text('VERILATOR LINT: TOOL UNAVAILABLE\nSee reports/static_rtl_audit.txt for the non-compiler source audit.\n')
    print(report.read_text(),end=''); raise SystemExit(2)
cmd=[verilator,'--lint-only','-Wall','--timing','-Wno-DECLFILENAME','--top-module','superscalar_core','-f','sim/rtl_filelist.f']
cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
report.write_text(cp.stdout+cp.stderr)
print(report.read_text(),end='')
raise SystemExit(cp.returncode)
