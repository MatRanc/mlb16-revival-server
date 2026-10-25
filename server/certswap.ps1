# Windows version of certswap.sh: put the host's CA in place of every PS3 root CA in RPCS3, or restore the originals.
#   powershell -ExecutionPolicy Bypass -File certswap.ps1 install C:\RPCS3 C:\Users\you\Downloads\ca.pem
#   powershell -ExecutionPolicy Bypass -File certswap.ps1 restore C:\RPCS3
# The first path is your RPCS3 folder (the one with rpcs3.exe). Restore when you're done; other games need the originals.
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
    foreach ($f in $files) { Copy-Item $CaFile (Join-Path $cert $f.Name) -Force }
    Write-Host "Installed $CaFile over $($files.Count) cert files (originals in $backup)"
} else {
    if (-not (Test-Path $backup)) { throw "No backup at $backup" }
    Copy-Item (Join-Path $backup '*') $cert -Force
    Write-Host 'Restored original certs'
}
