#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'reports'/'synthesis'/'synthesis_report.txt'; out.parent.mkdir(parents=True,exist_ok=True)
timing=ROOT/'reports'/'timing'/'timing_report.txt'; timing.parent.mkdir(parents=True,exist_ok=True)
yosys=shutil.which('yosys')
if not yosys:
    out.write_text('YOSYS SYNTHESIS: TOOL UNAVAILABLE\nNo cell count, area, or timing number is claimed.\n')
    timing.write_text('TIMING: NOT RUN — no synthesis tool/characterized Liberty library available in this environment.\n')
    print(out.read_text(),end=''); raise SystemExit(2)
# Prefer the Slang SystemVerilog frontend when its Yosys plugin is installed.
probe=subprocess.run([yosys,'-m','slang','-p','help read_slang'],cwd=ROOT,text=True,capture_output=True)
if probe.returncode==0:
    cmd=[yosys,'-m','slang','-s','synthesis/synth_slang.ys']; frontend='yosys-slang'
else:
    cmd=[yosys,'-s','synthesis/synth.ys']; frontend='yosys native read_verilog -sv fallback'
cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
out.write_text(f'Frontend: {frontend}\n\n'+cp.stdout+cp.stderr)
timing.write_text('TIMING: NOT RUN unless a characterized Liberty library is supplied. Generic Yosys statistics are not a MHz/WNS measurement.\n')
print(out.read_text(),end='')
raise SystemExit(cp.returncode)
