# Current Performance Comparison

**Status:** RTL timing/performance simulation remains `TOOL UNAVAILABLE` in the current sandbox.

The core now has an `ENABLE_DUAL_ISSUE` elaboration parameter so the identical RTL can later be simulated with dual issue enabled and disabled. Until that RTL run exists, only executable model comparisons are reported.

| Model workload | Single-issue cycles | 2-wide cycles | 2-wide IPC/model | Model speedup |
|---|---:|---:|---:|---:|
| Independent ALU issue-policy stream (200 instructions) | 200 | 100 | 2.000 issue IPC | 2.000x |
| Dependency chain (100 instructions) | 100 | 100 | 1.000 issue IPC | 1.000x |
| 01_alu cycle model | 28 | 17 | 1.353 pipeline IPC | 1.647x |
| 02_dual_issue cycle model | 15 | 10 | 1.000 pipeline IPC | 1.500x |

Across **500/500** generated cycle-model workloads, mean 2-wide pipeline IPC was **0.615** and mean speedup over the forced single-issue model was **1.187x**.

These are **not RTL measurements**. Real comparison remains gated on an HDL simulator.
