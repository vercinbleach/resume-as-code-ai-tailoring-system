$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$projectRoot = Split-Path -Parent $PSScriptRoot
$renderCV = Join-Path $projectRoot ".venv\Scripts\rendercv.exe"
$resumeSource = Join-Path $projectRoot "resumes\vincenzo-rosciano-jakes-cambria.yaml"
$outputRoot = Join-Path $projectRoot "output\pdf\rendercv-themes"
$themes = @(
    "classic",
    "engineeringclassic",
    "engineeringresumes",
    "harvard",
    "moderncv"
)

if (-not (Test-Path -LiteralPath $renderCV)) {
    throw "RenderCV was not found at $renderCV"
}

foreach ($theme in $themes) {
    $design = Join-Path $projectRoot "resumes\variants\rendercv-theme-$theme.yaml"
    $output = Join-Path $outputRoot $theme
    & $renderCV render $resumeSource --design $design --output-folder $output --quiet
}
