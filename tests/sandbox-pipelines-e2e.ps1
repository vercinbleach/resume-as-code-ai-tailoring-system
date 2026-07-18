[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root "qa\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { $python = "python" }

Push-Location $root
try {
    & $python -m unittest tests.test_sandbox_workspace tests.test_resume_composer_pipeline
    if ($LASTEXITCODE -ne 0) { throw "Sandbox and Resume Composer E2E tests failed." }
}
finally {
    Pop-Location
}
