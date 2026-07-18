$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$projectRoot = Split-Path -Parent $PSScriptRoot
$renderCV = Join-Path $projectRoot ".venv\Scripts\rendercv.exe"
$resumeSource = Join-Path $projectRoot "resumes\vincenzo-rosciano-jakes-cambria.yaml"

if (-not (Test-Path -LiteralPath $renderCV)) {
    throw "RenderCV was not found at $renderCV"
}

& $renderCV render $resumeSource --quiet
