## Summary

Describe the change and why it is needed.

## Area

- [ ] RTL / microarchitecture
- [ ] Testbench / assertions
- [ ] Reference model / test generation
- [ ] Formal verification
- [ ] Synthesis / timing flow
- [ ] CI / tooling
- [ ] Documentation only

## Verification performed

List the exact commands and results that were executed. Do not mark a tool-dependent gate PASS unless it actually ran.

- [ ] `python3 -m pytest -q tb/tests`
- [ ] `make test`
- [ ] `make rtl`
- [ ] `make rtl-coverage`
- [ ] `make rtl-perf`
- [ ] `make lint`
- [ ] `make formal`
- [ ] `make synth`

## Architectural impact

State whether the change affects ISA behavior, issue/replay policy, forwarding, traps, memory side effects, performance counters, or commit-trace semantics. Write `None` when it does not.

## Evidence / first divergence

For bug fixes, preserve the failing test and identify the first failing PC/instruction or proof obligation. Include only concise logs or links to CI artifacts.

## Claim discipline

- [ ] No unexecuted simulation/formal/synthesis result is presented as PASS.
- [ ] Model-level performance is not presented as RTL-measured performance.
- [ ] Generic Yosys cell counts are not presented as ASIC area.
- [ ] No frequency/WNS/TNS/power claim is added without characterized implementation evidence.

## Checklist

- [ ] `git diff --check` is clean.
- [ ] New behavior has a regression test or formal property where practical.
- [ ] Existing expected outputs were not changed merely to match incorrect RTL.
- [ ] Documentation was updated when externally visible behavior changed.
