# Changelog

All notable engineering milestones for this repository are recorded here. Results are listed only when backed by retained reports or executed tool output.

## Unreleased

### Release candidate: v0.2.0 — Verification Infrastructure Release

#### Added

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
- Python RV32IM architectural reference model
- deterministic directed and random program generation
- commit-trace RTL comparison infrastructure
- issue-policy, pipeline timing, front-end replay, and divider differential models
- portable assertions and yosys-slang/SymbiYosys formal harnesses
- strict OSS CAD Suite GitHub Actions flow
- Yosys synthesis plus optional Liberty-based mapping/STA infrastructure

#### Executed reference/model evidence

- 25/25 Python tests PASS
- 41/41 directed architectural programs PASS
- 500/500 deterministic random architectural seeds PASS
- 47/47 required ISA mnemonics exercised
- 54/54 reference/stimulus coverage points PASS
- 47,280 architectural commits checked
- 20,000/20,000 restoring-divider differential comparisons PASS
- 100,000/100,000 front-end replay stress cycles PASS
- 500/500 cycle-oriented microarchitecture workloads completed

#### Open EDA gates

Full RTL simulation/commit equivalence, RTL functional coverage, measured RTL IPC, Verilator lint, formal solver proofs, Yosys synthesis, and characterized ASIC timing remain environment/tool dependent until actually executed. No PPA or frequency values are inferred from model-only evidence.
