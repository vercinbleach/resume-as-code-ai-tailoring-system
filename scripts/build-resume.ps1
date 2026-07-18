$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$projectRoot = Split-Path -Parent $PSScriptRoot
$renderCV = Join-Path $projectRoot ".venv\Scripts\rendercv.exe"
$resumeSource = Join-Path $projectRoot "resumes\vincenzo-rosciano-one-page.yaml"

if (-not (Test-Path -LiteralPath $renderCV)) {
    throw "RenderCV is not installed. Create .venv and install requirements.txt first."
}

& $renderCV render $resumeSource
