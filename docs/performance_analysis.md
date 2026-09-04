# Performance Analysis

## Baseline

The core can issue/retire at most two instructions per cycle. The baseline pairs independent simple integer operations while memory, control-flow, system, and M-extension operations serialize the pair. `ENABLE_DUAL_ISSUE=0` forces the same RTL into single-issue mode, allowing an apples-to-apples performance comparison without changing the program or microarchitectural implementation.

## RTL-measured results

GitHub Actions run #20 executed `make rtl-perf` under Verilator. The same programs were simulated with dual issue enabled and disabled.

| Program | Retired | Single cycles | 2-wide cycles | Single IPC | 2-wide IPC | RTL speedup | Dual-issue cycles |
|---|---:|---:|---:|---:|---:|---:|---:|
| dependency_100 | 100 | 105 | 105 | 0.952 | 0.952 | **1.000x** | 0 |
| independent_200 | 200 | 205 | 105 | 0.976 | **1.905** | **1.952x** | 100 |

These are **SystemVerilog RTL simulator measurements**. They are not analytical estimates and are not copied from the Python timing model.

### Interpretation

The independent 200-instruction stream demonstrates the intended superscalar benefit: 100 cycles issue two instructions, reducing total execution from 205 cycles to 105 cycles and reaching **1.905 IPC**, a **1.952x** speedup over the forced single-issue build.

The 100-instruction dependency chain produces no legal dual-issue pairs. Both builds take 105 cycles and achieve 0.952 IPC, so the measured speedup is **1.000x**. This is the expected result for an in-order pairer that blocks intra-pair RAW dependencies.

The fixed startup/drain overhead prevents the independent test from reporting exactly 2.000 architectural IPC even though the useful steady-state section dual-issues 100 pairs.

## Supporting RTL counters and events

The core exposes counters for cycles, retired instructions, dual/single issue cycles, stalls, branch count, static-not-taken mispredictions, load-use stalls, structural stalls, and divider stalls.

The RTL functional-coverage run observed, among other events:

- dual issue: 59 events across the directed suite
- single issue: 203
- RAW pair blocks: 60
- WAW pair blocks: 17
- structural blocks: 552
- redirects: 20
- EX forwarding: 71
- MEM forwarding: 24
- WB forwarding: 18
- load-use stalls: 1
- divider stalls: 126

These totals are verification-event observations across the 41 directed programs, not performance-benchmark totals.

## Model-level evidence

The project also keeps two executable Python performance models for rapid microarchitectural exploration:

1. a simple issue-policy model reaches **2.000 issue IPC** for a 200-instruction independent ALU stream and **1.000** for a same-register dependency chain;
2. a cycle-oriented model includes front-end fill/replay, load-use bubbles, branch redirects, and the blocking divider.

The cycle model completed **500/500 deterministic random workloads** with mean 2-wide model IPC **0.615** and mean model speedup **1.187x** versus its forced single-issue configuration.

Model results remain explicitly separated from RTL measurements.

## Current bottlenecks

1. lane 1 accepts only simple ALU/LUI/AUIPC work
2. every memory operation serializes the pair
3. all M-extension operations serialize issue
4. static-not-taken control flow pays redirect bubbles when taken
5. load-use adds a one-cycle dependency stall
6. DIV/REM holds EX for the configured divider latency
7. no same-cycle lane0→lane1 forwarding is implemented

## Next performance experiments

1. allow safe ALU + memory pairing with explicit resource ownership
2. add same-cycle lane0→lane1 forwarding for simple integer results
3. pipeline or decouple the MDU where useful
4. add a BTB + 2-bit branch predictor
5. add instruction/data caches
6. evaluate scoreboard-based scheduling only after the in-order baseline remains fully verified

Raw simulator evidence is retained by CI in the `rtl-simulation-reports` artifact; the generated summary is `reports/performance/rtl_performance_comparison.md` during the workflow run.
