# Local EDA bootstrap

The project does not require the RISC-V GCC toolchain for baseline tests because it includes a controlled RV32IM encoder.

## Windows / PowerShell

From `E:\Superscalar_RISCV_Core`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\bootstrap_eda.ps1
powershell -ExecutionPolicy Bypass -File tools\run_full_verification.ps1
```

The OSS CAD Suite is downloaded under the repository's own `tools\` directory, so the project does not need to install the EDA binaries on `C:\`.

## WSL / Linux

```bash
./tools/bootstrap_eda.sh
source tools/env_eda.sh
python3 scripts/run_all_checks.py
```

The bootstrap queries the latest YosysHQ OSS CAD Suite release rather than hard-coding a dated archive URL.
