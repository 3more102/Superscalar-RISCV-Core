#!/usr/bin/env python3
"""Portable source audit. Intentionally NOT labeled as HDL lint/compile."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
rtl=sorted((ROOT/'rtl').rglob('*.sv'))
tb=sorted((ROOT/'tb').rglob('*.sv'))
files=rtl+tb
issues=[]; stats={}
for p in files:
    s=p.read_text()
    rel=str(p.relative_to(ROOT))
    # Strip comments/strings approximately before lexical balance checks.
    t=re.sub(r'/\*.*?\*/','',s,flags=re.S)
    t=re.sub(r'//.*','',t)
    t=re.sub(r'"(?:\\.|[^"\\])*"','""',t)
    for a,b in [('(',')'),('[',']'),('{','}')]:
        if t.count(a)!=t.count(b): issues.append(f'{rel}: unbalanced {a}{b}: {t.count(a)} vs {t.count(b)}')
    mods=len(re.findall(r'\bmodule\b',t)); ends=len(re.findall(r'\bendmodule\b',t))
    if mods!=ends: issues.append(f'{rel}: module/endmodule mismatch {mods}/{ends}')
    # Synthesizable RTL directory must not contain simulation-only time control
    # or process termination/debug tasks.
    if p in rtl:
        if re.search(r'(^|[^#])#\s*\d',t): issues.append(f'{rel}: delay control found in synthesizable RTL')
        if re.search(r'\b(initial|final)\b',t): issues.append(f'{rel}: initial/final block found in synthesizable RTL')
        if re.search(r'\$(display|write|fwrite|finish|stop|fatal)\b',t): issues.append(f'{rel}: simulation task found in synthesizable RTL')
    stats[rel]={'lines':len(s.splitlines()),'always_ff':len(re.findall(r'\balways_ff\b',s)),'always_comb':len(re.findall(r'\balways_comb\b',s))}

required=['rtl/common/riscv_pkg.sv','rtl/core/superscalar_core.sv','rtl/core/register_file.sv',
          'rtl/decode/decoder.sv','rtl/issue/dual_issue_unit.sv','rtl/execute/alu.sv',
          'rtl/branch/branch_unit.sv','rtl/mdu/mul_unit.sv','rtl/mdu/div_unit.sv',
          'rtl/memory/load_store_unit.sv']
for r in required:
    if not (ROOT/r).exists(): issues.append(f'missing required file {r}')

# Architecture-specific source invariants (still textual, not semantic lint).
checks={
 'rtl/mdu/div_unit.sv':['restoring_step','STEPS_PER_CYCLE','special_result_q'],
 'rtl/issue/dual_issue_unit.sv':['pair_raw','pair_waw','pair_structural','issue1 = issue0'],
 'rtl/core/superscalar_core.sv':['commit1_valid = !halted && wb1_q.valid','redirect_valid','d0_load_use_hazard','perf_dual_issue_cycles'],
}
for rel,needles in checks.items():
    text=(ROOT/rel).read_text()
    for needle in needles:
        if needle not in text: issues.append(f'{rel}: expected architecture marker missing: {needle}')

text=['STATIC RTL SOURCE AUDIT (not a compiler/linter)','',
      f'Files inspected: {len(files)}',f'RTL files: {len(rtl)}',f'TB/assertion files: {len(tb)}',f'Issues: {len(issues)}']
if issues: text += ['']+issues
text += ['', 'Per-file stats:']+[f'{k}: lines={v["lines"]} always_ff={v["always_ff"]} always_comb={v["always_comb"]}' for k,v in stats.items()]
out=ROOT/'reports'/'static_rtl_audit.txt'; out.write_text('\n'.join(text)+'\n')
print(out.read_text(),end='')
raise SystemExit(1 if issues else 0)
