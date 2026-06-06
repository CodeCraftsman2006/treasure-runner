# Build and run Treasure Runner web app (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "==> Installing Python web dependencies..."
pip install -q -r "$Root\python\requirements-web.txt"

Write-Host "==> Building React frontend..."
Push-Location "$Root\web"
npm install
npm run build
Pop-Location

$Config = if ($env:TREASURE_RUNNER_CONFIG) { $env:TREASURE_RUNNER_CONFIG } else { "$Root\assets\starter.ini" }
Write-Host "==> Starting server on http://localhost:8000"
Write-Host "    Share http://YOUR-IP:8000 with students on the same network"
Write-Host "    World config: $Config"

Push-Location "$Root\python"
python run_server.py --host 0.0.0.0 --port 8000 --config $Config
Pop-Location
