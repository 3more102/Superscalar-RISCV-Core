# v0.2.0 — Verification Infrastructure Release Candidate

This release candidate packages the complete educational/research **2-wide in-order superscalar RV32IM core** together with its reference verification stack, formal targets, CI, and synthesis/timing infrastructure.

## Architecture

- 32-bit RV32IM
- 2-wide fetch / decode / maximum issue
- conservative in-order issue and in-order retirement
- slot0 older / slot1 younger with replay on illegal pairing
- lane0 ALU + branch/jump + LSU + MDU
- lane1 integer ALU baseline
- static not-taken control-flow policy
- Harvard-style instruction/data interfaces
- iterative restoring DIV/REM implementation

## Executed evidence

Use `reports/final_verification_summary.md` as the authoritative snapshot. The current release candidate records 25/25 Python tests, 41/41 directed programs, 500/500 random architectural seeds, 47/47 requested ISA mnemonics, 54/54 reference/stimulus coverage points, 47,280 checked architectural commits, 20,000 divider comparisons, and 100,000 front-end replay stress cycles.

These are **reference/model/infrastructure results**. They are not substitutes for RTL simulation, formal solver proofs, synthesis, or characterized timing.

## Known open gates

- full SystemVerilog RTL simulation and commit-trace equivalence
- RTL functional coverage
- real RTL IPC and single-vs-dual speedup
- Verilator lint in an EDA-equipped environment
- SymbiYosys solver execution
- Yosys synthesis
- Liberty-mapped cell count and STA

## Quick verification

```bash
python3 -m pip install pytest
make test
```

With OSS CAD Suite:

```bash
make rtl
make rtl-coverage
make rtl-perf
make lint
make formal
make synth
```
