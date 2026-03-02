param(
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Content
)

$dir = Split-Path -Parent $Path
if ($dir -and !(Test-Path $dir)) {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Always write UTF-8 (no BOM) to avoid mojibake across tools.
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Path, $Content, $utf8)

Write-Output $Path
