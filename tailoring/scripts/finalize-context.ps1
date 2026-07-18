[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Session
)

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sessionPath = (Resolve-Path -LiteralPath $Session).Path
$sessionsRoot = (Resolve-Path -LiteralPath (Join-Path $root "tailoring\sessions")).Path
$python = Join-Path $root "qa\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}
$sandboxTool = Join-Path $root "scripts\sandbox_workspace.py"

function Test-PathInside {
    param(
        [Parameter(Mandatory = $true)][string]$Child,
        [Parameter(Mandatory = $true)][string]$Parent
    )
    $parentPrefix = [IO.Path]::GetFullPath($Parent).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    $childPath = [IO.Path]::GetFullPath($Child)
    return $childPath.StartsWith($parentPrefix, [StringComparison]::OrdinalIgnoreCase)
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $temporary = "$Path.tmp-$([Guid]::NewGuid().ToString('N'))"
    $json = $Value | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText($temporary, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Invoke-SandboxTool {
    param([Parameter(Mandatory = $true)][string[]]$ToolArguments)
    $lines = @(& $python $sandboxTool @ToolArguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Sandbox tool failed: $($lines -join [Environment]::NewLine)"
    }
    try {
        return (($lines -join [Environment]::NewLine) | ConvertFrom-Json)
    }
    catch {
        throw "Sandbox tool returned invalid JSON: $($lines -join [Environment]::NewLine)"
    }
}

function Clear-ReadOnlyTree {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    foreach ($item in @(Get-ChildItem -LiteralPath $Path -Recurse -Force)) {
        if (-not $item.PSIsContainer -and $item.IsReadOnly) {
            $item.IsReadOnly = $false
        }
    }
}

function Remove-SandboxRun {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedRiskSandbox
    )
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $resolved = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\', '/')
    $volumeRoot = [IO.Path]::GetPathRoot($resolved).TrimEnd('\', '/')
    if ($resolved.Equals($volumeRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a volume root: $resolved"
    }
    foreach ($protected in @($root, $sessionPath)) {
        $protectedPath = [IO.Path]::GetFullPath($protected).TrimEnd('\', '/')
        if ($resolved.Equals($protectedPath, [StringComparison]::OrdinalIgnoreCase) -or
            (Test-PathInside -Child $protectedPath -Parent $resolved)) {
            throw "Refusing to remove sandbox root containing protected path: $protectedPath"
        }
    }
    $expected = [IO.Path]::GetFullPath($ExpectedRiskSandbox).TrimEnd('\', '/')
    if (-not (Test-PathInside -Child $expected -Parent $resolved)) {
        throw "Risk sandbox is outside its declared run root: $expected"
    }
    $children = @(Get-ChildItem -LiteralPath $resolved -Force)
    foreach ($child in $children) {
        if (-not $child.FullName.TrimEnd('\', '/').Equals($expected, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to delete sandbox root with unexpected content: $($child.FullName)"
        }
    }
    Clear-ReadOnlyTree -Path $resolved
    Remove-Item -LiteralPath $resolved -Recurse -Force
}

if (-not (Test-PathInside -Child $sessionPath -Parent $sessionsRoot)) {
    throw "Session must be inside $sessionsRoot"
}

$manifestPath = Join-Path $sessionPath "manifest.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Missing session manifest: $manifestPath"
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.pipeline -ne "resume-context-builder") {
    throw "Session manifest is not a context-builder session."
}

$sandboxRoot = [IO.Path]::GetFullPath([string]$manifest.sandbox_root)
$riskSandbox = [IO.Path]::GetFullPath([string]$manifest.tasks.claim_risk_critic.sandbox)
$output = Join-Path $sessionPath "output\context-pack.json"

if ($manifest.status -eq "complete-pending-cleanup") {
    Remove-SandboxRun -Path $sandboxRoot -ExpectedRiskSandbox $riskSandbox
    $manifest.cleanup.status = "completed"
    $manifest.cleanup.completed_at = [DateTimeOffset]::UtcNow.ToString("o")
    $manifest.status = "completed"
    Write-JsonFile -Path $manifestPath -Value $manifest
    Write-Output $output
    exit 0
}
if ($manifest.status -ne "risk-pending") {
    throw "Context finalization requires status risk-pending, found: $($manifest.status)"
}
if (-not (Test-PathInside -Child $riskSandbox -Parent $sandboxRoot)) {
    throw "Risk sandbox is outside the declared sandbox root: $riskSandbox"
}

foreach ($snapshotName in @("job_intake", "candidate_pool", "claim_index")) {
    $snapshot = $manifest.snapshots.$snapshotName
    if ((Get-Sha256 ([string]$snapshot.path)) -ne [string]$snapshot.sha256) {
        throw "Session snapshot changed: $snapshotName"
    }
}
$evidence = Join-Path $sessionPath "reviews\evidence.json"
if (-not (Test-Path -LiteralPath $evidence -PathType Leaf)) {
    throw "Missing promoted evidence review: $evidence"
}
if ((Get-Sha256 $evidence) -ne [string]$manifest.tasks.evidence_reviewer.output_sha256) {
    throw "Promoted evidence review changed: $evidence"
}

$riskVerified = Invoke-SandboxTool -ToolArguments @(
    "verify",
    "--sandbox", $riskSandbox,
    "--expected-manifest-sha256", [string]$manifest.tasks.claim_risk_critic.manifest_sha256,
    "--require-output"
)

$riskStaging = Join-Path $sessionPath ".risk-staging-$([Guid]::NewGuid().ToString('N')).json"
$contextStaging = Join-Path $sessionPath "output\.context-pack-staging-$([Guid]::NewGuid().ToString('N')).json"
$risk = Join-Path $sessionPath "reviews\risk.json"
if (Test-Path -LiteralPath $risk) {
    throw "Durable risk packet already exists: $risk"
}
if (Test-Path -LiteralPath $output) {
    throw "Context pack already exists: $output"
}
$riskPromoted = $false
$contextPromoted = $false
$committed = $false

try {
    Copy-Item -LiteralPath ([string]$riskVerified.output) -Destination $riskStaging
    if ((Get-Sha256 $riskStaging) -ne [string]$riskVerified.output_sha256) {
        throw "Risk output changed while staging."
    }
    & $python (Join-Path $root "scripts\validate_evidence_findings.py") $riskStaging `
        --root $root --claim-index ([string]$manifest.snapshots.claim_index.path) `
        --source-root (Join-Path $riskSandbox "inputs")
    if ($LASTEXITCODE -ne 0) { throw "Risk packet validation failed." }
    $riskPacket = Get-Content -Raw -LiteralPath $riskStaging | ConvertFrom-Json
    if ($riskPacket.role -ne "claim-risk-critic") {
        throw "Risk sandbox emitted the wrong role: $($riskPacket.role)"
    }
    Move-Item -LiteralPath $riskStaging -Destination $risk
    $riskPromoted = $true

    & $python (Join-Path $root "scripts\assemble_context_pack.py") `
        --job-intake (Join-Path $sessionPath "inputs\job-intake.json") `
        --candidates (Join-Path $sessionPath "inputs\candidate-pool.json") `
        --evidence-review $evidence `
        --claim-use-risk $risk `
        --source-root (Join-Path $riskSandbox "inputs") `
        --output $contextStaging `
        --root $root `
        --claim-index ([string]$manifest.snapshots.claim_index.path)
    if ($LASTEXITCODE -ne 0) { throw "Context pack assembly failed." }
    & $python (Join-Path $root "scripts\validate_context_artifact.py") `
        context-pack $contextStaging --root $root `
        --claim-index ([string]$manifest.snapshots.claim_index.path) `
        --source-root (Join-Path $riskSandbox "inputs")
    if ($LASTEXITCODE -ne 0) { throw "Context pack validation failed." }
    Move-Item -LiteralPath $contextStaging -Destination $output
    $contextPromoted = $true

    $now = [DateTimeOffset]::UtcNow.ToString("o")
    $manifest.tasks.claim_risk_critic.status = "promoted"
    $manifest.tasks.claim_risk_critic.output_sha256 = Get-Sha256 $risk
    $manifest.promotion.risk_promoted_at = $now
    $manifest.promotion.context_pack = [ordered]@{
        path = $output
        sha256 = Get-Sha256 $output
        promoted_at = $now
    }
    $manifest.status = "complete-pending-cleanup"
    Write-JsonFile -Path $manifestPath -Value $manifest
    $committed = $true
}
catch {
    if (-not $committed) {
        if (Test-Path -LiteralPath $contextStaging) {
            Remove-Item -LiteralPath $contextStaging -Force
        }
        if ($contextPromoted -and (Test-Path -LiteralPath $output)) {
            Remove-Item -LiteralPath $output -Force
        }
        if (Test-Path -LiteralPath $riskStaging) {
            Remove-Item -LiteralPath $riskStaging -Force
        }
        if ($riskPromoted -and (Test-Path -LiteralPath $risk)) {
            Remove-Item -LiteralPath $risk -Force
        }
    }
    throw
}

Remove-SandboxRun -Path $sandboxRoot -ExpectedRiskSandbox $riskSandbox
$manifest.cleanup.status = "completed"
$manifest.cleanup.completed_at = [DateTimeOffset]::UtcNow.ToString("o")
$manifest.status = "completed"
Write-JsonFile -Path $manifestPath -Value $manifest

Write-Output $output
