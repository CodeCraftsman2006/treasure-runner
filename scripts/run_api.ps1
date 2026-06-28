# Start the API server in WSL (required on Windows — the C backend is Linux-only)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$WslRoot = wsl wslpath -a $Root

Write-Host "Starting API server in WSL..."
Write-Host "Keep this window open. In another terminal run: cd web && npm run dev"
Write-Host ""

wsl -e bash -lc "cd '$WslRoot' && bash scripts/run_api.sh"
