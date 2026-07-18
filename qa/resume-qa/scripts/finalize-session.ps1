[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Session
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$QaRoot = Split-Path -Parent $SkillRoot
$ProjectRoot = Split-Path -Parent $QaRoot
$VenvPython = Join-Path $QaRoot ".venv\Scripts\python.exe"
$SandboxWorkspaceScript = Join-Path $ProjectRoot "scripts\sandbox_workspace.py"
$EvaluatorValidator = Join-Path $PSScriptRoot "validate_evaluator.py"
$ReportAssembler = Join-Path $PSScriptRoot "assemble_report.py"
$ReportValidator = Join-Path $PSScriptRoot "validate_report.py"

function Resolve-SessionDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        $Candidate = [System.IO.Path]::GetFullPath($PathValue)
    }
    else {
        $ProjectCandidate = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $PathValue))
        $IdCandidate = [System.IO.Path]::GetFullPath((Join-Path $QaRoot "sessions\$PathValue"))
        if (Test-Path -LiteralPath $ProjectCandidate -PathType Container) {
            $Candidate = $ProjectCandidate
        }
        else {
            $Candidate = $IdCandidate
        }
    }

    if (-not (Test-Path -LiteralPath $Candidate -PathType Container)) {
        throw "Session directory not found: $PathValue"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Candidate "manifest.json") -PathType Leaf)) {
        throw "Session manifest not found: $Candidate"
    }
    return (Resolve-Path -LiteralPath $Candidate).Path
}

function Test-PathContainedBy {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Child,
        [Parameter(Mandatory = $true)]
        [string]$Parent
    )

    $ChildFull = [System.IO.Path]::GetFullPath($Child)
    $ParentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd([char[]]@(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ))
    $Prefix = $ParentFull + [System.IO.Path]::DirectorySeparatorChar
    return $ChildFull.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-NamedPropertyValue {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Object,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $Property = $Object.PSObject.Properties[$Name]
    if (-not $Property) {
        throw "Missing manifest property: $Name"
    }
    return $Property.Value
}

function Invoke-SandboxHelper {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $Output = & $VenvPython $SandboxWorkspaceScript @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "Sandbox validation failed: $($Output -join ' ')"
    }
    try {
        return (($Output -join "`n") | ConvertFrom-Json)
    }
    catch {
        throw "Sandbox helper returned invalid JSON."
    }
}

function Write-ManifestAtomically {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Value,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $Temporary = "$Path.tmp-$([System.Guid]::NewGuid().ToString('N'))"
    try {
        $Value | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Temporary -Encoding utf8
        Move-Item -LiteralPath $Temporary -Destination $Path -Force
    }
    finally {
        if (Test-Path -LiteralPath $Temporary -PathType Leaf) {
            Remove-Item -LiteralPath $Temporary -Force
        }
    }
}

function Clear-ReadOnlyTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    Get-ChildItem -LiteralPath $Path -Recurse -Force | ForEach-Object {
        if ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
            $_.Attributes = $_.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
        }
    }
    $RootItem = Get-Item -LiteralPath $Path -Force
    if ($RootItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
        $RootItem.Attributes = $RootItem.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
    }
}

function Remove-CheckedDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$RequiredParent
    )

    $FullPath = [System.IO.Path]::GetFullPath($Path)
    $FullParent = [System.IO.Path]::GetFullPath($RequiredParent)
    if (-not (Test-PathContainedBy -Child $FullPath -Parent $FullParent)) {
        throw "Refusing to remove a directory outside its declared parent: $FullPath"
    }
    if (-not (Test-Path -LiteralPath $FullPath)) {
        return
    }
    $Item = Get-Item -LiteralPath $FullPath -Force
    if (-not $Item.PSIsContainer -or ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing to remove a non-directory or reparse point: $FullPath"
    }
    Clear-ReadOnlyTree -Path $FullPath
    Remove-Item -LiteralPath $FullPath -Recurse -Force
    if (Test-Path -LiteralPath $FullPath) {
        throw "Could not remove directory: $FullPath"
    }
}

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "QA environment not found. Run .\qa\resume-qa\scripts\setup.ps1 first."
}
foreach ($RequiredScript in @($SandboxWorkspaceScript, $EvaluatorValidator, $ReportAssembler, $ReportValidator)) {
    if (-not (Test-Path -LiteralPath $RequiredScript -PathType Leaf)) {
        throw "Required script not found: $RequiredScript"
    }
}

