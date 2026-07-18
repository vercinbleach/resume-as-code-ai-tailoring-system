[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [string]$Slug,
    [string]$JobsRoot
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$QaRoot = Split-Path -Parent $SkillRoot
$ProjectRoot = Split-Path -Parent $QaRoot

$ParsedUrl = $null
if (-not [System.Uri]::TryCreate($Url, [System.UriKind]::Absolute, [ref]$ParsedUrl)) {
    throw "Url must be an absolute HTTP(S) URL."
}
if ($ParsedUrl.Scheme -notin @("http", "https")) {
    throw "Url must use HTTP or HTTPS."
}

if (-not $JobsRoot) {
    $JobsRootPath = Join-Path $QaRoot "jobs"
}
elseif ([System.IO.Path]::IsPathRooted($JobsRoot)) {
    $JobsRootPath = [System.IO.Path]::GetFullPath($JobsRoot)
}
else {
    $JobsRootPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $JobsRoot))
}

if (-not $Slug) {
    $Segments = @($ParsedUrl.AbsolutePath.Trim("/").Split("/") | Where-Object { $_ })
    $Tail = if ($Segments.Count) { $Segments[-1] } else { "job" }
    $Host = $ParsedUrl.Host -replace "^www\.", ""
    $Slug = "$Host-$Tail"
}
$Slug = ($Slug.ToLowerInvariant() -replace "[^a-z0-9]+", "-").Trim("-")
if (-not $Slug) {
    throw "Could not derive a valid slug. Pass -Slug explicitly."
}

$JobDirectory = Join-Path $JobsRootPath $Slug
if (Test-Path -LiteralPath $JobDirectory) {
    throw "Job intake directory already exists: $JobDirectory"
}
New-Item -ItemType Directory -Path $JobDirectory -Force | Out-Null

$Intake = [ordered]@{
    schema_version = "1.1"
    capture = [ordered]@{
        source_url = $ParsedUrl.AbsoluteUri
        canonical_url = $null
        captured_at = $null
        status = "pending"
        pages_visited = @()
        blockers = @()
        submission_attempted = $false
    }
    job = [ordered]@{
        company = $null
        title = $null
        job_id = $null
        locations = @()
        workplace_type = "unknown"
        employment_type = $null
        compensation = @()
        description = @()
        responsibilities = @()
        requirements = [ordered]@{
            must_have = @()
            preferred = @()
            unclear = @()
        }
        technologies = @()
        languages = @()
        education = @()
        experience = @()
        criteria = @()
    }
    application = [ordered]@{
        apply_url = $null
        host = $null
        status = "not-inspected"
        steps_visible = @()
        fields = @()
        documents = @()
        notices = @()
        blockers = @()
        autofill_from_resume_observed = "unknown"
        submission_attempted = $false
    }
    provenance = [ordered]@{
        observed_only = $true
        hidden_rules_claimed = $false
        notes = @()
    }
}

$OutputPath = Join-Path $JobDirectory "job-intake.json"
$Intake | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
Write-Output $OutputPath
