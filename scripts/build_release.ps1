$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$dist = Join-Path $root 'dist'
if (-not (Test-Path $dist)) {
    New-Item -ItemType Directory -Path $dist | Out-Null
}

$out = Join-Path $dist 'walap_upload-v0.1.0.mcdr'
if (Test-Path $out) {
    Remove-Item $out
}
$zipOut = Join-Path $dist 'walap_upload-v0.1.0.zip'
if (Test-Path $zipOut) {
    Remove-Item $zipOut
}
$stage = Join-Path $dist 'walap_upload-v0.1.0-stage'
if (Test-Path $stage) {
    Remove-Item -Recurse -Force $stage
}
New-Item -ItemType Directory -Path $stage | Out-Null

Copy-Item 'mcdreforged.plugin.json', 'requirements.txt' -Destination $stage
Copy-Item 'walap_upload' -Destination $stage -Recurse
Get-ChildItem $stage -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
Get-ChildItem $stage -Recurse -File -Include '*.pyc', '*.pyo' | Remove-Item -Force

Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zipOut
Move-Item $zipOut $out

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($out)
try {
    Write-Output "Built: $out"
    Write-Output "Size: $((Get-Item $out).Length) bytes"
    Write-Output 'Entries:'
    $zip.Entries | ForEach-Object { Write-Output $_.FullName }
}
finally {
    $zip.Dispose()
}

Remove-Item -Recurse -Force $stage