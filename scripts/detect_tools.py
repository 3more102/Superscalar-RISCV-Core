#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess, platform, sys
ROOT=Path(__file__).resolve().parents[1]
tools=['iverilog','vvp','verilator','yosys','sby','yosys-smtbmc','sta','opensta','gtkwave','riscv32-unknown-elf-gcc','riscv64-unknown-elf-gcc','python3','make','git']
lines=[f'Platform: {platform.platform()}',f'Python runtime: {sys.version.splitlines()[0]}','']
for t in tools:
    p=shutil.which(t)
    if not p:
        lines.append(f'{t}: TOOL UNAVAILABLE')
        continue
    version=''
    for args in ([t,'--version'],[t,'-V'],[t,'-v']):
        try:
            cp=subprocess.run(args,text=True,capture_output=True,timeout=5)
            text=(cp.stdout+cp.stderr).strip().splitlines()
            if text:
                version=text[0]; break
        except Exception: pass
    lines.append(f'{t}: {p} | {version}')

# SystemVerilog synthesis frontend check.
y=shutil.which('yosys')
if y:
    try:
        cp=subprocess.run([y,'-m','slang','-p','help read_slang'],text=True,capture_output=True,timeout=10)
        lines.append('yosys-slang frontend: AVAILABLE' if cp.returncode==0 else 'yosys-slang frontend: TOOL UNAVAILABLE')
    except Exception:
        lines.append('yosys-slang frontend: TOOL UNAVAILABLE')

out=ROOT/'reports'/'tool_versions.txt'; out.write_text('\n'.join(lines)+'\n')
print(out.read_text(),end='')
