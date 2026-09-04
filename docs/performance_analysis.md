# Performance Analysis

## Baseline behavior

The machine can retire at most two instructions per cycle. The baseline pairs only independent simple integer operations. Memory, control-flow and M-extension operations serialize the pair. The RTL parameter `ENABLE_DUAL_ISSUE=0` forces the same core into single-issue mode for a later measured comparison.

## Measurements available in the current environment

No HDL simulator is installed here, so **no RTL-cycle IPC is claimed**. Two executable Python models were run:

1. the simple issue-policy sanity model reaches 2.000 issue IPC for a 200-instruction independent ALU stream and 1.000 for a same-register dependency chain;
2. the cycle-oriented microarchitecture model includes front-end fill/replay, load-use bubbles, branch redirects and the blocking divider.

The cycle model completed **500/500 deterministic random workloads** with mean 2-wide model IPC **0.615** and mean speedup **1.187x** versus its forced single-issue configuration.

Directed model results are recorded in `reports/performance/microarchitecture_timing_model.md`; examples include:

| Program | Single cycles(model) | 2-wide cycles(model) | Model speedup |
|---|---:|---:|---:|
| 01_alu | 28 | 17 | 1.647x |
| 02_dual_issue | 15 | 10 | 1.500x |
| 03_dependencies | 12 | 11 | 1.091x |
| 09_div | 90 | 88 | 1.023x |

These values are **timing-model results only**, not evidence of RTL performance.

## RTL counters

The core contains counters for cycles, retired instructions, dual/single issue, stalls, branch/redirect count, static-not-taken mispredictions, load-use stalls, structural stalls and divider stalls. After real simulation, measured RTL IPC is `perf_retired / perf_cycles`.

## Expected bottlenecks

1. lane1 accepts only simple ALU/LUI/AUIPC work
2. every memory operation serializes issue
3. all M-extension operations serialize issue
4. static-not-taken pays redirect bubbles on taken branches/JAL/JALR
5. load-use adds one cycle
6. DIV/REM holds EX for the configured divider latency

## Next performance steps after RTL correctness

1. allow `ALU + memory` pairing where resource ownership is unambiguous
2. add same-cycle lane0-to-lane1 forwarding for simple ALU results
3. pipeline or decouple the iterative MDU
4. add BTB + 2-bit branch predictor
5. add instruction/data caches
6. consider scoreboard-based scheduling only after the in-order baseline is fully RTL-verified
