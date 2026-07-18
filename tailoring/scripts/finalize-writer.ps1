[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$Session)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$python = Join-Path $root "qa\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { $python = "python" }
& $python (Join-Path $root "scripts\resume_composer_pipeline.py") finalize --session $Session
if ($LASTEXITCODE -ne 0) { throw "Resume Composer finalization failed." }
