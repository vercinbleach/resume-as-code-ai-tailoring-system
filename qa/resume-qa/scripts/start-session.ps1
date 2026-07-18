[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Resume,

    [ValidateSet("pdf", "technical", "leadership", "job-match", "callback", "all")]
    [string[]]$Modes = @("technical", "leadership"),

    [string]$JobDescription,
    [string]$JobIntake,
    [string]$SessionId = (Get-Date -Format "yyyyMMdd-HHmmss"),
    [string]$SessionsRoot,
    [string]$SandboxRoot
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$QaRoot = Split-Path -Parent $SkillRoot
$ProjectRoot = Split-Path -Parent $QaRoot
$VenvPython = Join-Path $QaRoot ".venv\Scripts\python.exe"
$PdfChecksScript = Join-Path $PSScriptRoot "pdf_checks.py"
$ParsedProfileScript = Join-Path $PSScriptRoot "parsed_profile.py"
$TextSearchScript = Join-Path $PSScriptRoot "ashby_text_search.py"
$ApplicationReadinessScript = Join-Path $PSScriptRoot "application_readiness.py"
$JobIntakeValidator = Join-Path $PSScriptRoot "validate_job_intake.py"
$JobDescriptionRenderer = Join-Path $PSScriptRoot "render_job_description.py"
$TemplatePath = Join-Path $SkillRoot "assets\session-report.md"
$SandboxWorkspaceScript = Join-Path $ProjectRoot "scripts\sandbox_workspace.py"

$EvaluatorSpecs = [ordered]@{
    "technical" = [ordered]@{
        skill = Join-Path $ProjectRoot ".agents\skills\resume-technical-clean"
        skill_relative = ".agents/skills/resume-technical-clean/SKILL.md"
        job_description = $false
    }
    "leadership" = [ordered]@{
        skill = Join-Path $ProjectRoot ".agents\skills\resume-leadership-clean"
        skill_relative = ".agents/skills/resume-leadership-clean/SKILL.md"
        job_description = $false
    }
    "job-match" = [ordered]@{
        skill = Join-Path $ProjectRoot ".agents\skills\resume-job-match-clean"
        skill_relative = ".agents/skills/resume-job-match-clean/SKILL.md"
        job_description = $true
    }
    "callback" = [ordered]@{
        skill = Join-Path $ProjectRoot ".agents\skills\resume-callback-clean"
        skill_relative = ".agents/skills/resume-callback-clean/SKILL.md"
        job_description = $true
    }
}

function Resolve-ProjectFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )

    $Candidate = $PathValue
    if (-not [System.IO.Path]::IsPathRooted($Candidate)) {
        $Candidate = Join-Path $ProjectRoot $Candidate
    }
    if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
        throw "File not found: $PathValue"
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

function Assert-SafeSandboxRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$RepositoryRoot,
        [Parameter(Mandatory = $true)]
        [string]$SessionPath
    )

    $FullPath = [System.IO.Path]::GetFullPath($Path).TrimEnd([char[]]@(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ))
    $VolumeRoot = [System.IO.Path]::GetPathRoot($FullPath).TrimEnd([char[]]@(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ))
    if ($FullPath.Equals($VolumeRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "SandboxRoot cannot be a volume root: $FullPath"
    }

    foreach ($Protected in @($RepositoryRoot, $SessionPath)) {
        $ProtectedPath = [System.IO.Path]::GetFullPath($Protected).TrimEnd([char[]]@(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        ))
        if ($FullPath.Equals($ProtectedPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "SandboxRoot cannot equal a protected path: $ProtectedPath"
        }
        if (Test-PathContainedBy -Child $ProtectedPath -Parent $FullPath) {
            throw "SandboxRoot cannot contain a protected path: $ProtectedPath"
        }
    }
}

function Remove-PartialSetupDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$RequiredParent
    )

    $FullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not (Test-PathContainedBy -Child $FullPath -Parent $RequiredParent)) {
        throw "Refusing to clean a partial directory outside its declared parent: $FullPath"
    }
    if (-not (Test-Path -LiteralPath $FullPath)) {
        return
    }
    $Item = Get-Item -LiteralPath $FullPath -Force
    if (-not $Item.PSIsContainer -or ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing to clean a non-directory or reparse point: $FullPath"
    }
    Get-ChildItem -LiteralPath $FullPath -Recurse -Force | ForEach-Object {
        if ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
            $_.Attributes = $_.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
        }
    }
    if ($Item.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
        $Item.Attributes = $Item.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
    }
    Remove-Item -LiteralPath $FullPath -Recurse -Force
}

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "QA environment not found. Run .\qa\resume-qa\scripts\setup.ps1 first."
}
if (-not (Test-Path -LiteralPath $SandboxWorkspaceScript -PathType Leaf)) {
    throw "Sandbox helper not found: $SandboxWorkspaceScript"
}

