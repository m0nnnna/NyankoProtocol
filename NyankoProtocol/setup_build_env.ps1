# Setup self-contained Python 3.12 + pip for building. No system Python required.
# Embeddable package does not include venv; we use tools/python312 directly.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ToolsDir = Join-Path $ScriptDir "tools"
$PyDir = Join-Path $ToolsDir "python312"
$PyVersion = "3.12.8"
$EmbedZip = "python-$PyVersion-embed-amd64.zip"
$EmbedUrl = "https://www.python.org/ftp/python/$PyVersion/$EmbedZip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

# Already set up (pip in embed = ready to use)
$PipExe = Join-Path $PyDir "Scripts\pip.exe"
if (Test-Path $PipExe) {
    Write-Host "tools\python312 already set up. OK."
    exit 0
}

Write-Host "Setting up self-contained Python $PyVersion for build..."
New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

# Download embed zip
$ZipPath = Join-Path $ToolsDir $EmbedZip
if (-not (Test-Path $ZipPath)) {
    Write-Host "Downloading $EmbedZip..."
    Invoke-WebRequest -Uri $EmbedUrl -OutFile $ZipPath -UseBasicParsing
}

# Extract (zip may have root folder or files at top level)
if (-not (Test-Path (Join-Path $PyDir "python.exe"))) {
    Write-Host "Extracting Python..."
    $ExtractTo = Join-Path $ToolsDir "embed_extract"
    if (Test-Path $ExtractTo) { Remove-Item -Recurse -Force $ExtractTo }
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractTo -Force
    $PyExeFound = Get-ChildItem -Path $ExtractTo -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    $SrcDir = if ($PyExeFound) { $PyExeFound.Directory.FullName } else { $ExtractTo }
    New-Item -ItemType Directory -Force -Path $PyDir | Out-Null
    Copy-Item -Path "$SrcDir\*" -Destination $PyDir -Recurse -Force
    Remove-Item -Recurse -Force $ExtractTo
}

# Enable site-packages: uncomment "import site" in python312._pth
$PthFile = Join-Path $PyDir "python312._pth"
if (Test-Path $PthFile) {
    $pth = Get-Content $PthFile -Raw
    if ($pth -match "#\s*import site") {
        $pth = $pth -replace "#\s*import site", "import site"
        Set-Content $PthFile $pth -NoNewline
    }
}

# Ensure Lib\site-packages exists
$SitePackages = Join-Path $PyDir "Lib\site-packages"
New-Item -ItemType Directory -Force -Path $SitePackages | Out-Null

# Install pip
$GetPipPath = Join-Path $ToolsDir "get-pip.py"
if (-not (Test-Path $GetPipPath)) {
    Write-Host "Downloading get-pip.py..."
    Invoke-WebRequest -Uri $GetPipUrl -OutFile $GetPipPath -UseBasicParsing
}
$PyExe = Join-Path $PyDir "python.exe"
Write-Host "Installing pip..."
& $PyExe $GetPipPath --quiet 2>$null

Write-Host "Done. tools\python312 is ready (no venv; embed has no venv module)."
exit 0
