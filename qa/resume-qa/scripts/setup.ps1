[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$QaRoot = Split-Path -Parent $SkillRoot
$ProjectRoot = Split-Path -Parent $QaRoot
$VenvRoot = Join-Path $QaRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$ProjectPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $QaRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    if (Test-Path -LiteralPath $ProjectPython) {
        $BootstrapPython = $ProjectPython
    }
    else {
        $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $PythonCommand) {
            throw "Python was not found. Install Python 3.11+ or create the project .venv first."
        }
        $BootstrapPython = $PythonCommand.Source
    }

    Write-Host "Creating isolated QA environment at $VenvRoot"
    & $BootstrapPython -m venv $VenvRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the QA virtual environment."
    }
}

Write-Host "Installing deterministic QA dependencies"
& $VenvPython -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Could not install QA dependencies."
}

Write-Host "Resume QA is ready. Semantic evaluation remains Codex-only."
