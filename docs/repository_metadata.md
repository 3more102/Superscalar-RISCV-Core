# Repository Metadata and Admin Checklist

Repository:

`3more102/Superscalar-RISCV-Core`

## GitHub About panel

Recommended description:

> 2-wide in-order superscalar RV32IM RISC-V core in synthesizable SystemVerilog with dual issue, forwarding, iterative M-extension, differential verification, formal proofs, and open-source synthesis.

Recommended topics:

`risc-v`, `riscv`, `rv32im`, `cpu`, `processor`, `superscalar`, `systemverilog`, `rtl`, `asic`, `fpga`, `digital-design`, `microarchitecture`, `verification`, `formal-verification`, `yosys`, `verilator`, `symbiyosys`, `computer-architecture`, `pipeline`, `open-source-hardware`

These values are repository presentation metadata only; they do not change RTL behavior or verification status.

## Recommended `main` ruleset

For a public portfolio repository, configure a branch ruleset targeting the default branch (`main`) with:

- block force pushes;
- restrict branch deletion;
- require a pull request before merging if all future changes should be reviewable;
- require the branch to be up to date before merge;
- require the mandatory RTL CI checks when source, verification, formal, synthesis, or workflow files change;
- keep bypass permissions limited to deliberate repository-administration recovery.

The mandatory CI job names are:

1. `Python / Reference Verification`
2. `RTL Simulation / Coverage / Performance`
3. `Verilator Lint`
4. `Formal Verification`
5. `Yosys Synthesis`

Do not enable a signed-commit requirement until commit signing is intentionally configured; the existing project history includes unsigned commits.

## CI path policy

The full EDA suite intentionally ignores maintainer-only presentation files such as issue templates, CODEOWNERS, Dependabot configuration, `.gitattributes`, and this metadata document. RTL/source/tool-flow changes still trigger the strict five-job CI workflow.

## Release policy

`v0.2.0` is the engineering/educational verification-infrastructure release. Create a new release only when engineering behavior, verification evidence, or a meaningful user-facing project capability changes; documentation-only/community-maintenance commits do not require a new version.
