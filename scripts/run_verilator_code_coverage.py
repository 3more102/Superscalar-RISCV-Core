#!/usr/bin/env python3
"""Run RTL-only Verilator line/branch/toggle code coverage.

This is separate from the project's architectural functional-event coverage.
It compiles an instrumented Verilator binary, runs the same 41 directed and
50 deterministic random programs used by the RTL regression, merges per-test
coverage databases, and reports coverage points from synthesizable RTL files
only (the testbench is excluded from the reported percentages).

Definition-only SystemVerilog packages are recorded but are not required to
produce executable coverage points. Every synthesizable RTL source that is
not package-only must appear in both the LCOV database and annotated output.

No minimum percentage is enforced in the first baseline. The gate fails only
if the simulator/coverage tools fail, a test fails to execute, an executable
RTL source is missing from coverage evidence, or an expected coverage class
contains no measurable RTL points.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COV = ROOT / "reports" / "coverage"
RAW = COV / "verilator_raw"
ANNOTATED = COV / "verilator_annotated"
TMP = ROOT / "sim" / "codecov_tmp"
OBJ = ROOT / "sim" / "obj_codecov"
COV.mkdir(parents=True, exist_ok=True)

verilator = shutil.which("verilator")
verilator_coverage = shutil.which("verilator_coverage")
if not verilator or not verilator_coverage:
    text = (
        "# Verilator RTL Code Coverage\n\n"
        "**TOOL UNAVAILABLE** — requires both `verilator` and "
        "`verilator_coverage`.\n"
    )
    (COV / "verilator_code_coverage.md").write_text(text)
    print(text, end="")
    raise SystemExit(2)

for p in (RAW, ANNOTATED, TMP, OBJ):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)

files = [
    str(ROOT / line.strip())
    for line in (ROOT / "sim" / "filelist.f").read_text().splitlines()
    if line.strip()
]
rtl_rel = [
    line.strip()
    for line in (ROOT / "sim" / "rtl_filelist.f").read_text().splitlines()
    if line.strip()
]
rtl_names = {Path(p).name for p in rtl_rel}
package_only_names = {
    Path(rel).name
    for rel in rtl_rel
    if re.search(r"^\s*package\s+\w+", (ROOT / rel).read_text(errors="ignore"), re.MULTILINE)
    and not re.search(r"^\s*module\s+\w+", (ROOT / rel).read_text(errors="ignore"), re.MULTILINE)
}
measurable_rtl_names = rtl_names - package_only_names

compile_cmd = [
    verilator,
    "--binary",
    "--timing",
    "--assert",
    "-Wall",
    "-Wno-fatal",
    "--coverage-line",
    "--coverage-toggle",
    "--top-module",
    "tb_superscalar_core",
    "--Mdir",
    str(OBJ),
    *files,
]
cp = subprocess.run(compile_cmd, cwd=ROOT, text=True, capture_output=True)
(COV / "verilator_code_coverage_compile.log").write_text(cp.stdout + cp.stderr)
if cp.returncode:
    print(cp.stdout, cp.stderr)
    raise SystemExit(cp.returncode)

simv = OBJ / "Vtb_superscalar_core"
if not simv.is_file():
    raise SystemExit(f"coverage simulator missing: {simv}")

sys.path.insert(0, str(ROOT / "scripts"))
from gen_random_program import program as random_program  # noqa: E402
import riscv_encode as E  # noqa: E402

programs: list[tuple[str, Path]] = []
for hp in sorted((ROOT / "sw" / "hex").glob("[0-9][0-9]_*.hex")):
    programs.append((hp.stem, hp))

directed_count = len(programs)
rnd = TMP / "random"
rnd.mkdir(parents=True, exist_ok=True)
for seed in range(1, 51):
    hp = rnd / f"random_seed_{seed:04d}.hex"
    E.write_hex(hp, random_program(seed, 80))
    programs.append((hp.stem, hp))

failures: list[str] = []
for name, hp in programs:
    trace = TMP / f"{name}_trace.csv"
    functional = TMP / f"{name}_functional.txt"
    status = TMP / f"{name}_status.txt"
    dat = RAW / f"{name}.dat"
    args = [
        str(simv),
        f"+HEX={hp}",
        f"+TRACE={trace}",
        f"+COVERAGE={functional}",
        f"+STATUS={status}",
        f"+verilator+coverage+file+{dat}",
    ]
    run = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    (TMP / f"{name}.log").write_text(run.stdout + run.stderr)
    if run.returncode:
        failures.append(f"{name}: simulator rc={run.returncode}")
    elif not dat.is_file():
        failures.append(f"{name}: coverage database not produced")

if failures:
    out = "# Verilator RTL Code Coverage\n\nFAIL\n\n" + "\n".join(
        f"- {x}" for x in failures
    ) + "\n"
    (COV / "verilator_code_coverage.md").write_text(out)
    print(out, end="")
    raise SystemExit(1)

raw_files = sorted(RAW.glob("*.dat"))
merged = COV / "verilator_code_coverage.dat"
info = COV / "verilator_code_coverage.info"
summary_txt = COV / "verilator_code_coverage_tool_summary.txt"

merge = subprocess.run(
    [verilator_coverage, "--write", str(merged), *map(str, raw_files)],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
if merge.returncode:
    print(merge.stdout, merge.stderr)
    raise SystemExit(merge.returncode)

summary = subprocess.run(
    [verilator_coverage, "--report", "summary", str(merged)],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
summary_txt.write_text(summary.stdout + summary.stderr)
if summary.returncode:
    print(summary.stdout, summary.stderr)
    raise SystemExit(summary.returncode)

lcov = subprocess.run(
    [verilator_coverage, "--write-info", str(info), str(merged)],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
if lcov.returncode:
    print(lcov.stdout, lcov.stderr)
    raise SystemExit(lcov.returncode)

lcov_source_names = {
    Path(line[3:]).name
    for line in info.read_text(errors="ignore").splitlines()
    if line.startswith("SF:")
}
missing_from_lcov = sorted(measurable_rtl_names - lcov_source_names)

annotate = subprocess.run(
    [
        verilator_coverage,
        "--annotate",
        str(ANNOTATED),
        "--annotate-all",
        "--annotate-points",
        "--annotate-min",
        "1",
        str(merged),
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
(COV / "verilator_code_coverage_annotate.log").write_text(
    annotate.stdout + annotate.stderr
)
if annotate.returncode:
    print(annotate.stdout, annotate.stderr)
    raise SystemExit(annotate.returncode)

# Verilator 5.050+ annotates individual points as, for example:
#   +000010 point: type=branch comment=if ...
#   -000000 point: type=toggle comment=foo[0]:0->1 ...
point_re = re.compile(r"^\s*([+-])\d+\s+point:\s+type=(line|branch|toggle)\b")
counts = {
    "line": {"covered": 0, "total": 0},
    "branch": {"covered": 0, "total": 0},
    "toggle": {"covered": 0, "total": 0},
}
matched_files: set[str] = set()
for p in ANNOTATED.rglob("*"):
    if not p.is_file() or p.name not in measurable_rtl_names:
        continue
    matched_files.add(p.name)
    for line in p.read_text(errors="ignore").splitlines():
        m = point_re.match(line)
        if not m:
            continue
        covered, kind = m.groups()
        counts[kind]["total"] += 1
        if covered == "+":
            counts[kind]["covered"] += 1

for kind, vals in counts.items():
    vals["percent"] = (
        100.0 * vals["covered"] / vals["total"] if vals["total"] else None
    )

missing_annotated = sorted(measurable_rtl_names - matched_files)
valid = (
    not missing_from_lcov
    and not missing_annotated
    and all(counts[k]["total"] > 0 for k in counts)
)
result = {
    "label": "VERILATOR RTL CODE COVERAGE",
    "backend": "Verilator",
    "tests_executed": len(programs),
    "directed_tests": directed_count,
    "random_tests": 50,
    "rtl_sources_total": len(rtl_names),
    "definition_only_packages_excluded": sorted(package_only_names),
    "measurable_rtl_files_expected": len(measurable_rtl_names),
    "measurable_rtl_files_annotated": len(matched_files),
    "missing_measurable_rtl_from_lcov": missing_from_lcov,
    "missing_measurable_rtl_from_annotation": missing_annotated,
    "coverage": counts,
    "coverage_threshold_enforced": False,
    "valid_non_vacuous_report": valid,
}
(COV / "verilator_code_coverage.json").write_text(json.dumps(result, indent=2) + "\n")

lines = [
    "# Verilator RTL Code Coverage",
    "",
    "Coverage source: **Verilator instrumented RTL simulation**.",
    "",
    f"Programs executed: **{len(programs)}** — {directed_count} directed + 50 deterministic random.",
    f"Measurable synthesizable RTL files: **{len(matched_files)}/{len(measurable_rtl_names)}**.",
]
if package_only_names:
    lines.append(
        "Definition-only package sources excluded from executable coverage: "
        + ", ".join(f"`{x}`" for x in sorted(package_only_names))
        + "."
    )
lines += [
    "",
    "| Coverage type | Covered points | Total points | Coverage |",
    "|---|---:|---:|---:|",
]
for kind in ("line", "branch", "toggle"):
    vals = counts[kind]
    pct = "N/A" if vals["percent"] is None else f"{vals['percent']:.2f}%"
    lines.append(
        f"| {kind.title()} | {vals['covered']} | {vals['total']} | **{pct}** |"
    )
lines += [
    "",
    "The percentages above are **RTL-only**: annotated testbench files are excluded.",
    "Definition-only packages are reported separately because Verilator does not emit executable coverage points for declarations/typedefs alone.",
    "A coverage point is counted as covered when it executed/toggled at least once (`--annotate-min 1`).",
    "No arbitrary pass-percentage threshold is enforced in this first measured baseline; the gate verifies instrumentation, collection, merge, all measurable RTL sources, and all three coverage classes are non-vacuous.",
    "This report is separate from the project's 58/58 architectural functional-event coverage points.",
]
if missing_from_lcov:
    lines += ["", "Missing measurable RTL files from LCOV: " + ", ".join(missing_from_lcov)]
if missing_annotated:
    lines += ["", "Missing measurable RTL files from annotation: " + ", ".join(missing_annotated)]
out = "\n".join(lines) + "\n"
(COV / "verilator_code_coverage.md").write_text(out)
print(out, end="")
raise SystemExit(0 if valid else 1)
