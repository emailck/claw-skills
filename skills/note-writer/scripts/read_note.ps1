param(
  [Parameter(Mandatory=$true, Position=0)][string]$Path,
  [string]$Vault = 'D:\\Notes',
  [int]$MaxChars = 12000
)

# Resolve to vault if a relative path is provided.
if (-not ([System.IO.Path]::IsPathRooted($Path))) {
  $Path = Join-Path -Path $Vault -ChildPath $Path
}

if (-not (Test-Path -LiteralPath $Path)) {
  throw "Not found: $Path"
}

# Read as UTF-8 (no BOM) by default; fall back to UTF-8 with BOM.
try {
  $text = Get-Content -LiteralPath $Path -Raw -Encoding utf8
} catch {
  $text = Get-Content -LiteralPath $Path -Raw -Encoding utf8BOM
}

if ($null -eq $text) { $text = "" }

if ($text.Length -gt $MaxChars) {
  $text = $text.Substring(0, $MaxChars) + "\n\n…(truncated)"
}

# Emit JSON so the caller can render consistently.
[pscustomobject]@{
  Path = $Path
  Length = $text.Length
  Content = $text
} | ConvertTo-Json -Depth 3
