$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$tectonic = "C:\Users\Vincenzo\.cache\codex-tools\tectonic-0.16.9\tectonic.exe"
$source = Join-Path $projectRoot "resumes\vincenzo-rosciano-jake.tex"
$output = Join-Path $projectRoot "output\pdf"

if (-not (Test-Path -LiteralPath $tectonic)) {
    throw "Tectonic was not found at $tectonic"
}

& $tectonic $source --outdir $output
