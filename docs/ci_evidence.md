# CI Verification Evidence

This page records the **latest fully green source/tool-flow baseline**, a subsequent full revalidation of the evidence-refresh commit, and the first fully green execution of the strengthened verification flow for historical provenance.

## Latest fully green source/tool-flow baseline

- Repository: `3more102/Superscalar-RISCV-Core`
- Branch: `main`
- GitHub Actions workflow: `.github/workflows/rtl-ci.yml`
- Run: [#48 / 33900989274](https://github.com/3more102/Superscalar-RISCV-Core/actions/runs/33900989274)
- Verified source/tool-flow commit: [`9a620d9d2b6ab2970b3a54f6852fae9684afe5ad`](https://github.com/3more102/Superscalar-RISCV-Core/commit/9a620d9d2b6ab2970b3a54f6852fae9684afe5ad)
- Commit subject: `test: classify definition-only packages in code coverage`

All five mandatory jobs completed with conclusion `success` on that commit:

1. Python / Reference Verification
2. RTL Simulation / Coverage / Performance
3. Verilator Lint
4. Formal Verification
5. Yosys Synthesis

The RTL job separately executed commit-trace regression, functional-event coverage, RTL line/branch/toggle code coverage, and single-vs-dual performance. The code-coverage step completed successfully before the RTL job was archived.

### Current-HEAD evidence revalidation

The documentation/report evidence-refresh commit [`0b00e18ae9a4ddb474c24b169c3a078886fbc824`](https://github.com/3more102/Superscalar-RISCV-Core/commit/0b00e18ae9a4ddb474c24b169c3a078886fbc824) did not alter RTL, testbench, reference-model, formal, synthesis, or verification-script behavior. Because it modified `reports/final_verification_summary.md`, which is not in the workflow `paths-ignore` list, it correctly triggered GitHub Actions [run #49 / `33903013127`](https://github.com/3more102/Superscalar-RISCV-Core/actions/runs/33903013127).

Run #49 completed with overall conclusion **success**. All five mandatory jobs passed again, including 91-program RTL differential regression, 58/58 functional-event coverage, RTL line/branch/toggle code coverage, RTL single-vs-dual performance, Verilator lint, Yosys synthesis, and formal verification.

Pushes limited to `README.md`, `CHANGELOG.md`, `docs/**`, and the other presentation files explicitly listed in `.github/workflows/rtl-ci.yml` are ignored by push/pull-request CI. `reports/**` is intentionally not part of that ignore set.

The workflow also executes every Monday at `03:17 UTC` for reproducibility.

### Run #48 retained GitHub Actions artifacts

| Artifact | Artifact ID | SHA-256 digest |
|---|---:|---|
| reference-verification-reports | 9947615667 | `f6eebba836caca80c50c35788e7e75b570295f17b2b2163113317eec4bffd4ad` |
| lint-report | 9947634223 | `c97afba00a5822cb9776436f5a0b7ee085aa882a8d04e8baa9bedd92161b9f89` |
| synthesis-report | 9947634201 | `0233529a903a52cbd805f4df8b90e5dd6901fdae118c1d85c189649f48309a45` |
| rtl-simulation-reports | 9947672592 | `bcf65ea4864d18b846efb32a7caf2e7b404063828b19aeef31c2162b5d88016e` |
| formal-reports | 9947699599 | `a161b520384b046e963e43e9e3dd32b594738f9b8b9d2ff71dcc19e77bcfbaf8` |

These are GitHub-reported artifact digests for run #48.

## Reference verification

Executed results:

- Python tests: **25/25 PASS**
- directed architectural programs: **41/41 PASS**
- deterministic random architectural seeds: **500/500 PASS**
- reference commits checked: **47,280**
- required ISA exercise: **47/47 mnemonics**
- reference/stimulus functional coverage: **54/54**
- divider algorithm differential stress: **20,000/20,000 PASS**
- front-end replay stress: **100,000/100,000 cycles PASS**
- replay stress issued instructions: **126,494**
- replay stress redirects: **208**
- cycle-oriented random timing workloads: **500/500 completed**

## RTL differential regression

Backend: **Verilator**.

The RTL regression compares commit behavior and terminal trap state with the Python RV32IM architectural model.

- directed RTL programs: **41/41 PASS**
- random RTL programs: **50/50 PASS**
- total: **91/91 PASS**

The directed suite includes normal execution, dual issue, RAW/WAW dependencies, replay, forwarding, all branch classes, jumps, loads/stores, all eight RV32M operations, divide corners, x0, ECALL/EBREAK, instruction/load/store misalignment, precise traps, byte lanes, signed/unsigned extremes, shift masking, overflow wrapping, and reserved/illegal encodings.

## RTL functional-event coverage

The CI-generated RTL functional coverage report closed **58/58 points**.

Observed branch outcomes:

| Branch | Taken | Not taken |
|---|---:|---:|
| BEQ | 4 | 1 |
| BNE | 1 | 3 |
| BLT | 7 | 2 |
| BGE | 2 | 1 |
| BLTU | 1 | 3 |
| BGEU | 2 | 1 |

Other observed event classes include all load/store sizes, byte/halfword lanes, all eight M operations, instruction/load/store misalignment, illegal/breakpoint/ecall traps, dual/single issue, RAW/WAW/structural blocking, redirects, EX/MEM/WB forwarding, load-use stall, and divider stall.

Representative event totals:

- dual_issue=59
- single_issue=203
- pair_raw=60
- pair_waw=17
- structural_block=552
- redirect=20
- forward_ex=71
- forward_mem=24
- forward_wb=18
- load_use_stall=1
- divider_stall=126

This is functional-event coverage. It is intentionally separate from RTL code coverage.

## RTL line/branch/toggle code coverage

Run #48 reran the same **91 programs** with Verilator code-coverage instrumentation and merged the resulting coverage databases.

| Coverage type | Covered points | Total points | Coverage |
|---|---:|---:|---:|
| Line | 416 | 423 | **98.35%** |
| Branch | 303 | 305 | **99.34%** |
| Toggle | 10,636 | 14,182 | **75.00%** |

Coverage scope and validation:

- reported percentages are **RTL-only**; annotated testbench files are excluded
- **9/9 measurable synthesizable RTL files** appear in both expected coverage evidence paths
- `rtl/common/riscv_pkg.sv` is a definition-only package and is recorded separately because declarations/typedefs do not produce executable Verilator coverage points
- a point is counted covered when executed/toggled at least once (`--annotate-min 1`)
- no arbitrary percentage threshold is imposed in the first baseline
- the gate fails if instrumentation/collection/merge fails, a test fails, an executable RTL source is missing, or line/branch/toggle classes are vacuous

The run #48 JSON report records `valid_non_vacuous_report: true` and `coverage_threshold_enforced: false`.

## RTL performance

The same RTL was built with `ENABLE_DUAL_ISSUE=0` and `ENABLE_DUAL_ISSUE=1`.

| Program | Retired | Single cycles | 2-wide cycles | Single IPC | 2-wide IPC | Speedup | Dual-issue cycles |
|---|---:|---:|---:|---:|---:|---:|---:|
| dependency_100 | 100 | 105 | 105 | 0.952 | 0.952 | 1.000x | 0 |
| independent_200 | 200 | 205 | 105 | 0.976 | 1.905 | 1.952x | 100 |

These values come from RTL simulation of identical programs with only the dual-issue parameter changed.

## Formal verification

Engine: **Yosys-Slang + Yosys SAT**.

The retained run #48 `formal_report.txt` records:

- `issue`: `PASS rc=0 mode=seq depth=1`, followed by a successful SAT proof
- `alu_branch`: `PASS rc=0 mode=seq depth=1`, followed by a successful SAT proof
- `core`: `PASS rc=0 mode=base32 depth=32`

The retained `formal_flow_audit.txt` reports **3 targets** and **0 issues**. For the core target, RF read values plus ALU/MUL/DIV results and branch outcome are explicit formal cutpoints validated before the bounded proof.

### Formal interpretation

The issue and ALU/branch targets are direct symbolic combinational proofs. The core target is a **32-cycle compositional control/order proof**. Datapath result wires are made arbitrary at the cutpoints, so core ordering/control invariants are proven independently of particular values on those result paths. This strengthens control independence but does not constitute a monolithic proof of all RV32IM arithmetic semantics.

## Verilator lint

Verilator version retained by the verified flow: **5.051 devel rev v5.050-309-g228635918**.

Lint policy result:

- warnings: **12**
- allowed categories: `UNUSEDPARAM`, `UNUSEDSIGNAL`
- unexpected warnings: **0**
- job conclusion: **success**

The allowed warnings are intentional unused fields/bits in shared packed structures and helper expressions; no unexpected lint category was accepted by policy.

## Generic Yosys synthesis

Yosys version retained by the verified flow: **0.68+182**.

Final generic statistics for `superscalar_core`:

- wires: **6,742**
- wire bits: **78,709**
- public wires: **223**
- public wire bits: **8,505**
- ports: **51**
- port bits: **1,222**
- generic primitive cells: **43,289**
- `check` problems: **0**
- reported peak memory: **253.56 MB**

The 43,289 cell value is a Yosys generic primitive count after generic technology mapping. It is not standard-cell area, gate-equivalent area, timing, or power.

## First fully green provenance

The first fully green execution of the strengthened five-job flow is retained for history:

- Run: [#20 / 33873379783](https://github.com/3more102/Superscalar-RISCV-Core/actions/runs/33873379783)
- Verified RTL commit: [`94f688763d81035057f7fe00959bfd4f3e3948fc`](https://github.com/3more102/Superscalar-RISCV-Core/commit/94f688763d81035057f7fe00959bfd4f3e3948fc)
- Commit subject: `formal: abstract datapath in 32-cycle control proof`

Run #20 predates the run #48 RTL code-coverage extension; it remains provenance for the earlier verification closure, not the latest code-coverage baseline.

## What is still intentionally unclaimed

No characterized standard-cell Liberty was supplied in this CI run. Therefore the project does **not** claim:

- mapped standard-cell area
- WNS / TNS
- maximum clock frequency
- dynamic or leakage power
- post-layout timing
- PPA
- silicon validation

Those remain separate ASIC implementation gates and are documented in [`asic_timing_flow.md`](asic_timing_flow.md).
