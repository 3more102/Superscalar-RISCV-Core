$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ToolsRoot = Join-Path $ProjectRoot "tools"
$SuiteDir = Join-Path $ToolsRoot "oss-cad-suite"
$Archive = Join-Path $ToolsRoot "oss-cad-suite-windows-x64.tgz"

Write-Host "Project: $ProjectRoot"
Write-Host "EDA tools will stay under: $ToolsRoot"

if (Test-Path (Join-Path $SuiteDir "bin\verilator.exe")) {
    Write-Host "OSS CAD Suite already present."
} else {
    Write-Host "Querying latest YosysHQ OSS CAD Suite release..."
    $release = Invoke-RestMethod -Headers @{"User-Agent"="Superscalar-RISCV-Core-bootstrap"} `
        -Uri "https://api.github.com/repos/YosysHQ/oss-cad-suite-build/releases/latest"
    $asset = $release.assets | Where-Object { $_.name -match '^oss-cad-suite-windows-x64-[0-9]+\.tgz$' } | Select-Object -First 1
    if (-not $asset) { throw "Could not find windows-x64 OSS CAD Suite asset in latest release." }

    Write-Host "Downloading $($asset.name) ..."
    Invoke-WebRequest -Headers @{"User-Agent"="Superscalar-RISCV-Core-bootstrap"} `
        -Uri $asset.browser_download_url -OutFile $Archive

    Write-Host "Extracting..."
    tar -xzf $Archive -C $ToolsRoot
    Remove-Item $Archive -Force
    if (-not (Test-Path (Join-Path $SuiteDir "bin\verilator.exe"))) {
        throw "Extraction completed but verilator.exe was not found under $SuiteDir\bin"
    }
}

$env:PATH = "$(Join-Path $SuiteDir 'bin');$env:PATH"
Write-Host ""
Write-Host "Installed tool versions:" -ForegroundColor Cyan
& verilator --version
& yosys --version
if (Get-Command sby -ErrorAction SilentlyContinue) { & sby --version }
if (Get-Command iverilog -ErrorAction SilentlyContinue) { & iverilog -V 2>&1 | Select-Object -First 2 }

Write-Host ""
Write-Host "Current PowerShell PATH has been updated for this process." -ForegroundColor Green
Write-Host "Run: powershell -ExecutionPolicy Bypass -File tools\run_full_verification.ps1"
