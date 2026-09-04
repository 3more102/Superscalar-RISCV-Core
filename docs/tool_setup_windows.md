# Closing the RTL Gates on Windows / E:\

The project is designed to live at `E:\Superscalar_RISCV_Core`. The cleanest open-source flow on Windows is WSL2 with an OSS CAD Suite environment, or individual Icarus/Verilator/Yosys installations.

## Required gate order

1. confirm tools: `python3 scripts/detect_tools.py`
2. run strict full flow: `make ci` (requires EDA gates, unlike local `make test`)
3. run RTL commit equivalence: `make rtl`
4. real single-vs-dual RTL performance: `make rtl-perf`
5. lint: `make lint`
6. synthesis: `make synth`
7. formal: `make formal`

`make rtl` prefers Verilator `--binary --timing --assert` for SystemVerilog support and falls back to Icarus when only `iverilog` + `vvp` are available.

Inside WSL, the Windows E: drive is normally visible as `/mnt/e`. From the repository:

```bash
cd /mnt/e/Superscalar_RISCV_Core
python3 scripts/detect_tools.py
make ci
```

Do not copy any timing, frequency, area, cell-count or formal result into the README unless the corresponding command actually ran successfully and left its report under `reports/`.

## One-command PowerShell flow

From `E:\Superscalar_RISCV_Core`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\run_full_verification.ps1
```

The script bootstraps the latest Windows x64 OSS CAD Suite **inside the project `tools\` directory**, sets `REQUIRE_EDA=1`, and fails if RTL simulation, RTL coverage/performance, lint, formal, or synthesis is unavailable or fails.

## Optional technology-mapped ASIC timing

After generic RTL gates are closed, a characterized standard-cell library may be supplied explicitly:

```bash
export LIBERTY_FILE=/path/to/stdcells.lib
export SDC_FILE=/path/to/core.sdc   # or set CLOCK_PERIOD_NS explicitly
make asic
```

The ASIC flow is intentionally not part of `make ci` because the repository does not bundle a characterized Liberty library. See `docs/asic_timing_flow.md`.
