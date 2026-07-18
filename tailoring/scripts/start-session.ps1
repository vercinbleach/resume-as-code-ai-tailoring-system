[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$JobIntake,
    [string]$BaseResume,
    [string]$SessionId,
    [string]$SandboxRoot
)

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$python = Join-Path $root "qa\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { $python = "python" }
$arguments = @(
    (Join-Path $root "scripts\resume_composer_pipeline.py"),
    "start",
    "--job-intake", $JobIntake
)
if ($BaseResume) { $arguments += @("--base-resume", $BaseResume) }
if ($SessionId) { $arguments += @("--session-id", $SessionId) }
if ($SandboxRoot) { $arguments += @("--sandbox-root", $SandboxRoot) }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "Resume Composer session start failed." }
