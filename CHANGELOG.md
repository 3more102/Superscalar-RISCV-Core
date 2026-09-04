# Changelog

All notable engineering milestones for this repository are recorded here. Results are listed only when backed by retained reports or executed tool output.

## Unreleased

### Verification closure and repository maintenance

The latest fully green source/tool-flow baseline is GitHub Actions **run #48** (`33900989274`) on commit `9a620d9d2b6ab2970b3a54f6852fae9684afe5ad`. All five mandatory jobs completed successfully on that same revision.

Executed evidence on the current engineering baseline:

- Python verification: **25/25 PASS**
- directed architectural reference programs: **41/41 PASS**
- deterministic random architectural seeds: **500/500 PASS**
- required RV32IM mnemonics exercised: **47/47**
- reference/stimulus coverage: **54/54 PASS**
- architectural commits checked: **47,280**
- restoring-divider differential comparisons: **20,000/20,000 PASS**
- front-end replay stress: **100,000/100,000 cycles PASS**
- RTL differential regression under Verilator: **91/91 PASS** — 41 directed + 50 random
- RTL functional-event coverage: **58/58 PASS**
- Verilator RTL line coverage: **98.35%** — 416/423
- Verilator RTL branch coverage: **99.34%** — 303/305
- Verilator RTL toggle coverage: **75.00%** — 10,636/14,182
- RTL code-coverage source completeness: **9/9 measurable module files present**; definition-only `riscv_pkg.sv` reported separately
- Verilator lint: **PASS** — 0 unexpected warning categories
- formal issue proof: **PASS**
- formal ALU/branch equivalence proof: **PASS**
- formal core control/order proof: **PASS through 32 cycles**
- generic Yosys synthesis: **PASS** — 43,289 generic primitive cells, 0 `check` problems
- RTL single-vs-dual performance: dependency chain **1.000x**, independent ALU stream **1.952x** speedup with 2-wide IPC **1.905**

### RTL code-coverage baseline

A dedicated `make rtl-code-coverage` flow now reruns all 91 RTL programs with Verilator code-coverage instrumentation, merges per-test databases, excludes testbench instrumentation from reported percentages, and validates that every measurable synthesizable RTL source appears in coverage evidence.

The first baseline intentionally does **not** impose an arbitrary pass percentage. It fails on broken instrumentation/collection, test failures, missing executable RTL sources, or vacuous line/branch/toggle coverage classes. Functional-event coverage remains a separate 58/58 semantic metric.

Repository maintenance also includes strict multi-job CI, weekly reproducibility execution, Dependabot for GitHub Actions, issue/PR templates, CODEOWNERS, retained CI artifact digests, and repository-presentation metadata.

Technology-characterized ASIC area, STA, WNS/TNS, maximum frequency, and power remain intentionally unclaimed because no characterized standard-cell Liberty/constraint set has been supplied.

## v0.2.0 — Verification Infrastructure Release

Released: **2026-09-04**

### Architecture and RTL

- synthesizable 32-bit RV32IM processor baseline
- 2-wide fetch and decode with conservative in-order dual issue
- ordered two-entry front-end buffer with slot1 replay
- RAW/WAW/resource pairing checks
- lane0 ALU/branch/LSU/MDU plus lane1 integer-ALU execution
- EX/MEM/WB forwarding instrumentation and load-use handling
- static-not-taken redirect/flush baseline
- IALIGN=32 control-transfer alignment behavior and JALR bit-0 clearing
- byte/half/word LSU formatting and misalignment handling
- RV32M multiply forms and configurable-latency restoring divider
- precise baseline trap/halt quiescence for younger architectural side effects

### Verification and tooling infrastructure

- Python RV32IM architectural reference model
- deterministic directed and random program generation
- commit-trace RTL comparison infrastructure
- issue-policy, pipeline timing, front-end replay, and divider differential models
- SystemVerilog assertions and formal harnesses
- Verilator simulation/lint flows
- Yosys-Slang/Yosys SAT formal automation
- generic Yosys synthesis
- optional Liberty-based technology mapping and STA infrastructure
- OSS CAD Suite GitHub Actions integration

### Project status language

This release is an **engineering/educational RTL release with executable verification infrastructure**. It is not presented as silicon-proven, production-ready, security-certified, or tapeout-ready hardware. Technology-dependent PPA claims require a real standard-cell library and implementation flow.
