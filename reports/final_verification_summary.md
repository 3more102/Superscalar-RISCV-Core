# Final Verification Summary — Current Environment

| Item | Result |
|---|---|
| Project structure | PASS |
| Python tests | **25/25 PASS** |
| Directed architectural tests | **41/41 PASS** |
| Random architectural seeds | **500/500 PASS** |
| Required ISA mnemonics exercised | **47/47** |
| Reference/stimulus coverage | **54/54 points PASS** — not RTL code coverage |
| Reference-model committed instructions checked | **47,280** |
| Restoring-divider algorithm stress | **20000/20000 PASS** |
| Front-end replay stress | **100000/100000 cycles PASS**, issued=126494, redirects=208 |
| Cycle-oriented microarchitecture stress | **500/500 completed** |
| Static RTL source audit | **PASS** |
| Formal-flow source audit | **PASS** — configuration integrity only, not proof |
| EDA/CI tool-flow source audit | **PASS** — configuration integrity only |
| RTL compile/simulation | **TOOL UNAVAILABLE** |
| RTL functional coverage | **TOOL UNAVAILABLE** |
| RTL single-vs-dual performance | **TOOL UNAVAILABLE** |
| Verilator lint | **TOOL UNAVAILABLE** |
| Formal execution | **TOOL UNAVAILABLE** |
| Generic Yosys synthesis | **TOOL UNAVAILABLE** |
| Technology-mapped ASIC synthesis | **ASIC MAPPED SYNTHESIS: NOT RUN — LIBERTY_FILE was not supplied.** |
| Characterized STA | **ASIC STA: NOT RUN — LIBERTY_FILE was not supplied.** |

## Executed model-only performance evidence

* independent ALU issue-policy stream: **2.000 issue IPC**, dual cycles=100
* dependency chain: **1.000 issue IPC**, dual cycles=0
* cycle-oriented timing model: **500/500** random workloads; mean 2-wide IPC **0.615**, mean model speedup **1.187x** versus forced single issue

> These performance values are executable **model results, not SystemVerilog RTL cycle measurements**.

## Formal and precise-ordering hardening

* complete-core formal target uses `formal/core_harness.sv`, which constrains reset before symbolic instruction/data traffic
* in-core formal invariants cover front-end alignment/adjacency, lane1 legality, slot1 replay, redirect flush, EX→MEM movement, precise exceptions, and memory-side-effect ordering
* SBY targets explicitly load `slang` before `read_slang`; `scripts/audit_formal_flow.py` verifies target/file/top consistency even when SBY itself is unavailable
* `halted` gates commit, register-file writes, and data-memory activity; directed precise-trap tests keep younger state from becoming architectural

## ASIC timing policy

`make asic` requires a real `LIBERTY_FILE`. STA additionally requires an explicit `SDC_FILE` or user-supplied `CLOCK_PERIOD_NS`. No default frequency/WNS/TNS/area/power value is invented. See `docs/asic_timing_flow.md`.

## Remaining hardware-execution gates

RTL compile/commit equivalence, RTL coverage, RTL IPC, lint, formal solver execution, technology mapping, and characterized STA remain open whenever their actual tools/library are unavailable. Missing tools are never converted into PASS.
