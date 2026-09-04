# Final Verification Summary — GitHub CI Run #20

This file records executed evidence for commit [`94f688763d81035057f7fe00959bfd4f3e3948fc`](https://github.com/3more102/Superscalar-RISCV-Core/commit/94f688763d81035057f7fe00959bfd4f3e3948fc), validated by GitHub Actions run [`33873379783`](https://github.com/3more102/Superscalar-RISCV-Core/actions/runs/33873379783).

All five mandatory jobs completed successfully on the same RTL revision: Python/reference verification, RTL simulation/coverage/performance, Verilator lint, formal verification, and Yosys synthesis.

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
| Verilator lint policy | **PASS** — warnings=12, allowed=`UNUSEDPARAM`,`UNUSEDSIGNAL`, unexpected=0 |
| Formal issue target | **PASS**, Yosys SAT `SUCCESS` |
| Formal ALU/branch target | **PASS**, Yosys SAT `SUCCESS` |
| Formal core control/order target | **PASS through 32 cycles** — `proved base case for 32 steps: SUCCESS!` |
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

Representative totals from the run include: dual_issue=59, single_issue=203, pair_raw=60, pair_waw=17, structural_block=552, redirect=20, forward_ex=71, forward_mem=24, forward_wb=18, load_use_stall=1, divider_stall=126.

## Formal proof boundary

The executed formal engine is **Yosys-Slang + Yosys SAT**.

- `issue`: symbolic primary-input combinational proof, depth 1.
- `alu_branch`: symbolic primary-input RTL-vs-expected-output proof, depth 1.
- `core`: bounded base-case proof through **32 cycles**.

The core target is intentionally compositional. RF read values plus ALU/MUL/DIV results and branch outcome are explicit formal cutpoints. The solver log confirms all intended cutpoints were created before the 32-cycle proof. This means the core control/order properties must hold for arbitrary values at those datapath boundaries; it does **not** claim a monolithic proof of every RV32IM arithmetic operation across 32 cycles.

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

See [`docs/ci_evidence.md`](../docs/ci_evidence.md) for the exact run, artifact identifiers, SHA-256 artifact digests, formal solver markers, lint policy, and synthesis provenance.
