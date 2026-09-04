#!/usr/bin/env python3
"""Static integrity checks for local bootstrap/CI/EDA launcher scripts.

This is not an execution of Verilator/Yosys/SBY/OpenSTA. It catches broken
paths, missing strict-mode wiring, and shell syntax errors before those tools
are available.
"""
from pathlib import Path
import subprocess,re
ROOT=Path(__file__).resolve().parents[1]
issues=[]; notes=[]

# Shell syntax checks available in the current environment.
for rel in ['tools/bootstrap_eda.sh','tools/env_eda.sh']:
    p=ROOT/rel
    if not p.is_file(): issues.append(f'missing {rel}'); continue
    cp=subprocess.run(['bash','-n',str(p)],text=True,capture_output=True)
    if cp.returncode: issues.append(f'{rel}: bash -n failed: {cp.stderr.strip()}')
    else: notes.append(f'{rel}: bash syntax PASS')

required_text={
 'Makefile':['REQUIRE_EDA=1 $(PYTHON) scripts/run_all_checks.py','scripts/run_asic_timing.py'],
 '.github/workflows/rtl-ci.yml':['YosysHQ/setup-oss-cad-suite@v4','python-reference:','rtl-simulation:','make rtl','make rtl-coverage','make rtl-perf','make lint','make formal','make synth','actions/upload-artifact@v4'],
 'tools/bootstrap_eda.sh':['oss-cad-suite-linux-x64','releases/latest','export PATH="$SUITE/bin:$PATH"'],
 'tools/bootstrap_eda.ps1':['oss-cad-suite-windows-x64','releases/latest','bin\\verilator.exe'],
 'tools/run_full_verification.ps1':['REQUIRE_EDA','scripts/run_all_checks.py','verilator','yosys','sby'],
 'scripts/run_formal.py':["[yosys,'-m','slang'","env['PATH']=td+os.pathsep",'formal/core.sby'],
 'formal/core.sby':['read_slang','formal/core_harness.sv','-D FORMAL'],
 'scripts/run_asic_timing.py':['LIBERTY_FILE','CLOCK_PERIOD_NS','SDC_FILE','dfflibmap -liberty','abc -liberty'],
}
for rel,needles in required_text.items():
    p=ROOT/rel
    if not p.is_file(): issues.append(f'missing {rel}'); continue
    s=p.read_text(errors='ignore')
    for n in needles:
        if n not in s: issues.append(f'{rel}: required marker missing: {n}')
    notes.append(f'{rel}: markers checked={len(needles)}')

workflow=(ROOT/'.github/workflows/rtl-ci.yml').read_text(errors='ignore')
if 'continue-on-error:' in workflow:
    issues.append('.github/workflows/rtl-ci.yml: mandatory workflow must not use continue-on-error')

# Make sure strict EDA mode does not silently accept return-code 2.
r=(ROOT/'scripts/run_all_checks.py').read_text()
if "p.returncode==2 and not strict_eda" not in r:
    issues.append('scripts/run_all_checks.py: strict EDA missing-tool gate not found')

# PowerShell scripts cannot be executed in this Linux sandbox if pwsh is absent,
# but basic delimiter balance still catches accidental truncation.
for rel in ['tools/bootstrap_eda.ps1','tools/run_full_verification.ps1']:
    s=(ROOT/rel).read_text(errors='ignore')
    if s.count('{')!=s.count('}'):
        issues.append(f'{rel}: unbalanced braces')
    if s.count('(')!=s.count(')'):
        issues.append(f'{rel}: unbalanced parentheses')

out=ROOT/'reports'/'tool_flow_audit.txt'
lines=['EDA/CI TOOL FLOW SOURCE AUDIT (not EDA execution)','',f'Issues: {len(issues)}']+notes
if issues: lines += ['']+issues
out.write_text('\n'.join(lines)+'\n')
print(out.read_text(),end='')
raise SystemExit(1 if issues else 0)
