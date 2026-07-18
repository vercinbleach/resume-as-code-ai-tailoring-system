[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$Session)

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$python = Join-Path $root "qa\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { $python = "python" }
& $python (Join-Path $root "scripts\resume_composer_pipeline.py") prepare-composer --session $Session
if ($LASTEXITCODE -ne 0) { throw "Resume Composer preparation failed." }
