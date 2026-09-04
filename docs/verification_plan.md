# Verification Plan

## Strategy

Verification is split into five independently interpreted layers:

1. architectural Python RV32IM reference model and controlled encoder
2. directed and deterministic random program generation
3. RTL self-checking simulation with commit-trace comparison
4. functional-event coverage plus RTL-only line/branch/toggle code coverage
5. assertions, lint, formal verification and synthesis

No stage is marked PASS unless its tool actually executes successfully. Model-only measurements are never presented as RTL results, and technology-dependent ASIC metrics are not claimed without a characterized library and constraints.

## Directed tests

| Test | Main coverage |
|---|---|
| 01_alu | all base integer ALU families, signed/unsigned comparisons, shifts, corner values |
| 02_dual_issue | independent ALU pairs and 2-wide pairing |
| 03_dependencies | RAW dependency chain and slot1 replay |
| 04_forwarding | back-to-back producer/consumer forwarding |
| 05_branches | branch taken/not taken and wrong-path suppression |
| 06_jumps | JAL/JALR link and redirect |
| 07_load_store | LB/LBU/LH/LHU/LW, SB/SH/SW, sign extension |
| 08_mul | MUL/MULH/MULHSU/MULHU |
| 09_div | DIV/DIVU/REM/REMU, divide-by-zero, signed overflow |
| 10_random_mix | mixed ALU/M/MEM behavior |
| 11_stress_dependencies | long RAW chain |
| 12_branch_flush | loop redirects and younger wrong-path suppression |
| 13_waw_pairing | WAW blocking and replay |
| 14_x0_invariant | x0 write suppression |
| 15–18 | misaligned load/store, ECALL, generic illegal trap |
| 19–22 | structural replay, unsigned DIV corners, complete branch outcomes, EX/MEM/WB forwarding stimuli |
| 23–25 | IALIGN=32 misaligned JAL/JALR/taken-branch traps |
| 26 | precise trap: younger register/store side effects forbidden |
| 27–33 | reserved illegal encodings inside JALR/branch/load/store/shift/OP/SYSTEM opcodes |
| 34 | not-taken branch with misaligned encoded target must not trap |
| 35 | JALR bit-0 clearing before IALIGN check |
| 36 | 32-bit arithmetic overflow/wrap-around |
| 37 | register shift amount masking to low 5 bits |
| 38 | signed/unsigned comparison and branch extremes |
| 39 | SB byte-enable lanes 0,1,2,3 plus signed byte load |
| 40 | SH upper halfword lane plus LH/LHU behavior |
| 41 | MUL/MULH/MULHSU/MULHU high-word corner values |

## Random tests

`scripts/gen_random_program.py` creates deterministic straight-line RV32IM streams with seeded ALU, M-extension, dependency chains and periodic store/load operations. `run_reference_regression.py` executes seeds **1..500** against the Python architectural model. The Verilator RTL regression additionally runs **50 deterministic random RTL seeds** and checks every commit against the same architectural model.

Generated `.hex` programs are run on RTL and the architectural commit sequence is compared against the reference model.

## Commit checker

The RTL testbench emits:

```text
cycle,slot,pc,instr,rd_we,rd,rd_value,mem_we,mem_addr,mem_data
```

The comparison checks PC and instruction identity for each architectural commit, destination write enable/register/value, store side effects, and terminal trap state. Slot0 is logged before slot1.

## Assertion intent

Portable immediate assertions check:

* x0 remains zero
* slot1 cannot issue without slot0
* a pair with RAW cannot issue slot1
* a pair with WAW cannot issue slot1
* a structurally illegal pair cannot issue slot1
* a redirect cannot coincide with younger issue
* single data-memory port cannot read and write simultaneously
* slot1 cannot commit without the older slot0 commit
* architectural commit cannot write x0
* no instruction issues after halt
* no architectural commit, register-file write, or data-memory access after halt

