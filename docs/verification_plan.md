# Verification Plan

## Strategy

Verification is split into four layers:

1. architectural Python RV32IM reference model and controlled encoder
2. directed and deterministic random program generation
3. RTL self-checking simulation with commit-trace comparison when Icarus/Verilator is available
4. assertions, lint, formal and synthesis when their tools are available

No stage is marked PASS unless its tool actually executed successfully.

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

`scripts/gen_random_program.py` creates deterministic straight-line RV32IM streams with seeded ALU, M-extension, dependency chains and periodic store/load operations. `run_reference_regression.py` executes seeds **1..500** against the Python architectural model. When an HDL simulator is present, `run_rtl_regression.py` additionally runs **50 deterministic random RTL seeds** and checks every commit against the same architectural model.

When an RTL simulator is available, generated `.hex` programs are run on RTL and the architectural commit sequence is compared against the reference model.

## Commit checker

The RTL testbench emits:

```text
cycle,slot,pc,instr,rd_we,rd,rd_value,mem_we,mem_addr,mem_data
```

The comparison checks PC and instruction identity for each architectural commit, destination write enable/register/value, and store side effects. Slot0 is logged before slot1.

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

Additional OSS formal targets are specified in `formal/`. They use yosys-slang plus immediate assertions; the core invariants are compiled under `` `ifdef FORMAL `` to avoid dependence on `bind`/rich SVA in the default open-source flow. `formal/core_harness.sv` constrains reset low for the first sampled clock and high thereafter while leaving instruction/data values symbolic. The complete-core invariant set also checks front-end adjacency/alignment, slot1 replay, redirect flush, lane1 resource legality, precise-exception emptiness, memory-side-effect ordering, and EX→MEM age preservation.

## Functional coverage

The portable testbench records explicit functional event counters rather than relying on simulator-specific covergroups. Counters include dual/single issue, RAW/WAW/structural pairing blocks, redirects, loads, stores, branches, JAL/JALR, OP/OP-IMM, and M-extension commits. Detailed architectural behavior is independently checked by the commit-trace scoreboard. The files are generated under `reports/coverage/` during RTL simulation.

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

## Exit criteria

Architectural-model tests, RTL commit-trace equivalence, RTL assertions, lint and synthesis are independent quality gates. Missing tools yield `TOOL UNAVAILABLE`, not PASS.

## RTL performance comparison

`make rtl-perf` compiles the same testbench twice, once with `ENABLE_DUAL_ISSUE=1` and once with `ENABLE_DUAL_ISSUE=0`, then runs identical independent and dependency-heavy programs. The resulting cycles, IPC, dual-issue count and speedup are written only if the simulator runs successfully.
