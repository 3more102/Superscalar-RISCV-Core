#!/usr/bin/env python3
"""Static integrity audit for formal source/configuration.

This does NOT prove any RTL property. It verifies that formal targets are
self-consistent enough to hand to the configured Yosys-Slang/SAT flow:
referenced files exist, requested tops are defined, combinational harnesses
expose symbolic primary inputs, and the complete-core target contains an
explicit reset/environment harness.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
targets=sorted((ROOT/'formal').glob('*.sby'))
issues=[]
rows=[]

if not targets:
    issues.append('no formal/*.sby targets found')

for sby in targets:
    text=sby.read_text()
    rel=str(sby.relative_to(ROOT))
    m=re.search(r'(?ms)^\[files\]\s*\n(.*?)(?=^\[|\Z)',text)
    files=[]
    if not m:
        issues.append(f'{rel}: missing [files] section')
    else:
        for raw in m.group(1).splitlines():
            raw=raw.strip()
            if raw and not raw.startswith('#'):
                files.append(raw.split()[0])
        for f in files:
            if not (ROOT/f).is_file():
                issues.append(f'{rel}: referenced file missing: {f}')

    top_matches=re.findall(r'--top\s+([A-Za-z_][A-Za-z0-9_]*)',text)
    if not top_matches:
        top_matches=re.findall(r'prep\s+[^\n]*-top\s+([A-Za-z_][A-Za-z0-9_]*)',text)
    if not top_matches:
        issues.append(f'{rel}: no top module found in script')
        top='?'
    else:
        top=top_matches[-1]
        corpus='\n'.join((ROOT/f).read_text(errors='ignore') for f in files if (ROOT/f).is_file())
        if not re.search(rf'\bmodule\s+{re.escape(top)}\b',corpus):
            issues.append(f'{rel}: top module {top} not defined in [files] corpus')
    rows.append((rel,top,len(files)))

core=ROOT/'formal'/'core.sby'
if core.is_file():
    ct=core.read_text()
    for needle in ('formal/core_harness.sv','-D FORMAL','--top core_formal_harness','read_slang'):
        if needle not in ct:
            issues.append(f'formal/core.sby: required complete-core marker missing: {needle}')
else:
    issues.append('formal/core.sby missing')

h=ROOT/'formal'/'core_harness.sv'
if h.is_file():
    ht=h.read_text()
    core_patterns=(
        r'\binput\s+logic\s+reset_n\b',
        r'\binput\s+logic\s*\[31:0\]\s+imem_rdata0\b',
        r'\binput\s+logic\s*\[31:0\]\s+imem_rdata1\b',
        r'\binput\s+logic\s*\[31:0\]\s+dmem_rdata\b',
        r'assume\s*\(\s*!reset_n\s*\)',
        r'assume\s*\(\s*reset_n\s*\)',
        r'\bf_seen_clock\b',
    )
    for pattern in core_patterns:
        if not re.search(pattern, ht):
            issues.append(f'formal/core_harness.sv: reset/symbolic-environment pattern missing: {pattern}')
else:
    issues.append('formal/core_harness.sv missing')

# Combinational proof harnesses must expose their stimulus as top-level primary
# inputs so Yosys SAT receives real symbolic variables rather than undriven Xs.
# Match by syntax with flexible whitespace rather than brittle exact strings.
for rel, patterns in {
    'formal/issue_harness.sv': (
        r'\binput\s+riscv_pkg::decoded_t\s+d0\b',
        r'\binput\s+riscv_pkg::decoded_t\s+d1\b',
        r'\binput\s+logic\s+stall0\b',
        r'\binput\s+logic\s+stall1\b',
    ),
    'formal/alu_branch_harness.sv': (
        r'\binput\s+logic\s*\[31:0\]\s+a\b',
        r'\binput\s+logic\s*\[31:0\]\s+b\b',
        r'\binput\s+riscv_pkg::alu_op_e\s+alu_op\b',
        r'\binput\s+riscv_pkg::branch_op_e\s+br_op\b',
        r'\boutput\s+logic\s*\[31:0\]\s+actual_y\b',
        r'\boutput\s+logic\s*\[31:0\]\s+expected_y\b',
        r'\bassert\s*\(\s*actual_y\s*==\s*expected_y\s*\)',
        r'\bassert\s*\(\s*actual_taken\s*==\s*expected_taken\s*\)',
    ),
}.items():
    p=ROOT/rel
    if not p.is_file():
        issues.append(f'{rel} missing')
        continue
    text=p.read_text()
    for pattern in patterns:
        if not re.search(pattern, text):
            issues.append(f'{rel}: symbolic-primary-input/specification pattern missing: {pattern}')

rtl=ROOT/'rtl'/'core'/'superscalar_core.sv'
if rtl.is_file():
    rt=rtl.read_text()
    for needle in ('f_prev_replay','f_prev_redirect','assert (!buf_v1 || buf_v0)',
                   'if (ex0_exc_valid)','if (dmem_we)','if (f_prev_replay)'):
        if needle not in rt:
            issues.append(f'rtl/core/superscalar_core.sv: formal invariant marker missing: {needle}')

lines=['FORMAL FLOW SOURCE AUDIT (not a formal proof)','',f'Targets: {len(targets)}']
for rel,top,n in rows:
    lines.append(f'{rel}: top={top} files={n}')
lines.append(f'Issues: {len(issues)}')
if issues:
    lines += [''] + issues
out=ROOT/'reports'/'formal'/'formal_flow_audit.txt'; out.parent.mkdir(parents=True,exist_ok=True)
out.write_text('\n'.join(lines)+'\n')
print(out.read_text(),end='')
raise SystemExit(1 if issues else 0)
