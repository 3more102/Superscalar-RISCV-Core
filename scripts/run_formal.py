#!/usr/bin/env python3
"""Execute real formal proofs with Yosys-Slang and the Yosys SAT engine.

The project keeps SymbiYosys .sby configurations under formal/, but current
OSS CAD Suite SBY launches its own Yosys process without the external Slang
frontend loaded. This runner therefore proves the same harness assertions
directly through Yosys-Slang. A target is reported PASS only when the SAT
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

# mode='seq' performs a direct one-step combinational proof.  mode='base32'
# keeps the complete-core obligation at 32 cycles, but uses Yosys' documented
# faster bounded base-case engine (-tempinduct-baseonly -maxsteps 32) instead
# of building one monolithic -seq 32 SAT instance.
targets = [
    (
        'issue',
        ['rtl/common/riscv_pkg.sv', 'rtl/issue/dual_issue_unit.sv', 'formal/issue_harness.sv'],
        'issue_harness',
        'seq',
        1,
        False,
    ),
    (
        'alu_branch',
        ['rtl/common/riscv_pkg.sv', 'rtl/execute/alu.sv', 'rtl/branch/branch_unit.sv',
         'formal/alu_branch_harness.sv'],
        'alu_branch_harness',
        'seq',
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
        'base32',
        32,
        True,
    ),
]

results = []
for name, files, top, mode, depth, formal_define in targets:
    read_cmd = 'read_slang ' + ' '.join(files) + f' --top {top}'
    if formal_define:
        read_cmd += ' -D FORMAL'

    # Keep this common prefix explicit: source audits require that failed
    # assertions remain fatal and harness assumptions are enforced.
    sat_common = 'sat -verify -prove-asserts -set-assumes -show-inputs -show-outputs'
    if mode == 'seq':
        sat_cmd = f'{sat_common} -seq {depth}'
    elif mode == 'base32':
        sat_cmd = f'{sat_common} -tempinduct-baseonly -maxsteps {depth}'
    else:
        raise RuntimeError(f'unknown formal mode: {mode}')

    script = '; '.join([
        read_cmd,
        f'prep -top {top}',
        'memory_map',
        'async2sync',
        'opt_clean',
        'flatten',
        f'select -module {top}',
        sat_cmd,
    ])
    cp = subprocess.run(
        [yosys, '-m', 'slang', '-Q', '-p', script],
        cwd=ROOT, text=True, capture_output=True,
    )
    results.append((name, mode, depth, cp.returncode, cp.stdout + cp.stderr))
    # Preserve the first counterexample and avoid spending time on deeper
    # targets until the earlier proof obligation is fixed. When all targets
    # pass, the loop naturally executes the complete suite including core/32.
    if cp.returncode != 0:
        break

with out.open('w') as f:
    f.write('FORMAL ENGINE: Yosys-Slang + Yosys SAT\n')
    f.write('SBY configuration files are retained under formal/ for portability.\n')
    f.write('Core bounded proof: Yosys base-case engine through depth 32.\n\n')
    for name, mode, depth, rc, text in results:
        status = 'PASS' if rc == 0 else 'FAIL'
        f.write(f'=== {name}: {status} rc={rc} mode={mode} depth={depth} ===\n{text}\n')

print(out.read_text(), end='')
raise SystemExit(0 if len(results) == len(targets) and all(rc == 0 for _, _, _, rc, _ in results) else 1)