$ResumePath = Resolve-ProjectFile -PathValue $Resume
if ($JobDescription -and $JobIntake) {
    throw "Pass either -JobDescription or -JobIntake, not both."
}

$JobIntakePath = if ($JobIntake) { Resolve-ProjectFile -PathValue $JobIntake } else { $null }
$JobPath = $null
if ($JobIntakePath) {
    $JobValidationOutput = & $VenvPython $JobIntakeValidator $JobIntakePath
    $JobValidationExit = $LASTEXITCODE
    $JobValidationOutput | ForEach-Object { Write-Host $_ }
    if ($JobValidationExit -ne 0) {
        throw "Job intake validation failed."
    }
}
elseif ($JobDescription) {
    $JobPath = Resolve-ProjectFile -PathValue $JobDescription
}
$HasJobEvidence = [bool]($JobIntakePath -or $JobPath)

$RequestedModes = @($Modes | ForEach-Object { $_.ToLowerInvariant() })
if ($RequestedModes -contains "all") {
    $RequestedModes = @("technical", "leadership")
    if ($HasJobEvidence) {
        $RequestedModes += "job-match"
        $RequestedModes += "callback"
    }
}
if (($RequestedModes -contains "job-match") -and -not $HasJobEvidence) {
    throw "job-match mode requires -JobDescription."
}
if (($RequestedModes -contains "callback") -and -not $HasJobEvidence) {
    throw "callback mode requires -JobDescription."
}
$SelectedModes = @("pdf") + @($RequestedModes | Where-Object { $_ -ne "pdf" })
$SelectedModes = @($SelectedModes | Select-Object -Unique)

if ($SessionId -notmatch "^[A-Za-z0-9][A-Za-z0-9._-]*$") {
    throw "SessionId may contain only letters, numbers, dots, underscores, and hyphens."
}

if (-not $SessionsRoot) {
    $SessionsRootPath = Join-Path $QaRoot "sessions"
}
elseif ([System.IO.Path]::IsPathRooted($SessionsRoot)) {
    $SessionsRootPath = [System.IO.Path]::GetFullPath($SessionsRoot)
}
else {
    $SessionsRootPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $SessionsRoot))
}

if (-not $SandboxRoot) {
    $SandboxRootPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot ".sandbox\qa\$SessionId"))
}
elseif ([System.IO.Path]::IsPathRooted($SandboxRoot)) {
    $SandboxRootPath = [System.IO.Path]::GetFullPath($SandboxRoot)
}
else {
    $SandboxRootPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $SandboxRoot))
}

$SessionPath = Join-Path $SessionsRootPath $SessionId
Assert-SafeSandboxRoot -Path $SandboxRootPath -RepositoryRoot $ProjectRoot -SessionPath $SessionPath
if (Test-Path -LiteralPath $SessionPath) {
    throw "Session already exists: $SessionPath"
}
if (Test-Path -LiteralPath $SandboxRootPath) {
    throw "Sandbox root already exists: $SandboxRootPath"
}

