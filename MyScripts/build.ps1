# Clean prior PyInstaller output and build a new windowed executable.
# Run from Explorer (right-click Run with PowerShell) or: powershell -File build.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found. Install build deps:"
    Write-Host "  pip install -r requirements.txt -r requirements-build.txt"
    exit 1
}

if (Test-Path (Join-Path $Root "requirements.txt")) {
    python -m pip install -q -r (Join-Path $Root "requirements.txt")
}

$dist = Join-Path $Root "dist"
$build = Join-Path $Root "build"
foreach ($p in @($dist, $build)) {
    if (Test-Path $p) {
        Write-Host "Removing $p"
        Remove-Item -LiteralPath $p -Recurse -Force
    }
}

Write-Host "Building TLOPOPotionsMaster.exe (PyInstaller)..."
python -m PyInstaller --clean --noconfirm (Join-Path $Root "brew_gui.spec")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$exe = Join-Path $dist "TLOPOPotionsMaster.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Expected output not found: $exe"
    exit 1
}

Write-Host "Done: $exe"
