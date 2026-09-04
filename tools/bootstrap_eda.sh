#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$ROOT/tools"
SUITE="$TOOLS/oss-cad-suite"
mkdir -p "$TOOLS"

arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) asset_re='^oss-cad-suite-linux-x64-[0-9]+\.tgz$' ;;
  aarch64|arm64) asset_re='^oss-cad-suite-linux-arm64-[0-9]+\.tgz$' ;;
  *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
esac

if [[ ! -x "$SUITE/bin/verilator" ]]; then
  python3 - "$TOOLS" "$asset_re" <<'PY'
import json,re,sys,urllib.request,subprocess,os
from pathlib import Path
tools=Path(sys.argv[1]); pat=re.compile(sys.argv[2])
req=urllib.request.Request('https://api.github.com/repos/YosysHQ/oss-cad-suite-build/releases/latest',headers={'User-Agent':'Superscalar-RISCV-Core-bootstrap'})
with urllib.request.urlopen(req) as r: rel=json.load(r)
asset=next((a for a in rel['assets'] if pat.match(a['name'])),None)
if not asset: raise SystemExit('No matching OSS CAD Suite asset found')
archive=tools/asset['name']
print('Downloading',asset['browser_download_url'])
urllib.request.urlretrieve(asset['browser_download_url'],archive)
subprocess.run(['tar','-xzf',str(archive),'-C',str(tools)],check=True)
archive.unlink()
PY
fi
export PATH="$SUITE/bin:$PATH"
verilator --version
yosys --version
command -v sby >/dev/null && sby --version || true
printf '\nRun in this shell:\n  source tools/env_eda.sh\n  REQUIRE_EDA=1 python3 scripts/run_all_checks.py\n'
