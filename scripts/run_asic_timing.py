#!/usr/bin/env python3
"""Technology-map the core and optionally run STA against a user-supplied Liberty.

Required environment:
  LIBERTY_FILE=/absolute/path/to/stdcells.lib

Optional timing environment:
  CLOCK_PERIOD_NS=<positive number>   # required to run STA
  SDC_FILE=/absolute/path/to/file.sdc # overrides generated clock constraint

No default frequency, WNS, area or power number is invented.  If the required
library/tool/constraint is absent the report says exactly what was not run.
"""
from pathlib import Path
import os, shutil, subprocess, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
SYNTH_RPT=ROOT/'reports'/'synthesis'/'asic_mapped_synthesis_report.txt'
TIMING_RPT=ROOT/'reports'/'timing'/'asic_sta_report.txt'
NETLIST=ROOT/'reports'/'synthesis'/'superscalar_core_mapped.v'
SYNTH_RPT.parent.mkdir(parents=True,exist_ok=True)
TIMING_RPT.parent.mkdir(parents=True,exist_ok=True)

lib_s=os.environ.get('LIBERTY_FILE','').strip()
if not lib_s:
    msg='ASIC MAPPED SYNTHESIS: NOT RUN — LIBERTY_FILE was not supplied.\nNo cell area/count or timing number is claimed.\n'
    SYNTH_RPT.write_text(msg)
    TIMING_RPT.write_text('ASIC STA: NOT RUN — LIBERTY_FILE was not supplied.\n')
    print(msg,end='')
    raise SystemExit(2)
lib=Path(lib_s).expanduser().resolve()
if not lib.is_file():
    msg=f'ASIC MAPPED SYNTHESIS: NOT RUN — Liberty file does not exist: {lib}\n'
    SYNTH_RPT.write_text(msg); TIMING_RPT.write_text(msg); print(msg,end=''); raise SystemExit(2)

yosys=shutil.which('yosys')
if not yosys:
    msg='ASIC MAPPED SYNTHESIS: TOOL UNAVAILABLE — yosys not found.\n'
    SYNTH_RPT.write_text(msg); TIMING_RPT.write_text('ASIC STA: NOT RUN — mapped netlist unavailable.\n'); print(msg,end=''); raise SystemExit(2)

rtl=[
 'rtl/common/riscv_pkg.sv','rtl/decode/decoder.sv','rtl/execute/alu.sv',
 'rtl/branch/branch_unit.sv','rtl/core/register_file.sv','rtl/issue/dual_issue_unit.sv',
 'rtl/mdu/mul_unit.sv','rtl/mdu/div_unit.sv','rtl/memory/load_store_unit.sv',
 'rtl/core/superscalar_core.sv'
]
probe=subprocess.run([yosys,'-m','slang','-p','help read_slang'],cwd=ROOT,text=True,capture_output=True)
slang_ok=probe.returncode==0
q=lambda p: str(p).replace('\\','/')
if slang_ok:
    read_cmd='read_slang ' + ' '.join(rtl) + ' --top superscalar_core'
    yosys_cmd=[yosys,'-m','slang','-p']
    frontend='yosys-slang'
else:
    # Native Yosys may not accept all package/struct constructs. Keep this as a
    # transparent fallback and propagate any parser failure into the report.
    read_cmd='read_verilog -sv ' + ' '.join(rtl)
    yosys_cmd=[yosys,'-p']
    frontend='yosys native read_verilog -sv fallback'

script='; '.join([
    read_cmd,
    'hierarchy -check -top superscalar_core',
    'proc', 'opt', 'memory', 'opt', 'techmap', 'opt',
    f'dfflibmap -liberty {q(lib)}',
    f'abc -liberty {q(lib)}',
    'clean -purge',
    f'stat -top superscalar_core -liberty {q(lib)}',
    f'write_verilog -noattr -noexpr -nodec {q(NETLIST)}'
])
cp=subprocess.run(yosys_cmd+[script],cwd=ROOT,text=True,capture_output=True)
SYNTH_RPT.write_text(
    f'Frontend: {frontend}\nLiberty: {lib}\nNetlist: {NETLIST}\nReturn code: {cp.returncode}\n\n'
    +cp.stdout+cp.stderr
)
print(SYNTH_RPT.read_text(),end='')
if cp.returncode!=0:
    TIMING_RPT.write_text('ASIC STA: NOT RUN — technology-mapped synthesis failed.\n')
    raise SystemExit(cp.returncode)

# Timing is deliberately opt-in: an explicit clock target or an SDC is needed.
sdc_s=os.environ.get('SDC_FILE','').strip()
period_s=os.environ.get('CLOCK_PERIOD_NS','').strip()
if not sdc_s and not period_s:
    TIMING_RPT.write_text(
        'ASIC STA: NOT RUN — mapped synthesis completed, but neither SDC_FILE nor '
        'CLOCK_PERIOD_NS was supplied. No timing number is claimed.\n'
    )
    print(TIMING_RPT.read_text(),end='')
    raise SystemExit(0)

sta=shutil.which('sta') or shutil.which('opensta')
if not sta:
    TIMING_RPT.write_text('ASIC STA: TOOL UNAVAILABLE — OpenSTA executable (sta/opensta) not found.\n')
    print(TIMING_RPT.read_text(),end='')
    raise SystemExit(2)

if sdc_s:
    sdc=Path(sdc_s).expanduser().resolve()
    if not sdc.is_file():
        TIMING_RPT.write_text(f'ASIC STA: NOT RUN — SDC_FILE does not exist: {sdc}\n')
        print(TIMING_RPT.read_text(),end=''); raise SystemExit(2)
    constraint=f'read_sdc {{{q(sdc)}}}'
    constraint_desc=f'SDC: {sdc}'
else:
    try:
        period=float(period_s)
        if period<=0: raise ValueError
    except ValueError:
        TIMING_RPT.write_text(f'ASIC STA: NOT RUN — CLOCK_PERIOD_NS must be positive, got {period_s!r}.\n')
        print(TIMING_RPT.read_text(),end=''); raise SystemExit(2)
    constraint=f'create_clock -name clk -period {period:g} [get_ports clk]'
    constraint_desc=f'Generated clock constraint: {period:g} ns (user supplied)'

with tempfile.NamedTemporaryFile('w',suffix='.tcl',delete=False,dir=ROOT/'reports'/'timing') as f:
    tcl=Path(f.name)
    f.write(f'''read_liberty {{{q(lib)}}}\nread_verilog {{{q(NETLIST)}}}\nlink_design superscalar_core\n{constraint}\ncheck_setup\nreport_checks -path_delay max -group_count 10 -endpoint_count 10\nreport_worst_slack -max\nreport_tns\n''')
try:
    sp=subprocess.run([sta,str(tcl)],cwd=ROOT,text=True,capture_output=True)
finally:
    try: tcl.unlink()
    except OSError: pass
TIMING_RPT.write_text(
    f'Liberty: {lib}\nNetlist: {NETLIST}\n{constraint_desc}\nSTA tool: {sta}\nReturn code: {sp.returncode}\n\n'
    +sp.stdout+sp.stderr
)
print(TIMING_RPT.read_text(),end='')
raise SystemExit(sp.returncode)
