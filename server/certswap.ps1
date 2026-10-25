# Windows version of certswap.sh: add the host's CA to every PS3 root CA file in RPCS3 (original + ours), or restore the originals.
#   powershell -ExecutionPolicy Bypass -File certswap.ps1 install C:\RPCS3 C:\Users\you\Downloads\ca.pem
#   powershell -ExecutionPolicy Bypass -File certswap.ps1 restore C:\RPCS3
# The first path is your RPCS3 folder (the one with rpcs3.exe). The originals stay in each file, so other games keep working.
param(
    [Parameter(Mandatory)][ValidateSet('install', 'restore')][string]$Action,
    [Parameter(Mandatory)][string]$Rpcs3Dir,
    [string]$CaFile
)
$ErrorActionPreference = 'Stop'
$cert = Join-Path $Rpcs3Dir 'dev_flash\data\cert'
$backup = Join-Path $Rpcs3Dir 'dev_flash\data\cert.orig'
if (-not (Test-Path $cert)) { throw "No $cert - install the PS3 firmware in RPCS3 first, or check the RPCS3 folder." }
if ($Action -eq 'install') {
    if (-not $CaFile -or -not (Test-Path $CaFile)) { throw 'Give the path to the host''s ca.pem as the third argument.' }
    if (-not (Test-Path $backup)) { Copy-Item $cert $backup -Recurse }
    $files = Get-ChildItem $backup -Filter *.cer
    $ca = [IO.File]::ReadAllBytes((Resolve-Path $CaFile).Path)
    # built from the backup each time, so re-running with another host's CA replaces the old one
    foreach ($f in $files) { [IO.File]::WriteAllBytes((Join-Path $cert $f.Name), [byte[]]([IO.File]::ReadAllBytes($f.FullName) + $ca)) }
    Write-Host "Added $CaFile to $($files.Count) cert files (untouched originals in $backup)"
} else {
    if (-not (Test-Path $backup)) { throw "No backup at $backup" }
    Copy-Item (Join-Path $backup '*') $cert -Force
    Write-Host 'Restored original certs'
}
