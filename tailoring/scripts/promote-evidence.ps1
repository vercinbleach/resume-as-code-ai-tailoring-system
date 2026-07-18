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

function Remove-SandboxTask {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$SandboxRoot
    )
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $resolvedPath = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\', '/')
    $resolvedRoot = (Resolve-Path -LiteralPath $SandboxRoot).Path.TrimEnd('\', '/')
    if (-not (Test-PathInside -Child $resolvedPath -Parent $resolvedRoot)) {
        throw "Refusing to remove sandbox outside its run root: $resolvedPath"
    }
    $parent = [IO.Path]::GetDirectoryName($resolvedPath).TrimEnd('\', '/')
    if (-not $parent.Equals($resolvedRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a non-task sandbox path: $resolvedPath"
    }
    Clear-ReadOnlyTree -Path $resolvedPath
    Remove-Item -LiteralPath $resolvedPath -Recurse -Force
}

function Remove-SessionStaging {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not (Test-PathInside -Child $resolved -Parent $sessionPath)) {
        throw "Refusing to remove staging outside the session: $resolved"
    }
    if (-not ([IO.Path]::GetFileName($resolved)).StartsWith(".reviews-staging-", [StringComparison]::Ordinal)) {
        throw "Refusing to remove an unexpected session directory: $resolved"
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
if ($manifest.status -ne "evidence-pending") {
    throw "Evidence promotion requires status evidence-pending, found: $($manifest.status)"
}

$sandboxRoot = [IO.Path]::GetFullPath([string]$manifest.sandbox_root)
$evidenceSandbox = [IO.Path]::GetFullPath([string]$manifest.tasks.evidence_reviewer.sandbox)
if (-not (Test-PathInside -Child $evidenceSandbox -Parent $sandboxRoot)) {
    throw "Evidence reviewer sandbox is outside the declared sandbox root: $evidenceSandbox"
}

$claimSnapshot = [string]$manifest.snapshots.claim_index.path
if ((Get-Sha256 $claimSnapshot) -ne [string]$manifest.snapshots.claim_index.sha256) {
    throw "Session claim-index snapshot changed."
}
foreach ($snapshotName in @("job_intake", "candidate_pool")) {
    $snapshot = $manifest.snapshots.$snapshotName
    if ((Get-Sha256 ([string]$snapshot.path)) -ne [string]$snapshot.sha256) {
        throw "Session snapshot changed: $snapshotName"
    }
}

$evidenceVerified = Invoke-SandboxTool -ToolArguments @(
    "verify",
    "--sandbox", $evidenceSandbox,
    "--expected-manifest-sha256", [string]$manifest.tasks.evidence_reviewer.manifest_sha256,
    "--require-output"
)

$reviewsPath = Join-Path $sessionPath "reviews"
if (Test-Path -LiteralPath $reviewsPath) {
    throw "Durable review directory already exists: $reviewsPath"
}
$staging = Join-Path $sessionPath ".reviews-staging-$([Guid]::NewGuid().ToString('N'))"
$riskSandbox = Join-Path $sandboxRoot "claim-risk-critic"
$committed = $false
$sourceSnapshotRoot = Join-Path $sessionPath "inputs\source-snapshots"

try {
    New-Item -ItemType Directory -Path $staging | Out-Null
    $evidenceStaged = Join-Path $staging "evidence.json"
    Copy-Item -LiteralPath ([string]$evidenceVerified.output) -Destination $evidenceStaged
    if ((Get-Sha256 $evidenceStaged) -ne [string]$evidenceVerified.output_sha256) {
        throw "Evidence review changed while staging."
    }

    & $python (Join-Path $root "scripts\validate_evidence_findings.py") $evidenceStaged `
        --root $root --claim-index $claimSnapshot `
        --source-root (Join-Path $evidenceSandbox "inputs")
    if ($LASTEXITCODE -ne 0) { throw "Evidence review validation failed." }
    $evidencePacket = Get-Content -Raw -LiteralPath $evidenceStaged | ConvertFrom-Json
    if ($evidencePacket.role -ne "evidence-reviewer") {
        throw "Evidence sandbox emitted the wrong role: $($evidencePacket.role)"
    }

    Move-Item -LiteralPath $staging -Destination $reviewsPath
    $evidencePromoted = Join-Path $reviewsPath "evidence.json"

    $claimsById = @{}
    foreach ($line in @(Get-Content -LiteralPath $claimSnapshot)) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $claim = $line | ConvertFrom-Json
            $claimsById[[string]$claim.id] = $claim
        }
    }
    $referencedClaimIds = @(
        @($evidencePacket.findings) |
            ForEach-Object { @($_.evidence_units) } |
            ForEach-Object { @($_.claim_ids) } |
            ForEach-Object { $_ } |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
            Sort-Object -Unique
    )
    $riskInputs = @(
        "$evidencePromoted::evidence/reviewer.json",
        "$claimSnapshot::knowledge-base/generated/claims.jsonl"
    )
    $referencedSourceFiles = @(
        @($evidencePacket.findings) |
            ForEach-Object { @($_.evidence_units) } |
            ForEach-Object { [string]$_.source_file } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )
    if (Test-Path -LiteralPath $sourceSnapshotRoot) {
        throw "Evidence source snapshot directory already exists: $sourceSnapshotRoot"
    }
    $riskSourceFiles = @{}
    foreach ($relative in $referencedSourceFiles) {
        if (-not $relative.EndsWith(".md", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Referenced evidence source is not Markdown: $relative"
        }
        $reviewerSource = [IO.Path]::GetFullPath((Join-Path (Join-Path $evidenceSandbox "inputs") $relative))
        if (-not (Test-PathInside -Child $reviewerSource -Parent (Join-Path $evidenceSandbox "inputs"))) {
            throw "Referenced evidence source escapes the sandbox inputs: $relative"
        }
        if (-not (Test-Path -LiteralPath $reviewerSource -PathType Leaf)) {
            throw "Referenced evidence source does not exist: $reviewerSource"
        }
        $normalizedRelative = $relative.Replace('\', '/')
        $sourceSnapshot = [IO.Path]::GetFullPath((Join-Path $sourceSnapshotRoot $normalizedRelative))
        if (-not (Test-PathInside -Child $sourceSnapshot -Parent $sourceSnapshotRoot)) {
            throw "Evidence snapshot path escapes its root: $normalizedRelative"
        }
        $sourceSnapshotParent = Split-Path $sourceSnapshot -Parent
        New-Item -ItemType Directory -Path $sourceSnapshotParent -Force | Out-Null
        Copy-Item -LiteralPath $reviewerSource -Destination $sourceSnapshot
        (Get-Item -LiteralPath $sourceSnapshot).IsReadOnly = $true
        $riskSourceFiles[$normalizedRelative] = $sourceSnapshot
    }
    foreach ($relative in @($riskSourceFiles.Keys | Sort-Object)) {
        $riskInputs += "$($riskSourceFiles[$relative])::$relative"
    }

    $riskArguments = @(
        "create",
        "--sandbox", $riskSandbox,
        "--pipeline", "resume-context-builder",
        "--session-id", [string]$manifest.session_id,
        "--task-id", "claim-risk-critic",
        "--skill", (Join-Path $root ".codex\skills\audit-resume-claim-use"),
        "--output-name", "result.json",
        "--promote-to", (Join-Path $reviewsPath "risk.json"),
        "--network", "deny"
    )
    foreach ($inputSpec in $riskInputs) {
        $riskArguments += @("--input", $inputSpec)
    }
    $riskCreated = Invoke-SandboxTool -ToolArguments $riskArguments

    $now = [DateTimeOffset]::UtcNow.ToString("o")
    $manifest.tasks.evidence_reviewer.status = "promoted"
    $manifest.tasks.evidence_reviewer.output_sha256 = [string]$evidenceVerified.output_sha256
    $manifest.tasks.claim_risk_critic = [ordered]@{
        status = "pending"
        sandbox = [string]$riskCreated.sandbox
        manifest_sha256 = [string]$riskCreated.manifest_sha256
        promoted_to = (Join-Path $reviewsPath "risk.json")
        output_sha256 = $null
        referenced_claim_ids = $referencedClaimIds
        referenced_source_files = $referencedSourceFiles
    }
    $manifest.snapshots | Add-Member -NotePropertyName evidence_sources -NotePropertyValue @(
        @($riskSourceFiles.Keys | Sort-Object) | ForEach-Object {
            [ordered]@{
                source_file = $_
                path = [string]$riskSourceFiles[$_]
                sha256 = Get-Sha256 ([string]$riskSourceFiles[$_])
            }
        }
    ) -Force
    $manifest.promotion.evidence_promoted_at = $now
    $manifest.status = "risk-pending"
    Write-JsonFile -Path $manifestPath -Value $manifest
    $committed = $true
}
catch {
    if (-not $committed) {
        if (Test-Path -LiteralPath $riskSandbox) {
            Remove-SandboxTask -Path $riskSandbox -SandboxRoot $sandboxRoot
        }
        if (Test-Path -LiteralPath $reviewsPath) {
            Clear-ReadOnlyTree -Path $reviewsPath
            Remove-Item -LiteralPath $reviewsPath -Recurse -Force
        }
        if (Test-Path -LiteralPath $sourceSnapshotRoot) {
            Clear-ReadOnlyTree -Path $sourceSnapshotRoot
            Remove-Item -LiteralPath $sourceSnapshotRoot -Recurse -Force
        }
        if (Test-Path -LiteralPath $staging) {
            Remove-SessionStaging -Path $staging
        }
    }
    throw
}

$riskPrompt = @'
# Claim-use risk critic prompt

Run this prompt in one new top-level Codex task. Do not use a subagent, fork,
reused task, parent-chat context, or any earlier sandbox.

Open and follow `{RISK_SKILL}`. Treat `{RISK_SANDBOX}` as the complete workspace
and do not read outside it. Write only `{RISK_OUTPUT}`.

Your only evidence packet is `{EVIDENCE_INPUT}`. The only claim index is
`{CLAIM_INDEX}`. Resolve referenced claim sources beneath the sandbox `inputs`
directory.

Audit every proposed `(criterion_id, claim_id)` use. Return only `completed` and
the output path.

After the task finishes, the coordinator runs:

```powershell
.\tailoring\scripts\finalize-context.ps1 -Session "{SESSION}"
```
'@
$riskPrompt = $riskPrompt.Replace("{RISK_SKILL}", (Join-Path $riskSandbox "skill\SKILL.md"))
$riskPrompt = $riskPrompt.Replace("{RISK_SANDBOX}", $riskSandbox)
$riskPrompt = $riskPrompt.Replace("{RISK_OUTPUT}", (Join-Path $riskSandbox "outbox\result.json"))
$riskPrompt = $riskPrompt.Replace("{EVIDENCE_INPUT}", (Join-Path $riskSandbox "inputs\evidence\reviewer.json"))
$riskPrompt = $riskPrompt.Replace("{CLAIM_INDEX}", (Join-Path $riskSandbox "inputs\knowledge-base\generated\claims.jsonl"))
$riskPrompt = $riskPrompt.Replace("{SESSION}", $sessionPath)
$riskPromptPath = Join-Path $sessionPath "risk-task-prompt.md"
[IO.File]::WriteAllText($riskPromptPath, $riskPrompt, [Text.UTF8Encoding]::new($false))

Remove-SandboxTask -Path $evidenceSandbox -SandboxRoot $sandboxRoot

Write-Output $riskPromptPath
