#!/usr/bin/env python3
"""Execute real formal proofs with Yosys-Slang and the Yosys SAT engine.

The project keeps SymbiYosys .sby configurations under formal/, but current
OSS CAD Suite SBY launches its own Yosys process without the external Slang
frontend loaded.  This runner therefore proves the same harness assertions
directly through Yosys-Slang.  A target is reported PASS only when the SAT
engine returns success for every assertion under the harness assumptions.
"""
from pathlib import Path
import shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'reports' / 'formal' / 'formal_report.txt'
out.parent.mkdir(parents=True, exist_ok=True)
yosys = shutil.which('yosys')

if not yosys:
    out.write_text('FORMAL: TOOL UNAVAILABLE (requires yosys).\n')
    print(out.read_text(), end='')
    raise SystemExit(2)

probe = subprocess.run(
    [yosys, '-m', 'slang', '-Q', '-p', 'help read_slang; help sat'],
    cwd=ROOT, text=True, capture_output=True,
)
if probe.returncode != 0 or 'No such command' in (probe.stdout + probe.stderr):
    out.write_text('FORMAL: TOOL UNAVAILABLE (yosys-slang/read_slang or SAT frontend unavailable).\n')
    print(out.read_text(), end='')
    raise SystemExit(2)

targets = [
    (
        'issue',
        ['rtl/common/riscv_pkg.sv', 'rtl/issue/dual_issue_unit.sv', 'formal/issue_harness.sv'],
        'issue_harness',
        1,
        False,
    ),
    (
        'alu_branch',
        ['rtl/common/riscv_pkg.sv', 'rtl/execute/alu.sv', 'rtl/branch/branch_unit.sv',
         'formal/alu_branch_harness.sv'],
        'alu_branch_harness',
        1,
        False,
    ),
    (
        'core',
        ['rtl/common/riscv_pkg.sv', 'rtl/decode/decoder.sv', 'rtl/execute/alu.sv',
         'rtl/branch/branch_unit.sv', 'rtl/core/register_file.sv',
         'rtl/issue/dual_issue_unit.sv', 'rtl/mdu/mul_unit.sv', 'rtl/mdu/div_unit.sv',
         'rtl/memory/load_store_unit.sv', 'rtl/core/superscalar_core.sv',
         'formal/core_harness.sv'],
        'core_formal_harness',
        32,
        True,
    ),
]

results = []
for name, files, top, depth, formal_define in targets:
    read_cmd = 'read_slang ' + ' '.join(files) + f' --top {top}'
    if formal_define:
        read_cmd += ' -D FORMAL'
    script = '; '.join([
        read_cmd,
        f'prep -top {top}',
        'memory_map',
        'async2sync',
        'opt_clean',
        'flatten',
        f'select -module {top}',
        f'sat -verify -prove-asserts -set-assumes -seq {depth}',
    ])
    cp = subprocess.run(
        [yosys, '-m', 'slang', '-Q', '-p', script],
        cwd=ROOT, text=True, capture_output=True,
    )
    results.append((name, cp.returncode, cp.stdout + cp.stderr))

with out.open('w') as f:
    f.write('FORMAL ENGINE: Yosys-Slang + Yosys SAT\n')
    f.write('SBY configuration files are retained under formal/ for portability.\n\n')
    for name, rc, text in results:
        status = 'PASS' if rc == 0 else 'FAIL'
        f.write(f'=== {name}: {status} rc={rc} ===\n{text}\n')

print(out.read_text(), end='')
raise SystemExit(0 if all(rc == 0 for _, rc, _ in results) else 1)
