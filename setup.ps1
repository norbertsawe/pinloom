param(
    [string]$PythonExe = '',
    [switch]$NoPath,
    [switch]$NoYaml,
    [string]$InstallDir = '',
    [string]$BinDir = ''
)
$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'tools\install.py'
$installArgs = @()
if ($NoPath) { $installArgs += '--no-path' }
if ($NoYaml) { $installArgs += '--no-yaml' }
if ($InstallDir) { $installArgs += @('--install-dir', $InstallDir) }
if ($BinDir) { $installArgs += @('--bin-dir', $BinDir) }
if ($PythonExe) {
    & $PythonExe $installer @installArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $installer @installArgs
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $installer @installArgs
} else {
    throw 'Python 3.10+ is required. Install Python from python.org, then rerun setup.cmd.'
}
if ($LASTEXITCODE -ne 0) { throw 'Pinloom installation failed; see the error above.' }
if (-not $NoPath) {
    $base = $env:LOCALAPPDATA
    if (-not $base) { $base = Join-Path $HOME 'AppData\Local' }
    $commandDir = Join-Path $base 'Pinloom\bin'
    if ($BinDir) { $commandDir = (Resolve-Path $BinDir).Path }
    if (($env:Path -split ';') -notcontains $commandDir) { $env:Path = "$commandDir;$env:Path" }
}
Write-Host 'Ready. Run pinloom --version, or open a new terminal if setup was launched in a child process.'
