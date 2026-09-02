$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$package = Join-Path $root 'dist/walap_upload-v0.1.0.mcdr'
if (-not (Test-Path $package)) {
    throw "Release package not found: $package"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($package)
try {
    Write-Output "Package: $package"
    Write-Output "Size: $((Get-Item $package).Length) bytes"
    Write-Output 'Suspicious entries:'
    $badEntries = $zip.Entries | Where-Object { $_.FullName -match '__pycache__|\.pyc|\.pyo|^tests/' }
    if ($badEntries) {
        $badEntries | ForEach-Object { Write-Output $_.FullName }
        throw 'Release package contains test/cache entries'
    }
    Write-Output 'none'
    Write-Output 'Entries:'
    $zip.Entries | ForEach-Object { Write-Output $_.FullName }
}
finally {
    $zip.Dispose()
}