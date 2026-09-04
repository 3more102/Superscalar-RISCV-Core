# 2-Wide Superscalar RV32IM RISC-V Core

[![ISA](https://img.shields.io/badge/ISA-RV32IM-5b2c6f)](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)
[![RTL](https://img.shields.io/badge/RTL-SystemVerilog-2f74c0)](rtl/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-educational%20%2F%20research%20RTL-informational)](#verification-status)

A synthesizable **32-bit, 2-wide superscalar, in-order issue / in-order retirement RV32IM processor core** written in SystemVerilog. The baseline implements dual fetch/decode/issue, conservative dependency-aware pairing, forwarding, control-flow recovery, a single-port LSU, RV32M including an iterative divider, precise educational trap handling, differential reference-model verification, formal infrastructure, and open-source synthesis/timing flows.

> **Verification boundary:** model/reference checks below have executed and are recorded in `reports/`. Full RTL simulation, lint, formal solver execution, synthesis, and characterized timing remain separate EDA gates and are never reported as PASS unless their tools actually run.

## Architecture at a glance

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

Slot 0 is always older than slot 1. If the younger instruction cannot legally pair, slot 0 proceeds and slot 1 is retained/replayed; slot 1 never overtakes slot 0 architecturally.

## What this project demonstrates

- CPU microarchitecture and pipeline design in synthesizable SystemVerilog
- superscalar dependency analysis, conservative pairing, and replay
- RAW/WAW/structural hazard handling and EX/MEM/WB bypassing
- branch/jump redirect and wrong-path suppression
- RV32IM decode and execution, including a multi-cycle restoring divider
- byte/half/word load-store formatting and alignment checking
- self-checking architectural reference modeling and commit-trace comparison infrastructure
- deterministic directed/random verification and coverage-oriented stimuli
- portable assertions plus SymbiYosys/yosys-slang formal targets
- Yosys generic synthesis and optional Liberty-based technology mapping / STA infrastructure

## Technical highlights

| Feature | Baseline implementation |
|---|---|
| ISA | RV32IM + ECALL/EBREAK educational trap termination |
| XLEN | 32 bits |
| Fetch width | 2 instructions |
| Decode width | 2 instructions |
| Maximum issue width | 2 instructions |
| Scheduling | In-order |
| Retirement | In-order |
| Lane 0 | ALU / control / LSU / MDU |
| Lane 1 | Integer ALU / LUI / AUIPC baseline |
| Pair policy | Conservative; no intra-pair RAW/WAW or serializing/resource conflicts |
| Branch policy | Static not-taken baseline |
| Memory architecture | Harvard-style instruction/data interfaces |
| LSU | One data-memory operation per issue cycle baseline |
| Divider | Configurable-latency restoring iterative divider |
| Verification | directed + random + reference model + commit trace + assertions/formal infrastructure |
| RTL language | SystemVerilog |

## Verification status

The current numbers are generated from the checked-in reports, especially `reports/final_verification_summary.md` and `reports/check_status.json`.

| Verification item | Current result |
|---|---:|
| Python verification tests | **25/25 PASS** |
| Directed architectural programs | **41/41 PASS** |
| Random architectural seeds | **500/500 PASS** |
| Required ISA mnemonics exercised | **47/47** |
| Reference/stimulus coverage | **54/54 points PASS** |
| Reference-model committed instructions checked | **47,280** |
| Restoring-divider differential checks | **20,000/20,000 PASS** |
| Front-end replay stress | **100,000/100,000 cycles PASS** |
| Front-end model instructions issued | **126,494** |
| Front-end model redirects | **208** |
| Cycle-oriented microarchitecture workloads | **500/500 completed** |
| Static RTL source audit | **PASS — 0 detected issues** |
| Formal-flow source audit | **PASS** — configuration integrity only |
| EDA/CI tool-flow source audit | **PASS** — configuration integrity only |
| RTL compile / simulation | **TOOL UNAVAILABLE** in the originating environment |
| RTL commit-trace equivalence | **NOT RUN** without HDL simulator |
| RTL functional coverage | **NOT RUN** without HDL simulator |
| Verilator lint | **TOOL UNAVAILABLE** in the originating environment |
| Formal solver execution | **TOOL UNAVAILABLE** in the originating environment |
| Yosys synthesis | **TOOL UNAVAILABLE** in the originating environment |
| Technology-mapped cell count / STA / WNS / MHz | **NOT RUN** — requires real Liberty/constraints/tools |

**Reference/stimulus coverage is not RTL code coverage.** Likewise, model IPC is not RTL-measured IPC.

Detailed evidence: [`reports/final_verification_summary.md`](reports/final_verification_summary.md).

## ISA support

### RV32I

| Class | Instructions |
|---|---|
| Upper immediates | `LUI`, `AUIPC` |
| Jumps | `JAL`, `JALR` |
| Branches | `BEQ`, `BNE`, `BLT`, `BGE`, `BLTU`, `BGEU` |
| Loads | `LB`, `LH`, `LW`, `LBU`, `LHU` |
| Stores | `SB`, `SH`, `SW` |
| Immediate ALU | `ADDI`, `SLTI`, `SLTIU`, `XORI`, `ORI`, `ANDI`, `SLLI`, `SRLI`, `SRAI` |
| Register ALU | `ADD`, `SUB`, `SLL`, `SLT`, `SLTU`, `XOR`, `SRL`, `SRA`, `OR`, `AND` |

### RV32M

`MUL`, `MULH`, `MULHSU`, `MULHU`, `DIV`, `DIVU`, `REM`, `REMU`

### System / illegal handling

`ECALL` and `EBREAK` are implemented as serializing educational termination/trap events. Unsupported/reserved encodings raise the internal illegal-instruction trap indication. This project does **not** claim full privileged-architecture compliance.

## Superscalar pairing rules

The baseline intentionally favors simple, auditable correctness over aggressive pairing.

| Older slot 0 | Younger slot 1 | Dual issue? | Reason |
|---|---|---:|---|
| independent ALU / OP-IMM | independent ALU / OP-IMM | Yes | no RAW/WAW/resource stall |
| `LUI` / `AUIPC` | simple integer op | Yes | same dependency rules |
| simple integer op | `LUI` / `AUIPC` | Yes | same dependency rules |
| ALU | dependent ALU | No | slot1 RAW; replay |
| same nonzero destination | same nonzero destination | No | WAW; replay |
| memory | anything | No | baseline LSU serialization |
| anything | memory | No | lane1 has no LSU |
| branch/JAL/JALR | anything | No | control-flow serialization |
| M-extension | anything | No | lane0-only MDU baseline |
| system/illegal | anything | No | precise serializing trap behavior |

See [`docs/dual_issue_matrix.md`](docs/dual_issue_matrix.md) for the exact implemented matrix.

## Forwarding and hazards

Operand selection gives priority to the newest valid producer and instruments three bypass classes:

- **EX forwarding** for ready ALU/MUL/link results
- **MEM forwarding**, including load data once available
- **WB forwarding** as the final bypass source

A load result still resident in EX causes a one-cycle load-use stall. DIV/REM holds EX until the iterative divider asserts completion. Intra-pair RAW/WAW is blocked rather than using same-cycle lane0-to-lane1 forwarding in this baseline.

## Control flow and precise traps

- static not-taken baseline prediction
- all six RV32I conditional branch classes
- `JAL` and `JALR` redirects
- buffered wrong-path instructions flushed on redirect
- `JALR` clears target bit 0 before alignment evaluation
- no RVC support, therefore **IALIGN=32**
- taken branch/jump to a non-4-byte-aligned target raises instruction-address-misaligned
- a not-taken branch does not trap merely because its encoded target would be misaligned
- load/store misalignment suppresses the external transaction and produces the corresponding baseline trap/halt indication
- once `halted` is asserted, architectural commit, register-file writes, and data-memory accesses are suppressed

## RV32M implementation

The multiply path supports all four RV32M multiply result forms. DIV/REM uses a restoring iterative divider. With the default `DIV_LATENCY=8`, four radix-2 quotient iterations are unrolled per clock for 32 total quotient steps across eight busy clocks. Divide-by-zero and signed `INT_MIN / -1` corner cases follow the RISC-V M-extension architectural results.

The Python mirror of the divider algorithm has executed **20,000 deterministic differential comparisons**; this remains algorithmic/model evidence until RTL simulation closes the hardware gate.

## Memory system

The baseline exposes separate instruction and data interfaces. Lane 0 owns the LSU and the baseline permits at most one memory operation per issue cycle.

Implemented behavior includes:

- `LB/LBU/LH/LHU/LW`
- `SB/SH/SW`
- byte enables for all four byte lanes
- aligned upper/lower halfword lanes
- sign and zero extension
- halfword/word alignment checks

## Verification architecture

```text
Assembly / Generated Programs
            |
            v
      Program Encoder
            |
            +---------------------+
            |                     |
            v                     v
   Python RV32IM Model      RTL Testbench
            |                     |
            +------ compare ------+
                     |
                Commit Trace
```

The verification stack includes:

1. 41 directed architectural programs with generated expected-state metadata
2. 500 deterministic random architectural seeds
3. Python RV32IM architectural model
4. commit-trace scoreboard infrastructure for RTL differential checking
5. issue-policy and cycle-oriented microarchitecture models
6. 100k-cycle front-end replay stress model
7. restoring-divider differential stress
8. portable RTL assertions and formal harnesses
9. Verilator/Yosys/SymbiYosys automation and strict GitHub CI configuration

Directed coverage includes ALU/immediate operations, dual issue, RAW, WAW, slot1 replay, EX/MEM/WB forwarding stimuli, load-use, branches/jumps/flush, wrong-path suppression, loads/stores, byte/halfword lanes, misalignment, all RV32M operations, divide-by-zero, signed overflow, x0, ECALL/EBREAK, instruction alignment, and reserved/illegal encoding classes.

See [`docs/verification_plan.md`](docs/verification_plan.md).

## Performance: model vs RTL

### Executed model-level evidence

- independent ALU issue-policy stream: **2.000 issue IPC**
- dependency chain: **1.000 issue IPC**
- cycle-oriented model: **500/500** workloads
- mean model 2-wide IPC: **0.615**
- mean model speedup vs forced single issue: **1.187x**

These values are **model-only** and are deliberately not presented as RTL performance.

### RTL-measured performance

`make rtl-perf` builds the same core with `ENABLE_DUAL_ISSUE=1` and `ENABLE_DUAL_ISSUE=0` and is prepared to report real cycles, IPC, dual-issue count, and speedup once an HDL simulator executes it. No RTL performance number is claimed in the checked-in baseline environment.

See [`docs/performance_analysis.md`](docs/performance_analysis.md).

## Formal and ASIC infrastructure

Formal targets cover controlled reset plus invariants for x0, issue legality, slot1 replay, redirect flush, precise exceptions, front-end adjacency/alignment, memory-side-effect ordering, and EX→MEM age preservation. The SBY/yosys-slang files are included, but solver execution remains environment-dependent until the tool chain runs.

The ASIC flow separates generic synthesis from technology-dependent results:

- Yosys generic synthesis scripts
- optional technology mapping with a user-supplied `LIBERTY_FILE`
- optional OpenSTA/Yosys timing reporting with an explicit `SDC_FILE` or `CLOCK_PERIOD_NS`

No cell count, area, WNS/TNS, maximum frequency, or power value is invented. See [`docs/asic_timing_flow.md`](docs/asic_timing_flow.md).

## Repository structure

```text
Superscalar-RISCV-Core/
├── rtl/                  # synthesizable SystemVerilog
│   ├── common/
│   ├── core/
│   ├── decode/
│   ├── execute/
│   ├── issue/
│   ├── memory/
│   ├── branch/
│   └── mdu/
├── tb/                   # self-checking testbench and Python tests
├── sw/                   # assembly/hex/expected directed programs
├── reference_model/      # architectural + issue/pipeline models
├── scripts/              # regression, audit, lint, formal, synth helpers
├── formal/               # SymbiYosys/yosys-slang targets
├── synthesis/            # generic synthesis scripts
├── reports/              # retained human-readable evidence/status
├── docs/                 # architecture and verification documentation
├── tools/                # local OSS CAD Suite bootstrap helpers
├── .github/workflows/    # strict CI
├── Makefile
└── README.md
```

## Quick start

### Python/reference verification

```bash
python3 -m pip install pytest
python3 scripts/run_all_checks.py
```

or:

```bash
make test
```

### Focused targets

```bash
make reference      # directed generation + architectural reference regression
make microarch      # cycle-oriented microarchitecture model
make coverage       # reference/stimulus coverage
make rtl            # real RTL regression with Verilator or Icarus
make rtl-coverage   # analyze RTL event coverage after simulation
make rtl-perf       # real single-vs-dual RTL performance comparison
make lint           # Verilator lint
make formal         # SBY formal targets
make synth          # generic Yosys synthesis
```

### Technology-mapped ASIC flow

```bash
export LIBERTY_FILE=/absolute/path/to/stdcells.lib
make asic
```

For STA, additionally provide `SDC_FILE` or an explicitly selected `CLOCK_PERIOD_NS`. The flow has no default timing target.

## Windows / WSL

The project is designed to work from an E: drive checkout such as:

```text
E:\Superscalar_RISCV_Core
```

The helper below bootstraps OSS CAD Suite into the project-local `tools/` area and runs the strict verification flow without requiring an EDA installation on C:\:

```powershell
tools\run_full_verification.ps1
```

See [`docs/tool_setup_windows.md`](docs/tool_setup_windows.md).

## GitHub CI

`.github/workflows/rtl-ci.yml` separates the verification surface into visible jobs:

- Python/reference verification
- RTL simulation + RTL coverage + RTL performance
- Verilator lint
- formal solver execution
- Yosys synthesis

The EDA jobs use OSS CAD Suite and fail if a required tool/gate is unavailable; mandatory failures are not hidden with `continue-on-error`.

## Limitations

The baseline intentionally excludes:

- out-of-order execution
- register renaming / reorder buffer
- same-cycle inter-lane forwarding
- MMU / virtual memory / page tables
- full privileged architecture and interrupt subsystem
- Linux boot support
- RVC compressed instructions
- floating point and vector extensions
- instruction/data caches
- cache coherence
- branch predictor/BTB beyond static not-taken
- lane1 LSU/MDU support

This is an educational/research RTL core and is **not** described as silicon-proven, security-certified, production-ready, or tapeout-ready.

## Roadmap

- [ ] close full RTL regression under Verilator/Icarus
- [ ] close RTL functional coverage and commit-trace equivalence
- [ ] close formal proofs under SBY
- [ ] technology-map with a characterized standard-cell library
- [ ] measure real RTL IPC and dual-issue speedup
- [ ] add BTB + 2-bit branch predictor
- [ ] add instruction cache
- [ ] add data cache
- [ ] pipeline/decouple MDU where useful
- [ ] evaluate lane1 LSU support
- [ ] add store buffer
- [ ] evaluate same-cycle lane0→lane1 forwarding
- [ ] optional deeper-pipeline / scoreboard successor architecture

## Documentation

- [Microarchitecture](docs/microarchitecture.md)
- [Dual-issue matrix](docs/dual_issue_matrix.md)
- [Verification plan](docs/verification_plan.md)
- [Performance analysis](docs/performance_analysis.md)
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
