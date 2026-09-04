# 2-Wide Superscalar RV32IM RISC-V Core

[![RTL CI](https://github.com/3more102/Superscalar-RISCV-Core/actions/workflows/rtl-ci.yml/badge.svg)](https://github.com/3more102/Superscalar-RISCV-Core/actions/workflows/rtl-ci.yml)
[![ISA](https://img.shields.io/badge/ISA-RV32IM-5b2c6f)](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)
[![RTL](https://img.shields.io/badge/RTL-SystemVerilog-2f74c0)](rtl/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A synthesizable **32-bit, 2-wide superscalar, in-order issue / in-order retirement RV32IM processor core** written in SystemVerilog. The project is built as a CPU-microarchitecture and RTL-verification portfolio piece: dual fetch/decode/issue, dependency-aware pairing, replay, EX/MEM/WB forwarding, branch recovery, a single-port LSU, RV32M with an iterative divider, precise educational trap handling, differential commit-trace verification, formal properties, and open-source synthesis automation.

## What this project demonstrates

- **CPU microarchitecture design:** 2-wide fetch/decode/issue, conservative superscalar pairing, replay, in-order retirement, control-flow recovery, and precise architectural ordering.
- **Synthesizable SystemVerilog RTL:** modular decode, ALU, branch, register-file, issue, LSU, multiply/divide, and top-level pipeline implementation.
- **Dependency and hazard engineering:** RAW/WAW/resource checks, EX/MEM/WB forwarding, load-use handling, divider stalls, and younger-slot replay.
- **RV32IM implementation:** base integer ISA, all eight M-extension operations, alignment handling, illegal encodings, ECALL/EBREAK, and JALR/IALIGN corner cases.
- **Self-checking verification:** directed programs, deterministic random workloads, a Python architectural reference model, commit-trace differential checking, and functional-event coverage.
- **Formal verification:** symbolic issue and ALU/branch proofs plus a bounded 32-cycle compositional control/order proof using Yosys-Slang and Yosys SAT.
- **Measured superscalar behavior:** the same RTL is compiled as single-issue and 2-wide to quantify IPC and speedup on dependent versus independent workloads.
- **Open-source ASIC/EDA flow design:** strict GitHub Actions CI, Verilator lint/simulation, Yosys synthesis, formal automation, and optional Liberty-based mapped synthesis/STA infrastructure.

## Verified status

The latest fully green **code/workflow baseline** is GitHub Actions **run #40**, commit [`5c99926`](https://github.com/3more102/Superscalar-RISCV-Core/commit/5c99926d7839c35b63ddb39e08d0176cae34313b). All five mandatory jobs passed on that revision. Run #40 also validates the weekly reproducibility schedule and the docs-only CI path policy. Subsequent README/CI-evidence commits are documentation-only and do not modify RTL, testbench, reference-model, formal, synthesis, or verification-script behavior. The CI badge above tracks the current `main` branch.

| Gate | Executed result |
|---|---:|
| Python verification tests | **25/25 PASS** |
| Directed architectural reference tests | **41/41 PASS** |
| Random architectural reference seeds | **500/500 PASS** |
| Reference commits checked | **47,280** |
| Required RV32IM mnemonics exercised | **47/47** |
| Reference/stimulus functional coverage | **54/54** |
| Divider differential stress | **20,000/20,000 PASS** |
| Front-end replay stress | **100,000/100,000 cycles PASS** |
| RTL differential regression | **91/91 PASS** — 41 directed + 50 random |
| RTL functional event coverage | **58/58 points PASS** |
| Verilator lint policy | **PASS** — 12 allowed unused warnings, 0 unexpected |
| Formal issue proof | **PASS** |
| Formal ALU/branch equivalence proof | **PASS** |
| Formal core control/order proof | **PASS through 32 cycles** |
| Generic Yosys synthesis | **PASS** — 43,289 generic primitive cells, 0 check problems |
| Characterized ASIC area/timing/power | **Not claimed** — no standard-cell Liberty was supplied |

Detailed CI provenance and artifact digests are recorded in [`docs/ci_evidence.md`](docs/ci_evidence.md). The concise verification summary is in [`reports/final_verification_summary.md`](reports/final_verification_summary.md).

## Architecture

```text
                         +----------------------+
                         | Instruction Memory   |
                         +----------+-----------+
                                    |
                              2-wide Fetch
                                    |
                         +----------v-----------+
                         | 2-entry Front-End    |
                         | Buffer / Replay      |
                         +----------+-----------+
                                    |
                              Dual Decode
                                    |
                         +----------v-----------+
                         | Pair / Hazard Check  |
                         | RAW / WAW / Resource |
                         +-----+-----------+----+
                               |           |
                            Lane 0       Lane 1
                               |           |
                       +-------v--+     +--v-------+
                       | ALU      |     | Integer  |
                       | Branch   |     | ALU      |
                       | LSU      |     |          |
                       | MDU      |     |          |
                       +-------+--+     +--+-------+
                               |           |
                               +-----+-----+
                                     |
                                   MEM
                               one data port
                                     |
                                    WB
                                     |
                           In-order Commit
                                     |
                              32 x 32 RF
```

Slot 0 is always older than slot 1. If the younger instruction cannot legally pair, slot 0 proceeds and slot 1 is retained/replayed. Slot 1 never overtakes slot 0 architecturally.

### Microarchitecture summary

| Feature | Baseline implementation |
|---|---|
| ISA | RV32IM + ECALL/EBREAK educational trap termination |
| XLEN | 32 bits |
| Fetch / decode / max issue width | 2 / 2 / 2 |
| Scheduling / retirement | In-order / in-order |
| Lane 0 | ALU, control flow, LSU, MDU |
| Lane 1 | Integer ALU, LUI, AUIPC |
| Pair policy | No intra-pair RAW, WAW, serializing, or structural conflict |
| Branch policy | Static not-taken |
| Memory | Harvard-style instruction/data interfaces; one data-memory operation baseline |
| Forwarding | EX, MEM, WB |
| Divider | Configurable-latency restoring iterative divider |
| Trap model | Precise educational halt/trap indication; not full privileged ISA |

See [`docs/microarchitecture.md`](docs/microarchitecture.md) and [`docs/dual_issue_matrix.md`](docs/dual_issue_matrix.md).

## ISA support

**RV32I:** `LUI`, `AUIPC`, `JAL`, `JALR`, `BEQ`, `BNE`, `BLT`, `BGE`, `BLTU`, `BGEU`, `LB`, `LH`, `LW`, `LBU`, `LHU`, `SB`, `SH`, `SW`, `ADDI`, `SLTI`, `SLTIU`, `XORI`, `ORI`, `ANDI`, `SLLI`, `SRLI`, `SRAI`, `ADD`, `SUB`, `SLL`, `SLT`, `SLTU`, `XOR`, `SRL`, `SRA`, `OR`, `AND`.

**RV32M:** `MUL`, `MULH`, `MULHSU`, `MULHU`, `DIV`, `DIVU`, `REM`, `REMU`.

`ECALL`, `EBREAK`, alignment faults, and unsupported/reserved encodings are handled by the project’s educational precise trap/halt path. The core does **not** claim full privileged-architecture compliance.

## Dual issue and hazards

The baseline deliberately favors correctness and auditability over aggressive pairing.

| Older slot 0 | Younger slot 1 | Dual issue? |
|---|---|---:|
| independent simple integer ops | independent simple integer ops | Yes |
| ALU result consumed by slot 1 | dependent ALU | No — RAW replay |
| same nonzero destination | any register writer | No — WAW replay |
| memory op | anything | No |
| anything | memory op | No |
| branch/JAL/JALR | anything | No |
| M-extension | anything | No |
| system/illegal | anything | No |

Operand selection uses newest-producer priority across EX, MEM, and WB. A load resident in EX causes the baseline one-cycle load-use stall. DIV/REM blocks EX until the iterative divider completes. Same-cycle lane0→lane1 forwarding is intentionally not implemented in this baseline.

## Control flow and traps

The core resolves control flow in lane 0, flushes buffered wrong-path instructions on redirect, clears JALR target bit 0, and uses **IALIGN=32** because RVC is not implemented. Taken branch/jump targets that are not 4-byte aligned raise instruction-address-misaligned; a not-taken branch does not trap merely because its encoded target is misaligned.

Load/store misalignment suppresses the external memory transaction. Once `halted` is asserted, commit, register-file writes, issue, and data-memory side effects are suppressed.

## Verification architecture

```text
Assembly / Generated Programs
            |
            v
      Program Encoder
            |
            +----------------------+
            |                      |
            v                      v
   Python RV32IM Model       SystemVerilog RTL
            |                      |
            +------ compare -------+
                     |
                Commit Trace
```

The RTL regression runs 41 directed programs and 50 deterministic random programs under Verilator, comparing architectural commit behavior and terminal trap state against the Python RV32IM model. The reference layer additionally runs 500 random seeds before the EDA jobs start.

RTL functional-event coverage closed **58/58 points** across branch outcomes, all load/store sizes and byte lanes, all eight M operations, trap classes, dual/single issue, RAW/WAW/structural blocking, replay/redirect behavior, EX/MEM/WB forwarding, load-use stalls, and divider stalls.

See [`docs/verification_plan.md`](docs/verification_plan.md).

## Formal verification

The executed formal flow uses **Yosys-Slang + Yosys SAT** and is fail-fast on the first proof failure.

- **Issue harness — PASS:** symbolic primary inputs prove issue ordering and RAW/WAW/structural blocking.
- **ALU/branch harness — PASS:** symbolic operands/opcodes compare RTL outputs against an independently written expected function.
- **Core control/order harness — PASS through 32 cycles:** bounded base-case proof covers front-end queue adjacency/alignment, slot replay, redirects, lane legality, issue ordering, precise exception ordering, memory-side-effect legality, halted-state suppression, divider stall behavior, and temporal pipeline movement.

The 32-cycle core proof uses explicit formal cutpoints for RF read data and ALU/MUL/DIV/branch result values. This is a **compositional control proof**: datapath values are arbitrary at those cutpoints, so the control invariants must hold for all such values; it is not presented as a monolithic proof of all RV32IM arithmetic semantics.

The retained solver report records `SUCCESS` for issue and ALU/branch and `proved base case for 32 steps: SUCCESS!` for the core target.

## RTL-measured performance

The performance job compiles the same RTL with only `ENABLE_DUAL_ISSUE` changed between single-issue and 2-wide configurations.

| Program | Retired | Single cycles | 2-wide cycles | Single IPC | 2-wide IPC | Speedup | Dual-issue cycles |
|---|---:|---:|---:|---:|---:|---:|---:|
| dependent chain | 100 | 105 | 105 | 0.952 | 0.952 | **1.000x** | 0 |
| independent ALU stream | 200 | 205 | 105 | 0.976 | **1.905** | **1.952x** | 100 |

This demonstrates the intended behavior: the 2-wide machine approaches 2× throughput on pairable independent integer work while preserving single-issue behavior on a dependency chain.

See [`docs/performance_analysis.md`](docs/performance_analysis.md).

## Synthesis and lint

The latest fully green code/workflow baseline, run #40, completed generic Yosys synthesis with **0 `check` problems**. After generic technology mapping the design contained **43,289 Yosys primitive cells**. This is a technology-independent complexity metric only; it is **not** standard-cell area and must not be compared directly with an ASIC gate-equivalent figure.

Verilator lint passed the repository policy with **12 warnings**, all from explicitly allowed `UNUSEDSIGNAL` / `UNUSEDPARAM` categories, and **0 unexpected warnings**.

For technology-mapped ASIC work, `make asic` requires a real `LIBERTY_FILE`; STA additionally requires `SDC_FILE` or an explicit `CLOCK_PERIOD_NS`. No area, WNS/TNS, maximum frequency, or power number is invented.

## Repository structure

```text
Superscalar-RISCV-Core/
├── rtl/                  # synthesizable SystemVerilog
├── tb/                   # self-checking RTL testbench + assertions
├── sw/                   # directed/random program images and metadata
├── reference_model/      # architectural + issue/timing models
├── scripts/              # regression, coverage, lint, formal, synthesis helpers
├── formal/               # formal harnesses and portable SBY targets
├── synthesis/            # generic synthesis scripts
├── reports/              # retained local/reference reports
├── docs/                 # architecture, verification, performance, tool docs
├── tools/                # OSS CAD Suite bootstrap helpers
├── .github/workflows/    # strict CI
├── Makefile
└── README.md
```

## Quick start

Reference/model checks:

```bash
python3 -m pip install pytest
make test
```

Focused EDA targets:

```bash
make rtl            # RTL differential regression
make rtl-coverage   # RTL event coverage
make rtl-perf       # single-vs-dual RTL performance
make lint           # Verilator lint
make formal         # Yosys-Slang/Yosys SAT formal proofs
make synth          # generic Yosys synthesis
```

Technology-mapped flow:

```bash
export LIBERTY_FILE=/absolute/path/to/stdcells.lib
make asic
```

On Windows/WSL, see [`docs/tool_setup_windows.md`](docs/tool_setup_windows.md) and `tools/run_full_verification.ps1`.

## CI

`.github/workflows/rtl-ci.yml` exposes five mandatory jobs:

1. Python / Reference Verification
2. RTL Simulation / Coverage / Performance
3. Verilator Lint
4. Formal Verification
5. Yosys Synthesis

The EDA jobs use OSS CAD Suite and mandatory failures are not hidden with `continue-on-error`. Source/tool-flow changes trigger the strict suite, and the workflow also runs automatically every Monday at **03:17 UTC** as a reproducibility check. Documentation-only and repository-presentation changes are intentionally excluded from the expensive EDA rerun.

## Limitations

The baseline intentionally excludes out-of-order execution, register renaming/ROB, same-cycle inter-lane forwarding, caches, MMU/virtual memory, full privileged architecture/interrupts, Linux boot, RVC, floating point/vector extensions, cache coherence, lane1 LSU/MDU, and dynamic branch prediction beyond static not-taken.

This is an **educational/research RTL core**, not a claim of silicon-proven, security-certified, production-ready, or tapeout-ready hardware.

## Roadmap

- [x] close RTL differential regression under Verilator
- [x] close RTL functional event coverage
- [x] measure single-vs-dual RTL IPC and speedup
- [x] close executable issue, ALU/branch, and 32-cycle core formal targets
- [x] close generic Yosys synthesis and Verilator lint in CI
- [ ] technology-map with a characterized standard-cell library
- [ ] run characterized STA with explicit constraints
- [ ] add BTB + 2-bit branch predictor
- [ ] evaluate lane0 ALU + lane1 memory pairing
- [ ] evaluate same-cycle lane0→lane1 forwarding
- [ ] pipeline/decouple MDU where useful
- [ ] add instruction/data caches
- [ ] optional scoreboard / register-renaming successor architecture

## Documentation

- [Microarchitecture](docs/microarchitecture.md)
- [Dual-issue matrix](docs/dual_issue_matrix.md)
- [Verification plan](docs/verification_plan.md)
- [Performance analysis](docs/performance_analysis.md)
- [CI evidence](docs/ci_evidence.md)
- [ASIC timing flow](docs/asic_timing_flow.md)
- [Specification sources](docs/spec_sources.md)

## References

- [RISC-V RV32I Base Integer ISA](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)
- [RISC-V M Extension](https://docs.riscv.org/reference/isa/unpriv/m-st-ext.html)
- [Verilator](https://verilator.org/)
- [Yosys](https://yosyshq.net/yosys/)
- [SymbiYosys](https://yosyshq.readthedocs.io/projects/sby/)
- [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build)

## License

Released under the [MIT License](LICENSE).