try {
New-Item -ItemType Directory -Path $SessionPath -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $SessionPath "inputs") -Force | Out-Null

$SessionResumePath = Join-Path $SessionPath "inputs\resume.pdf"
Copy-Item -LiteralPath $ResumePath -Destination $SessionResumePath
$SessionJobPath = $null
$SessionJobIntakePath = $null
if ($JobIntakePath) {
    $SessionJobIntakePath = Join-Path $SessionPath "inputs\job-intake.json"
    Copy-Item -LiteralPath $JobIntakePath -Destination $SessionJobIntakePath
    $SessionJobPath = Join-Path $SessionPath "inputs\job-description.md"
    $JobRenderOutput = & $VenvPython $JobDescriptionRenderer --input $SessionJobIntakePath --output $SessionJobPath
    $JobRenderExit = $LASTEXITCODE
    $JobRenderOutput | ForEach-Object { Write-Host $_ }
    if ($JobRenderExit -ne 0) {
        throw "Could not render the normalized job description."
    }
}
elseif ($JobPath) {
    $SessionJobPath = Join-Path $SessionPath "inputs\job-description.md"
    Copy-Item -LiteralPath $JobPath -Destination $SessionJobPath
}

$PdfChecksPath = Join-Path $SessionPath "pdf-checks.json"
$PdfChecksOutput = & $VenvPython $PdfChecksScript --resume $SessionResumePath --output $PdfChecksPath
$PdfChecksExit = $LASTEXITCODE
$PdfChecksOutput | ForEach-Object { Write-Host $_ }
if ($PdfChecksExit -ne 0) {
    throw "Deterministic PDF checks failed."
}

$ParsedProfilePath = Join-Path $SessionPath "parsed-profile.json"
$ParsedProfileOutput = & $VenvPython $ParsedProfileScript --resume $SessionResumePath --output $ParsedProfilePath
$ParsedProfileExit = $LASTEXITCODE
$ParsedProfileOutput | ForEach-Object { Write-Host $_ }
if ($ParsedProfileExit -ne 0) {
    throw "Parsed-profile projection failed."
}

$TextSearchPath = $null
if ($SessionJobPath) {
    $TextSearchPath = Join-Path $SessionPath "ashby-text-search.json"
    if ($SessionJobIntakePath) {
        $TextSearchOutput = & $VenvPython $TextSearchScript --resume $SessionResumePath --job-intake $SessionJobIntakePath --output $TextSearchPath
    }
    else {
        $TextSearchOutput = & $VenvPython $TextSearchScript --resume $SessionResumePath --job-description $SessionJobPath --output $TextSearchPath
    }
    $TextSearchExit = $LASTEXITCODE
    $TextSearchOutput | ForEach-Object { Write-Host $_ }
    if ($TextSearchExit -ne 0) {
        throw "Local Ashby-like text-search checks failed."
    }
}

$ApplicationReadinessPath = $null
if ($SessionJobIntakePath) {
    $ApplicationReadinessPath = Join-Path $SessionPath "application-readiness.json"
    $ReadinessOutput = & $VenvPython $ApplicationReadinessScript --job-intake $SessionJobIntakePath --parsed-profile $ParsedProfilePath --output $ApplicationReadinessPath
    $ReadinessExit = $LASTEXITCODE
    $ReadinessOutput | ForEach-Object { Write-Host $_ }
    if ($ReadinessExit -ne 0) {
        throw "Application-readiness analysis failed."
    }
}