$SessionPath = Resolve-SessionDirectory -PathValue $Session
$ManifestPath = Join-Path $SessionPath "manifest.json"
$Manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $ManifestPath | ConvertFrom-Json
if (-not $Manifest.sandbox -or -not $Manifest.sandbox.workspaces) {
    throw "Session does not contain lightweight sandbox metadata."
}
if ($Manifest.sandbox.status -eq "completed") {
    throw "Session is already finalized: $SessionPath"
}

$SemanticModes = @($Manifest.modes | Where-Object { $_ -ne "pdf" })
$SandboxRootPath = [System.IO.Path]::GetFullPath([string]$Manifest.sandbox.root)
$EvaluatorsPath = Join-Path $SessionPath "evaluators"

if ($Manifest.sandbox.status -eq "promoted-and-validated") {
    if (-not (Test-Path -LiteralPath $EvaluatorsPath -PathType Container)) {
        throw "Finalization checkpoint is missing its durable evaluator directory: $EvaluatorsPath"
    }
    $ExpectedNames = @($SemanticModes | ForEach-Object { "$_.json" } | Sort-Object)
    $ActualNames = @(Get-ChildItem -LiteralPath $EvaluatorsPath -File -Force | Select-Object -ExpandProperty Name | Sort-Object)
    $UnexpectedDirectories = @(Get-ChildItem -LiteralPath $EvaluatorsPath -Directory -Force)
    if ($UnexpectedDirectories.Count -ne 0 -or (Compare-Object -ReferenceObject $ExpectedNames -DifferenceObject $ActualNames).Count -ne 0) {
        throw "Durable evaluator inventory does not match the finalization checkpoint."
    }
    foreach ($Mode in $SemanticModes) {
        $Receipt = Get-NamedPropertyValue -Object $Manifest.sandbox.promotion_receipts -Name $Mode
        $EvaluatorPath = Join-Path $EvaluatorsPath "$Mode.json"
        $ExpectedReceiptPath = "evaluators/$Mode.json"
        if ($Receipt.path -ne $ExpectedReceiptPath) {
            throw "Promotion receipt path is invalid: $Mode"
        }
        $ActualHash = (Get-FileHash -LiteralPath $EvaluatorPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if (-not $ActualHash.Equals(([string]$Receipt.sha256).ToLowerInvariant(), [System.StringComparison]::Ordinal)) {
            throw "Promoted evaluator hash changed after validation: $Mode"
        }
        $ValidationOutput = & $VenvPython $EvaluatorValidator $EvaluatorPath --expected $Mode
        $ValidationExit = $LASTEXITCODE
        $ValidationOutput | ForEach-Object { Write-Host $_ }
        if ($ValidationExit -ne 0) {
            throw "Promoted evaluator is no longer valid: $Mode"
        }
    }
    $ReportValidationOutput = & $VenvPython $ReportValidator (Join-Path $SessionPath "report.json")
    $ReportValidationExit = $LASTEXITCODE
    $ReportValidationOutput | ForEach-Object { Write-Host $_ }
    if ($ReportValidationExit -ne 0) {
        throw "Finalization checkpoint report is invalid."
    }
    if (Test-Path -LiteralPath $SandboxRootPath) {
        foreach ($Mode in $SemanticModes) {
            $Workspace = Get-NamedPropertyValue -Object $Manifest.sandbox.workspaces -Name $Mode
            if (-not (Test-PathContainedBy -Child ([string]$Workspace.path) -Parent $SandboxRootPath)) {
                throw "Refusing cleanup because a workspace escaped the sandbox root: $Mode"
            }
        }
        Remove-CheckedDirectory -Path $SandboxRootPath -RequiredParent (Split-Path -Parent $SandboxRootPath)
    }
    $Manifest.sandbox.status = "completed"
    $Manifest.sandbox | Add-Member -NotePropertyName removed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString("o")) -Force
    Write-ManifestAtomically -Value $Manifest -Path $ManifestPath
    Write-Output $SessionPath
    return
}

