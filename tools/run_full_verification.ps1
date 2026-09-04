$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SuiteDir = Join-Path $PSScriptRoot "oss-cad-suite"

if (-not (Test-Path (Join-Path $SuiteDir "bin\verilator.exe"))) {
    & (Join-Path $PSScriptRoot "bootstrap_eda.ps1")
}
$env:PATH = "$(Join-Path $SuiteDir 'bin');$env:PATH"
Set-Location $ProjectRoot

$required = @("verilator","yosys","sby")
foreach ($tool in $required) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required verification tool is still unavailable: $tool"
    }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python is required. Install Python 3 and ensure 'python' is in PATH." }

Write-Host "=== Superscalar RV32IM full verification ===" -ForegroundColor Cyan
python scripts/detect_tools.py
$env:REQUIRE_EDA = "1"
python scripts/run_all_checks.py
if ($LASTEXITCODE -ne 0) { throw "Full verification failed. See reports/." }

Write-Host ""
Write-Host "Verification completed. Important evidence:" -ForegroundColor Green
Write-Host "  reports\simulation\rtl_regression.log"
Write-Host "  reports\coverage\rtl_functional_coverage.md"
Write-Host "  reports\performance\rtl_performance_comparison.md"
Write-Host "  reports\lint_report.txt"
Write-Host "  reports\formal\formal_report.txt"
Write-Host "  reports\synthesis\synthesis_report.txt"
