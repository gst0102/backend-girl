<#
.SYNOPSIS
  Fetch kdocs.cn document, dismiss login dialog, extract entries, save as JSON
.DESCRIPTION
  Uses opencli browser to navigate to a kdocs.cn smart document,
  handles login popups, waits for the COLLABX editor, extracts all
  entries with links, and saves structured JSON.
.PARAMETER Url
  kdocs.cn document URL (default: https://www.kdocs.cn/l/co72a28MWkmI)
.PARAMETER OutputFile
  Output JSON path (default: kdocs_output.json)
.EXAMPLE
  .\fetch_kdocs.ps1
  .\fetch_kdocs.ps1 -Url "https://www.kdocs.cn/l/xxxxx" -OutputFile "result.json"
#>

param(
    [string]$Url = "https://www.kdocs.cn/l/co72a28MWkmI",
    [string]$OutputFile = "kdocs_output.json"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  kdocs.cn Document Fetcher" -ForegroundColor Cyan
Write-Host "  URL : $Url" -ForegroundColor Gray
Write-Host "  OUT : $OutputFile" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan

# ============================================================
# STEP 0: Environment check
# ============================================================
Write-Host "`n[0/9] Environment check" -ForegroundColor Cyan

$extractJsPath = Join-Path $ScriptDir "kdocs_extract.js"
$dismissJsPath = Join-Path $ScriptDir "kdocs_dismiss_login.js"

if (-not (Test-Path $extractJsPath)) {
    Write-Error "Missing: $extractJsPath"; exit 1
}
if (-not (Test-Path $dismissJsPath)) {
    Write-Error "Missing: $dismissJsPath"; exit 1
}

$extractJs = Get-Content -Path $extractJsPath -Raw
$dismissJs = Get-Content -Path $dismissJsPath -Raw

Write-Host "  extract.js : $($extractJs.Length) chars" -ForegroundColor Gray
Write-Host "  dismiss.js : $($dismissJs.Length) chars" -ForegroundColor Gray

# Find opencli
$opencliCmd = $null
$opencliMain = Join-Path $env:APPDATA "npm\node_modules\@jackwener\opencli\dist\src\main.js"

# Try opencli direct (if in PATH)
if ((Get-Command "opencli" -ErrorAction SilentlyContinue) -and (Test-Path $opencliMain)) {
    $opencliCmd = "opencli"
    Write-Host "  opencli   : found in PATH" -ForegroundColor Gray
} else {
    # Try multiple node paths
    $nodeCandidates = @(
        Join-Path $env:APPDATA "npm\node.exe"
        "node.exe"
        "node"
    )
    # Also search trae sdks
    $traeNode = Get-ChildItem "$env:USERPROFILE\.trae-cn\sdks" -Filter "node.exe" -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    if ($traeNode) { $nodeCandidates = @($traeNode) + $nodeCandidates }

    $nodeExe = $null
    foreach ($cand in $nodeCandidates) {
        if (Test-Path $cand) { $nodeExe = $cand; break }
        # Try as command
        if ((Get-Command $cand -ErrorAction SilentlyContinue) -and ($cand -eq "node" -or $cand -eq "node.exe")) {
            $nodeExe = $cand; break
        }
    }

    if (-not $nodeExe) {
        Write-Error "Cannot find node.exe. Please install Node.js or ensure 'opencli' is in PATH."; exit 1
    }
    if (-not (Test-Path $opencliMain)) {
        Write-Error "Cannot find opencli at $opencliMain. Please run: npm i -g @jackwener/opencli"; exit 1
    }
    if ($nodeExe -eq "node" -or $nodeExe -eq "node.exe") {
        $opencliCmd = "$nodeExe `"$opencliMain`""
    } else {
        $opencliCmd = "`"$nodeExe`" `"$opencliMain`""
    }
    Write-Host "  opencli   : $nodeExe" -ForegroundColor Gray
}

function Invoke-OpenCLI {
    param([string[]]$Args)
    $cmd = "$opencliCmd $($Args -join ' ')"
    Write-Host "  [CMD] $cmd" -ForegroundColor DarkGray
    $output = Invoke-Expression $cmd 2>&1
    return @{ ExitCode = $LASTEXITCODE; Output = $output }
}

# ============================================================
# STEP 1: Doctor check
# ============================================================
Write-Host "`n[1/9] Bridge check (opencli doctor)" -ForegroundColor Cyan
$res = Invoke-OpenCLI -Args "doctor"
Write-Host $res.Output
if ($res.ExitCode -ne 0) {
    Write-Error "opencli doctor failed. Start Chrome + ensure extension installed."; exit 1
}
Write-Host "  OK" -ForegroundColor Green

# ============================================================
# STEP 2: Open kdocs URL
# ============================================================
Write-Host "`n[2/9] Open kdocs URL" -ForegroundColor Cyan
$SESSION = "kdocs_fetch"
$res = Invoke-OpenCLI -Args "browser", $SESSION, "open", $Url
Write-Host $res.Output
if ($res.ExitCode -ne 0) {
    Write-Error "Failed to open URL"; exit 1
}
Write-Host "  OK" -ForegroundColor Green

# ============================================================
# STEP 3: Wait for canvas (editor render)
# ============================================================
Write-Host "`n[3/9] Wait for canvas (20s timeout)" -ForegroundColor Cyan
$res = Invoke-OpenCLI -Args "browser", $SESSION, "wait", "selector", "canvas", "--timeout", "20000"
if ($res.ExitCode -ne 0) {
    Write-Warning "Canvas not found, continuing anyway..."
} else {
    Write-Host "  OK - canvas rendered" -ForegroundColor Green
}

# ============================================================
# STEP 4: Initial settle
# ============================================================
Write-Host "`n[4/9] Initial settle (3s)" -ForegroundColor Cyan
Start-Sleep -Seconds 3
Write-Host "  OK" -ForegroundColor Green

# ============================================================
# STEP 5: Dismiss login dialog
# ============================================================
Write-Host "`n[5/9] Detect & dismiss login dialog" -ForegroundColor Cyan
try {
    $res = Invoke-OpenCLI -Args "browser", $SESSION, "eval", $dismissJs
    Write-Host "  Result: $($res.Output)" -ForegroundColor Gray
    Write-Host "  OK" -ForegroundColor Green
} catch {
    Write-Host "  Not found or already closed (safe to ignore)" -ForegroundColor DarkYellow
}

Start-Sleep -Seconds 2

# ============================================================
# STEP 6: Wait for COLLABX editor
# ============================================================
Write-Host "`n[6/9] Wait for COLLABX editor (max 40s)" -ForegroundColor Cyan

$maxRetry = 20
$ready = $false
for ($i = 1; $i -le $maxRetry; $i++) {
    $checkJs = "(function(){ if (typeof window.COLLABX !== 'undefined' && window.COLLABX.editor) return 'ready'; return 'no'; })()"
    $res = Invoke-OpenCLI -Args "browser", $SESSION, "eval", $checkJs
    if ($res.Output -match "ready") {
        Write-Host "  OK - COLLABX ready (attempt $i)" -ForegroundColor Green
        $ready = $true
        break
    }

    if ($i -eq 5) {
        Write-Host "  Triggering scroll to activate lazy-load..." -ForegroundColor DarkYellow
        Invoke-OpenCLI -Args "browser", $SESSION, "scroll", "down", "--amount", "1000" | Out-Null
        Start-Sleep -Seconds 1
        Invoke-OpenCLI -Args "browser", $SESSION, "scroll", "up", "--amount", "500" | Out-Null
    }

    Write-Host "  ." -NoNewline
    Start-Sleep -Seconds 2
}
Write-Host ""

if (-not $ready) {
    Write-Error @"
COLLABX editor failed to load after ${maxRetry} attempts.
Please verify:
  1. You are logged into kdocs.cn in Chrome
  2. The document URL is valid and accessible
  3. Chrome is running with OpenCLI extension installed
"@
    exit 1
}

# ============================================================
# STEP 7: Full render wait
# ============================================================
Write-Host "`n[7/9] Wait for full content render (4s)" -ForegroundColor Cyan
Start-Sleep -Seconds 4
Write-Host "  OK" -ForegroundColor Green

# ============================================================
# STEP 8: Extract document data
# ============================================================
Write-Host "`n[8/9] Extract document data" -ForegroundColor Cyan
$res = Invoke-OpenCLI -Args "browser", $SESSION, "eval", $extractJs
Write-Host "  Extracted $($res.Output.Length) chars" -ForegroundColor Green

# ============================================================
# STEP 9: Parse and save JSON
# ============================================================
Write-Host "`n[9/9] Parse and save JSON" -ForegroundColor Cyan

try {
    $rawOutput = "$($res.Output)" -replace "[\r\n]+", " "
    $data = $rawOutput | ConvertFrom-Json -ErrorAction Stop

    if ($data.error) {
        throw "Extract script error: $($data.error)"
    }

    $data | ConvertTo-Json -Depth 6 | Out-File -FilePath $OutputFile -Encoding UTF8

    Write-Host "  Output : $OutputFile" -ForegroundColor Green
    Write-Host "  Entries: $($data.total_entries)" -ForegroundColor Green
    Write-Host "  Updated: $($data.meta.update_date) $($data.meta.update_time)" -ForegroundColor Green
    Write-Host "  Fetched: $($data.meta.fetch_time)" -ForegroundColor Green

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan

    foreach ($entry in $data.entries) {
        Write-Host "  [$($entry.index)] $($entry.title) | $($entry.quality) | $($entry.episode) | $($entry.status)" -ForegroundColor White
        if ($entry.baidu_url) { Write-Host "      baidu: $($entry.baidu_url) (pw: $($entry.baidu_password))" -ForegroundColor Gray }
        if ($entry.quark_url) { Write-Host "      quark: $($entry.quark_url)" -ForegroundColor Gray }
        if ($entry.k4_note)  { Write-Host "      4K: $($entry.k4_note)" -ForegroundColor Gray }
    }

    return $data
} catch {
    Write-Warning "JSON parse failed. Saving raw output to ${OutputFile}.raw.txt"
    $res.Output | Out-File -FilePath "${OutputFile}.raw.txt" -Encoding UTF8
    Write-Error "Parse error: $_"
    exit 1
}