$GeneratedAt = (Get-Date).ToUniversalTime().ToString("o")
$ResumeRelative = "inputs/resume.pdf"
$JobRelative = if ($SessionJobPath) { "inputs/job-description.md" } else { $null }
$JobIntakeRelative = if ($SessionJobIntakePath) { "inputs/job-intake.json" } else { $null }
[object[]]$JobMatchEvidence = @()
if ($JobRelative) {
    $JobMatchEvidence = @("inputs/job-description.md")
}
[object[]]$CoordinatorOnlyInputs = @()
if ($JobIntakeRelative) {
    $CoordinatorOnlyInputs = @("inputs/job-intake.json", "browser state")
}
$EvaluatorSkills = [ordered]@{}
$SandboxRecords = [ordered]@{}
$TaskPromptSections = @(
    "# Clean evaluator task prompts",
    "",
    "Launch every selected evaluator concurrently in a fresh top-level Codex task. Do not use subagents, forks, or reused tasks. Do not inspect any result until every task has completed."
)

$SemanticModes = @($SelectedModes | Where-Object { $_ -ne "pdf" })
if ($SemanticModes.Count -gt 0) {
    New-Item -ItemType Directory -Path $SandboxRootPath -Force | Out-Null
}

foreach ($Mode in $SemanticModes) {
    $Spec = $EvaluatorSpecs[$Mode]
    if (-not $Spec) {
        throw "No sandbox specification exists for evaluator: $Mode"
    }
    $SkillSource = [System.IO.Path]::GetFullPath($Spec.skill)
    if (-not (Test-Path -LiteralPath (Join-Path $SkillSource "SKILL.md") -PathType Leaf)) {
        throw "Clean evaluator skill not found: $SkillSource"
    }

    $EvaluatorSkills[$Mode] = $Spec.skill_relative
    $EvaluatorSandbox = Join-Path $SandboxRootPath $Mode
    $PromotionTarget = Join-Path $SessionPath "evaluators\$Mode.json"
    $CreateArguments = @(
        $SandboxWorkspaceScript,
        "create",
        "--sandbox", $EvaluatorSandbox,
        "--pipeline", "resume-qa",
        "--session-id", $SessionId,
        "--task-id", $Mode,
        "--skill", $SkillSource,
        "--input", "$SessionResumePath::resume.pdf",
        "--output-name", "result.json",
        "--promote-to", $PromotionTarget,
        "--network", "deny"
    )
    if ($Spec.job_description) {
        $CreateArguments += @("--input", "$SessionJobPath::job-description.md")
    }

    $CreateOutput = & $VenvPython @CreateArguments
    $CreateExit = $LASTEXITCODE
    if ($CreateExit -ne 0) {
        $CreateOutput | ForEach-Object { Write-Host $_ }
        throw "Could not create the $Mode evaluator sandbox."
    }
    try {
        $Created = ($CreateOutput -join "`n") | ConvertFrom-Json
    }
    catch {
        throw "Sandbox helper returned invalid JSON for evaluator $Mode."
    }

    [object[]]$AllowedInputs = @("inputs/resume.pdf")
    if ($Spec.job_description) {
        $AllowedInputs += "inputs/job-description.md"
    }
    $SandboxRecords[$Mode] = [ordered]@{
        path = $Created.sandbox
        manifest = $Created.manifest
        manifest_sha256 = $Created.manifest_sha256
        allowed_inputs = $AllowedInputs
        output = (Join-Path $Created.sandbox "outbox\result.json")
        promote_to = "evaluators/$Mode.json"
    }

    $SandboxSkillPath = Join-Path $Created.sandbox "skill\SKILL.md"
    $SandboxResumePath = Join-Path $Created.sandbox "inputs\resume.pdf"
    $SandboxJobPath = Join-Path $Created.sandbox "inputs\job-description.md"
    $SandboxOutputPath = Join-Path $Created.sandbox "outbox\result.json"
    $TaskPromptSections += @("", "## $Mode", "", '```text')
    $TaskPromptSections += "Run this evaluator in a fresh top-level Codex task. Do not use a subagent, fork, or reused task."
    $TaskPromptSections += "Read and follow `"$SandboxSkillPath`", including only the rubric and references inside that copied skill folder."
    $TaskPromptSections += "Evaluate only `"$SandboxResumePath`"."
    if ($Spec.job_description) {
        $TaskPromptSections += "Also compare only against `"$SandboxJobPath`"."
    }
    $TaskPromptSections += "Write only `"$SandboxOutputPath`"."
    $TaskPromptSections += "Return only completed and the output path."
    $TaskPromptSections += '```'
}

$TaskPromptsPath = Join-Path $SessionPath "task-prompts.md"
($TaskPromptSections -join "`n") | Set-Content -LiteralPath $TaskPromptsPath -Encoding utf8

$Artifacts = [ordered]@{
    pdf_checks = "pdf-checks.json"
    parsed_profile = "parsed-profile.json"
    human_report = "report.md"
    machine_report = "report.json"
}
if ($TextSearchPath) {
    $Artifacts["ashby_text_search"] = "ashby-text-search.json"
}
if ($ApplicationReadinessPath) {
    $Artifacts["application_readiness"] = "application-readiness.json"
}

$Manifest = [ordered]@{
    session_id = $SessionId
    generated_at = $GeneratedAt
    architecture = "clean-pdf-codex-sandboxes-v7"
    resume = $ResumeRelative
    job_description = $JobRelative
    job_intake = $JobIntakeRelative
    modes = $SelectedModes
    isolation = [ordered]@{
        candidate_evidence = @("inputs/resume.pdf")
        job_specific_additional_evidence = $JobMatchEvidence
        job_match_additional_evidence = $JobMatchEvidence
        callback_additional_evidence = $JobMatchEvidence
        semantic_evaluators = "concurrent new top-level Codex project tasks; no subagents, forks, or task reuse"
        result_flow = "each evaluator writes only sandbox outbox/result.json; finalize-session validates every result before promotion"
        coordinator_only_inputs = $CoordinatorOnlyInputs
        evaluator_forbidden_context = @("resume YAML", "knowledge-base", "previous CVs", "prior reports", "parent conversation", "browser state", "web")
    }
    evaluators = $EvaluatorSkills
    sandbox = [ordered]@{
        root = $SandboxRootPath
        lifecycle = "ephemeral"
        status = $(if ($SemanticModes.Count -gt 0) { "awaiting-evaluators" } else { "ready-to-finalize" })
        workspaces = $SandboxRecords
        promotion_receipts = [ordered]@{}
    }
    artifacts = $Artifacts
}
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $SessionPath "manifest.json") -Encoding utf8

