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
    [yosys, '-m', 'slang', '-Q', '-p', 'help read_slang; help sat; help cutpoint'],
    cwd=ROOT, text=True, capture_output=True,
)
if probe.returncode != 0 or 'No such command' in (probe.stdout + probe.stderr):
    out.write_text('FORMAL: TOOL UNAVAILABLE (yosys-slang/read_slang, SAT, or cutpoint unavailable).\n')
    print(out.read_text(), end='')
    raise SystemExit(2)

# mode='seq' performs a direct one-step combinational proof. mode='base32'
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

# The core assertions are control/ordering properties, while ALU and branch
# arithmetic is proven independently above.  For the 32-cycle core proof,
# abstract datapath values at their observation points.  Each cutpoint becomes
# an unconstrained value every cycle, so the control proof must hold for *all*
# datapath results rather than for a reduced set of concrete arithmetic cases.
# This is a conservative compositional abstraction and also removes the bulk of
# the register-file read mux and arithmetic cone from the bounded SAT problem.
CORE_CUTPOINTS = [
    'w:*rf_r0*',
    'w:*rf_r1*',
    'w:*rf_r2*',
    'w:*rf_r3*',
    'w:*ex0_alu_y*',
    'w:*ex1_alu_y*',
    'w:*ex0_mul_y*',
    'w:*div_result*',
    'w:*ex0_branch_taken*',
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

    script_parts = [
        read_cmd,
        f'prep -top {top}',
        'flatten',
        f'select -module {top}',
    ]

    if name == 'core':
        # Fail loudly if synthesis/elaboration renames away any intended
        # abstraction point; silently missing a cutpoint would weaken the
        # reproducibility/performance of the formal flow.
        script_parts.extend(f'select -assert-any {pat}' for pat in CORE_CUTPOINTS)
        script_parts.append('cutpoint ' + ' '.join(CORE_CUTPOINTS))
        script_parts.append('opt_clean')

    script_parts.extend([
        'memory_map',
        'async2sync',
        'opt_clean',
        f'select -module {top}',
        sat_cmd,
    ])
    script = '; '.join(script_parts)

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
    f.write('Core bounded proof: Yosys base-case engine through depth 32.\n')
    f.write('Core proof abstraction: RF read data + ALU/MUL/DIV results + branch outcome are formal cutpoints.\n\n')
    for name, mode, depth, rc, text in results:
        status = 'PASS' if rc == 0 else 'FAIL'
        f.write(f'=== {name}: {status} rc={rc} mode={mode} depth={depth} ===\n{text}\n')

print(out.read_text(), end='')
raise SystemExit(0 if len(results) == len(targets) and all(rc == 0 for _, _, _, rc, _ in results) else 1)
