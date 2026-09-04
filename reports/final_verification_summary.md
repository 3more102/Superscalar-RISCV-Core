# Final Verification Summary — GitHub CI Run #48

This file records executed evidence for source/tool-flow commit [`9a620d9d2b6ab2970b3a54f6852fae9684afe5ad`](https://github.com/3more102/Superscalar-RISCV-Core/commit/9a620d9d2b6ab2970b3a54f6852fae9684afe5ad), validated by GitHub Actions run [#48 / `33900989274`](https://github.com/3more102/Superscalar-RISCV-Core/actions/runs/33900989274).

All five mandatory jobs completed successfully on the same revision: Python/reference verification, RTL simulation/coverage/performance, Verilator lint, formal verification, and Yosys synthesis.

| Item | Executed result |
|---|---|
| Python tests | **25/25 PASS** |
| Directed architectural reference tests | **41/41 PASS** |
| Random architectural reference seeds | **500/500 PASS** |
| Required ISA mnemonics exercised | **47/47** |
| Reference/stimulus functional coverage | **54/54 points PASS** |
| Reference-model committed instructions checked | **47,280** |
| Restoring-divider algorithm stress | **20,000/20,000 PASS** |
| Front-end replay stress | **100,000/100,000 cycles PASS**, issued=126,494, redirects=208 |
| Cycle-oriented microarchitecture workloads | **500/500 completed** |
| RTL differential regression | **91/91 PASS** — 41 directed + 50 random |
| RTL functional event coverage | **58/58 points PASS** |
| RTL line code coverage | **98.35%** — 416/423 |
| RTL branch code coverage | **99.34%** — 303/305 |
| RTL toggle code coverage | **75.00%** — 10,636/14,182 |
| Code-coverage source completeness | **9/9 measurable RTL files present**; `riscv_pkg.sv` definition-only |
| Verilator lint policy | **PASS** — warnings=12, allowed=`UNUSEDPARAM`,`UNUSEDSIGNAL`, unexpected=0 |
| Formal issue target | **PASS**, Yosys SAT `SUCCESS` |
| Formal ALU/branch target | **PASS**, Yosys SAT `SUCCESS` |
| Formal core control/order target | **PASS through 32 cycles** — base-case depth 32 |
| Generic Yosys synthesis | **PASS**, 43,289 generic primitive cells, Yosys `check`: 0 problems |
| Technology-mapped ASIC synthesis | **NOT RUN** — no characterized `LIBERTY_FILE` supplied |
| Characterized STA / WNS / TNS / Fmax | **NOT RUN / NOT CLAIMED** |
| Power / physical area | **NOT RUN / NOT CLAIMED** |

## RTL-measured performance

The RTL performance flow compiles the same design twice, changing only `ENABLE_DUAL_ISSUE`.

| Program | Retired | Single cycles | 2-wide cycles | Single IPC | 2-wide IPC | RTL speedup | Dual-issue cycles |
|---|---:|---:|---:|---:|---:|---:|---:|
| dependency_100 | 100 | 105 | 105 | 0.952 | 0.952 | **1.000x** | 0 |
| independent_200 | 200 | 205 | 105 | 0.976 | **1.905** | **1.952x** | 100 |

These are **RTL simulator measurements**, not model estimates.

## RTL functional-event coverage

The directed RTL suite closed **58/58** tracked event points. Observed events include all six branch classes with taken/not-taken outcomes, all five load variants, all three stores and required byte/halfword lanes, all eight RV32M operations, all tracked trap classes, dual issue, single issue, RAW/WAW/structural blocking, redirects, EX/MEM/WB forwarding, load-use stall, and divider stall.

Representative totals from run #48 include: dual_issue=59, single_issue=203, pair_raw=60, pair_waw=17, structural_block=552, redirect=20, forward_ex=71, forward_mem=24, forward_wb=18, load_use_stall=1, divider_stall=126.

## Verilator RTL code coverage

Run #48 also executed a separate, instrumented 91-program Verilator pass for RTL-only code coverage. Annotated testbench points are excluded from the percentages.

| Coverage type | Covered | Total | Result |
|---|---:|---:|---:|
| Line | 416 | 423 | **98.35%** |
| Branch | 303 | 305 | **99.34%** |
| Toggle | 10,636 | 14,182 | **75.00%** |

Coverage evidence contains **9/9 measurable synthesizable RTL module files**. `rtl/common/riscv_pkg.sv` is explicitly recorded as a definition-only SystemVerilog package; Verilator does not emit executable coverage points for declarations/typedefs alone. The gate therefore requires every executable RTL source to appear in LCOV and annotated output, while reporting definition-only packages separately.

No arbitrary percentage threshold is enforced in this first measured baseline. The gate fails for simulator/coverage errors, failed tests, missing executable RTL sources, or vacuous line/branch/toggle classes. These metrics are separate from the project's 58/58 functional-event coverage.

## Formal proof boundary

The executed formal engine is **Yosys-Slang + Yosys SAT**.

- `issue`: `PASS rc=0 mode=seq depth=1`.
- `alu_branch`: `PASS rc=0 mode=seq depth=1`.
- `core`: `PASS rc=0 mode=base32 depth=32`.

The core target is intentionally compositional. RF read values plus ALU/MUL/DIV results and branch outcome are explicit formal cutpoints. The formal-flow source audit in the retained run #48 artifact reports **3 targets, 0 issues**. This means the core control/order properties must hold for arbitrary values at those datapath boundaries; it does **not** claim a monolithic proof of every RV32IM arithmetic operation across 32 cycles.

The in-core assertions cover issue legality, front-end adjacency/alignment, slot1 replay, redirect behavior, lane1 restrictions, precise exception ordering, memory-side-effect legality, halted-state suppression, divider stall behavior, and temporal pipeline movement.

## Generic synthesis boundary

Generic Yosys synthesis completed with:

- wires: 6,742
- wire bits: 78,709
- public wires: 223
- cells: **43,289**
- Yosys `check`: **0 problems**

The cell count is a Yosys generic-primitive count after generic technology mapping. It is **not** a standard-cell area, gate-equivalent, timing, or power result.

## Evidence provenance

See [`docs/ci_evidence.md`](../docs/ci_evidence.md) for the exact run, artifact identifiers, SHA-256 artifact digests, formal solver markers, lint policy, synthesis provenance, and code-coverage interpretation.