$Report = Get-Content -Raw -LiteralPath $TemplatePath
$Report = $Report.Replace("__SESSION_ID__", $SessionId)
$Report = $Report.Replace("__GENERATED_AT__", $GeneratedAt)
$Report = $Report.Replace("__RESUME__", $ResumeRelative)
$Report = $Report.Replace("__JOB_DESCRIPTION__", $(if ($JobRelative) { "``$JobRelative``" } else { "Not provided" }))
$Report = $Report.Replace("__JOB_INTAKE__", $(if ($JobIntakeRelative) { "``$JobIntakeRelative``" } else { "Not provided" }))
$Report = $Report.Replace("__MODES__", ($SelectedModes -join ", "))
$Report | Set-Content -LiteralPath (Join-Path $SessionPath "report.md") -Encoding utf8

Write-Output $SessionPath
}
catch {
    $Failure = $_
    if (Test-Path -LiteralPath $SandboxRootPath) {
        try {
            Remove-PartialSetupDirectory -Path $SandboxRootPath -RequiredParent (Split-Path -Parent $SandboxRootPath)
        }
        catch {
            Write-Warning "Could not remove the partial sandbox root: $($_.Exception.Message)"
        }
    }
    if (Test-Path -LiteralPath $SessionPath) {
        try {
            Remove-PartialSetupDirectory -Path $SessionPath -RequiredParent $SessionsRootPath
        }
        catch {
            Write-Warning "Could not remove the partial session: $($_.Exception.Message)"
        }
    }
    throw $Failure
}
