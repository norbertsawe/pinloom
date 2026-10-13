param([string]$PythonExe = '')
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (-not $PythonExe) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $projectRoot '.venv')
    } else {
        & python -m venv (Join-Path $projectRoot '.venv')
    }
} else {
    & $PythonExe -m venv (Join-Path $projectRoot '.venv')
}
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ with venv is required.' }
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $venvPython -m pip install "$projectRoot[yaml]"
if ($LASTEXITCODE -ne 0) { throw 'Installation failed.' }
$command = Join-Path $projectRoot '.venv\Scripts\pinout.exe'
& $command --version
if ($LASTEXITCODE -ne 0) { throw 'Installation verification failed.' }
Write-Host "Installed: $command"
Write-Host "PowerShell: & '$command' pico -d"
Write-Host "Command Prompt: `"$command`" pico -d"
Write-Host "Add '$projectRoot\.venv\Scripts' to your user PATH to run pinout anywhere."
