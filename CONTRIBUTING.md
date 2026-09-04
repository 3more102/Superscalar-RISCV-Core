# Contributing

Contributions are welcome when they preserve the project's core rule: **architectural correctness and reproducible evidence take priority over headline performance**.

## Development expectations

- Use synthesizable SystemVerilog for RTL (`always_ff`, `always_comb`, explicit widths, no unintended latches/multiple drivers).
- Keep slot 0 older than slot 1; never permit younger architectural overtaking.
- Add or extend directed/reference tests for every functional RTL change.
- Preserve a failing seed/program when fixing a bug; do not weaken the checker to make RTL pass.
- Do not report lint, formal, synthesis, timing, coverage, IPC, area, or power as PASS/measured unless the corresponding tool actually executed successfully.
- Keep generated EDA binaries, large waveforms, local toolchains, caches, and virtual environments out of Git.

## Before opening a pull request

Run the checks available in your environment:

```bash
python3 -m pip install pytest
python3 -m pytest -q
python3 scripts/run_all_checks.py
git diff --check
```

With OSS CAD Suite/compatible EDA tools installed, also run:

```bash
make rtl
make rtl-coverage
make rtl-perf
make lint
make formal
make synth
```

## Adding an instruction or microarchitectural feature

1. Update decode/execute/control RTL.
2. Add a directed program and expected architectural state.
3. Update the Python reference model when architectural behavior changes.
4. Add hazard/replay/flush assertions as appropriate.
5. Extend coverage points and documentation.
6. Run the failing case, then the full regression.

## Pull requests

Keep changes focused and explain:

- the architectural or verification intent
- affected pipeline/resources
- tests added or changed
- actual executed results
- known limitations or open gates

Do not include unverified performance claims in a PR description or README update.