if (Test-Path -LiteralPath $EvaluatorsPath) {
    throw "Durable evaluator directory must not exist before finalization: $EvaluatorsPath"
}

$Verified = [ordered]@{}
foreach ($Mode in $SemanticModes) {
    $Workspace = Get-NamedPropertyValue -Object $Manifest.sandbox.workspaces -Name $Mode
    $WorkspacePath = [System.IO.Path]::GetFullPath([string]$Workspace.path)
    if (-not (Test-PathContainedBy -Child $WorkspacePath -Parent $SandboxRootPath)) {
        throw "Evaluator sandbox is outside the declared sandbox root: $Mode"
    }

    $Check = Invoke-SandboxHelper -Arguments @(
        "verify",
        "--sandbox", $WorkspacePath,
        "--expected-manifest-sha256", [string]$Workspace.manifest_sha256,
        "--require-output"
    )
    if ($Check.manifest.pipeline -ne "resume-qa" -or $Check.manifest.session_id -ne $Manifest.session_id -or $Check.manifest.task_id -ne $Mode) {
        throw "Sandbox identity does not match the session manifest: $Mode"
    }
    if ($Check.manifest.skill.path -ne "skill/SKILL.md" -or $Check.manifest.output.path -ne "outbox/result.json") {
        throw "Sandbox skill or output contract is invalid: $Mode"
    }

    $ExpectedPromotion = [System.IO.Path]::GetFullPath((Join-Path $SessionPath "evaluators\$Mode.json"))
    $DeclaredPromotion = [System.IO.Path]::GetFullPath([string]$Check.manifest.output.promote_to)
    if (-not $DeclaredPromotion.Equals($ExpectedPromotion, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Sandbox promotion destination is invalid: $Mode"
    }

    [string[]]$ExpectedInputs = @("inputs/resume.pdf")
    if ($Mode -in @("job-match", "callback")) {
        $ExpectedInputs += "inputs/job-description.md"
    }
    [string[]]$ActualInputs = @($Check.manifest.inputs | ForEach-Object { [string]$_.path } | Sort-Object)
    [string[]]$SortedExpectedInputs = @($ExpectedInputs | Sort-Object)
    if ((Compare-Object -ReferenceObject $SortedExpectedInputs -DifferenceObject $ActualInputs).Count -ne 0) {
        throw "Sandbox input boundary is invalid: $Mode"
    }

    $Verified[$Mode] = [ordered]@{
        source = [System.IO.Path]::GetFullPath([string]$Check.output)
        sha256 = [string]$Check.output_sha256
        destination = $ExpectedPromotion
    }
}

$StagingPath = Join-Path $SessionPath (".evaluators-staging-" + [System.Guid]::NewGuid().ToString("N"))
$Promoted = $false
$ReportValidated = $false
$CheckpointWritten = $false
$OriginalReportMarkdown = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $SessionPath "report.md")
try {
    New-Item -ItemType Directory -Path $StagingPath | Out-Null
    foreach ($Mode in $SemanticModes) {
        $Record = $Verified[$Mode]
        $StagedPath = Join-Path $StagingPath "$Mode.json"
        Copy-Item -LiteralPath $Record.source -Destination $StagedPath
        $StagedHash = (Get-FileHash -LiteralPath $StagedPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if (-not $StagedHash.Equals(([string]$Record.sha256).ToLowerInvariant(), [System.StringComparison]::Ordinal)) {
            throw "Staged evaluator output hash mismatch: $Mode"
        }
    }

    foreach ($Mode in $SemanticModes) {
        $StagedPath = Join-Path $StagingPath "$Mode.json"
        $ValidationOutput = & $VenvPython $EvaluatorValidator $StagedPath --expected $Mode
        $ValidationExit = $LASTEXITCODE
        $ValidationOutput | ForEach-Object { Write-Host $_ }
        if ($ValidationExit -ne 0) {
            throw "Invalid staged evaluator output: $Mode"
        }
    }

    [System.IO.Directory]::Move($StagingPath, $EvaluatorsPath)
    $Promoted = $true

    $AssemblyOutput = & $VenvPython $ReportAssembler $SessionPath
    $AssemblyExit = $LASTEXITCODE
    $AssemblyOutput | ForEach-Object { Write-Host $_ }
    if ($AssemblyExit -ne 0) {
        throw "Could not assemble the clean Resume QA report."
    }

    $ReportJsonPath = Join-Path $SessionPath "report.json"
    $ReportValidationOutput = & $VenvPython $ReportValidator $ReportJsonPath
    $ReportValidationExit = $LASTEXITCODE
    $ReportValidationOutput | ForEach-Object { Write-Host $_ }
    if ($ReportValidationExit -ne 0) {
        throw "Combined Resume QA report validation failed."
    }
    $ReportValidated = $true

    $Receipts = [ordered]@{}
    foreach ($Mode in $SemanticModes) {
        $Destination = Join-Path $EvaluatorsPath "$Mode.json"
        $Receipts[$Mode] = [ordered]@{
            path = "evaluators/$Mode.json"
            sha256 = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    $Manifest.sandbox.promotion_receipts = $Receipts
    $Manifest.sandbox.status = "promoted-and-validated"
    $Manifest.sandbox | Add-Member -NotePropertyName finalized_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString("o")) -Force
    Write-ManifestAtomically -Value $Manifest -Path $ManifestPath
    $CheckpointWritten = $true

    if ($SemanticModes.Count -gt 0) {
        foreach ($Mode in $SemanticModes) {
            $Workspace = Get-NamedPropertyValue -Object $Manifest.sandbox.workspaces -Name $Mode
            if (-not (Test-PathContainedBy -Child ([string]$Workspace.path) -Parent $SandboxRootPath)) {
                throw "Refusing cleanup because a workspace escaped the sandbox root: $Mode"
            }
        }
        $SandboxParent = Split-Path -Parent $SandboxRootPath
        Remove-CheckedDirectory -Path $SandboxRootPath -RequiredParent $SandboxParent
    }

    $Manifest.sandbox.status = "completed"
    $Manifest.sandbox | Add-Member -NotePropertyName removed_at -NotePropertyValue ((Get-Date).ToUniversalTime().ToString("o")) -Force
    Write-ManifestAtomically -Value $Manifest -Path $ManifestPath
}
catch {
    if (Test-Path -LiteralPath $StagingPath -PathType Container) {
        Remove-CheckedDirectory -Path $StagingPath -RequiredParent $SessionPath
    }
    if ($Promoted -and -not $CheckpointWritten -and (Test-Path -LiteralPath $EvaluatorsPath -PathType Container)) {
        $ExpectedNames = @($SemanticModes | ForEach-Object { "$_.json" } | Sort-Object)
        $ActualNames = @(Get-ChildItem -LiteralPath $EvaluatorsPath -File -Force | Select-Object -ExpandProperty Name | Sort-Object)
        $UnexpectedEntries = @(Get-ChildItem -LiteralPath $EvaluatorsPath -Directory -Force)
        if ($UnexpectedEntries.Count -eq 0 -and (Compare-Object -ReferenceObject $ExpectedNames -DifferenceObject $ActualNames).Count -eq 0) {
            Remove-CheckedDirectory -Path $EvaluatorsPath -RequiredParent $SessionPath
        }
        $ReportJsonPath = Join-Path $SessionPath "report.json"
        if (Test-Path -LiteralPath $ReportJsonPath -PathType Leaf) {
            Remove-Item -LiteralPath $ReportJsonPath -Force
        }
        $OriginalReportMarkdown | Set-Content -LiteralPath (Join-Path $SessionPath "report.md") -Encoding utf8
    }
    throw
}

Write-Output $SessionPath