Additional OSS formal targets are specified in `formal/`. They use Yosys-Slang plus immediate assertions; the core invariants are compiled under `` `ifdef FORMAL `` to avoid dependence on `bind`/rich SVA in the default open-source flow. `formal/core_harness.sv` constrains reset low for the first sampled clock and high thereafter while leaving instruction/data values symbolic. The complete-core invariant set also checks front-end adjacency/alignment, slot1 replay, redirect flush, lane1 resource legality, precise-exception emptiness, memory-side-effect ordering, divider stall behavior, and temporal pipeline movement.

## Functional-event coverage

The portable testbench records explicit functional event counters rather than relying on simulator-specific covergroups. Counters include branch outcomes, dual/single issue, RAW/WAW/structural pairing blocks, replay/redirect behavior, EX/MEM/WB forwarding, loads/stores and byte lanes, OP/OP-IMM, all M-extension operations, trap classes, load-use stalls and divider stalls. Detailed architectural behavior is independently checked by the commit-trace scoreboard.

The run #48 directed suite closed **58/58 functional-event points**. These are semantic verification events and must not be confused with statement/branch/toggle code coverage.

## RTL line/branch/toggle code coverage

`make rtl-code-coverage` runs the same **41 directed + 50 deterministic random = 91 programs** using Verilator coverage instrumentation, writes one coverage database per test, merges the databases, and generates both LCOV and annotated RTL evidence.

The reported percentages are RTL-only; testbench files are excluded from the metric. The source-completeness gate requires every executable synthesizable RTL source to appear in LCOV and annotated output. Definition-only SystemVerilog packages are listed separately because declarations and typedefs do not produce executable Verilator coverage points.

The first verified baseline, GitHub Actions run #48, measured:

| Coverage class | Covered | Total | Result |
|---|---:|---:|---:|
| Line | 416 | 423 | **98.35%** |
| Branch | 303 | 305 | **99.34%** |
| Toggle | 10,636 | 14,182 | **75.00%** |

All **9/9 measurable RTL module files** were present. `riscv_pkg.sv` was correctly identified as definition-only package source.

No arbitrary percentage threshold is imposed for this initial measured baseline. The gate instead fails on simulator/coverage-tool errors, failed test execution, missing executable RTL sources, or vacuous line/branch/toggle classes. A future threshold should be introduced only after the baseline and exclusions are intentionally reviewed.

## Divider algorithm stress

The restoring divider has a bit-accurate Python mirror. The unit test executes **5,000 deterministic random operand pairs for DIV, DIVU, REM and REMU (20,000 result comparisons)**, including explicit ISA corner-case handling. This does not replace RTL simulation.

## Required corner cases

* x0 read/write behavior
* signed vs unsigned comparisons
* shifts by 0 and 31, plus register shift amounts 32 and 63 (low-5-bit masking)
* 0x00000000, 0xffffffff, 0x80000000, 0x7fffffff arithmetic behavior
* branch taken/not-taken
* JALR bit-0 clearing before IALIGN check
* IALIGN=32 instruction-address-misaligned traps only for taken control transfers
* precise trap quiescence after halt
* load-use stall
* pair RAW/WAW
* byte/half sign and zero extension
* byte-enable coverage for all four SB lanes and both aligned SH lanes
* misaligned half/word detection
* divide-by-zero
* `INT_MIN / -1`
* slot1 replay
* redirect flush
* divider busy stall

## RTL performance comparison

`make rtl-perf` compiles the same testbench twice, once with `ENABLE_DUAL_ISSUE=1` and once with `ENABLE_DUAL_ISSUE=0`, then runs identical independent and dependency-heavy programs. The resulting cycles, IPC, dual-issue count and speedup are written only if the simulator runs successfully.

## Exit criteria

The strict verification baseline requires independent success of architectural-model tests, RTL commit-trace equivalence, functional-event coverage, RTL code-coverage collection/integrity, RTL assertions, lint, formal verification, and generic synthesis. Missing tools yield `TOOL UNAVAILABLE`, not PASS. Technology-characterized timing/area/power remain separate gates that require a real standard-cell library and constraints.
