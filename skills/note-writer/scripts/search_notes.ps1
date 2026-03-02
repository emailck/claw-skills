param(
  [Parameter(Mandatory=$true, Position=0)][string[]]$Keywords,
  [string]$Vault = 'D:\\Notes',
  [int]$Limit = 5
)

$rg = Get-Command rg -ErrorAction SilentlyContinue
if ($rg) {
  $rgExe = $rg.Source
} else {
  $rgExe = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter rg.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
  if (-not $rgExe) {
    throw "ripgrep (rg) not found. Install BurntSushi.ripgrep.MSVC and restart your shell."
  }
}

$patterns = @()
foreach ($k in $Keywords) {
  $kk = $k.Trim()
  if (-not $kk) { continue }
  if ($kk.StartsWith('#')) { $patterns += [Regex]::Escape($kk) }
  else { $patterns += [Regex]::Escape($kk) }
}
if ($patterns.Count -eq 0) { throw "No keywords provided." }

# Prefer matching the keyword line first.
$keywordRegex = '^(关键词：).*(' + ($patterns -join '|') + ')'

$roots = @(
  (Join-Path -Path $Vault -ChildPath 'daily'),
  (Join-Path -Path $Vault -ChildPath 'topics'),
  (Join-Path -Path $Vault -ChildPath 'inbox')
)

$hits = @()
foreach ($root in $roots) {
  if (!(Test-Path $root)) { continue }

  $args = @('--no-heading','--with-filename','--line-number','--color','never','-S','--text', $keywordRegex, $root)
  $out = & $rgExe @args 2>$null
  foreach ($line in $out) {
    if ($line -match '^(?<path>.+?):(?<line>\d+):(?<snippet>.*)$') {
      $hits += [pscustomobject]@{ Path=$Matches['path']; Line=[int]$Matches['line']; Snippet=$Matches['snippet']; Score=2 }
    }
  }
}

# Fall back to full-text matches for remaining.
foreach ($root in $roots) {
  if (!(Test-Path $root)) { continue }

  $fullRegex = ($patterns -join '|')
  $args = @('--no-heading','--with-filename','--line-number','--color','never','-S','--text', $fullRegex, $root)
  $out = & $rgExe @args 2>$null
  foreach ($line in $out) {
    if ($line -match '^(?<path>.+?):(?<line>\d+):(?<snippet>.*)$') {
      $hits += [pscustomobject]@{ Path=$Matches['path']; Line=[int]$Matches['line']; Snippet=$Matches['snippet']; Score=1 }
    }
  }
}

# Clean snippet: keep first match line only
foreach ($h in $hits) {
  if ($h.Snippet -match '^(?<one>[^\r\n]+)') {
    $h.Snippet = $Matches['one']
  }
}

$results = $hits |
  Sort-Object -Property @(
    @{Expression='Score'; Descending=$true},
    @{Expression='Path'; Descending=$false},
    @{Expression='Line'; Descending=$false}
  ) |
  Group-Object -Property Path |
  ForEach-Object {
    $first = $_.Group | Sort-Object -Property @(
      @{Expression='Score'; Descending=$true},
      @{Expression='Line'; Descending=$false}
    ) | Select-Object -First 1
    [pscustomobject]@{ Path=$_.Name; Score=$first.Score; Line=$first.Line; Snippet=$first.Snippet }
  } |
  Sort-Object -Property @(
    @{Expression='Score'; Descending=$true},
    @{Expression='Path'; Descending=$false}
  ) |
  Select-Object -First $Limit

# Normalize output encoding quirks (some shells show UTF-8 as mojibake)
function Normalize-Text([string]$s) {
  if (-not $s) { return $s }
  try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($s)
    return [System.Text.Encoding]::UTF8.GetString($bytes)
  } catch {
    return $s
  }
}

foreach ($r in $results) {
  $r.Path = Normalize-Text $r.Path
  $r.Snippet = Normalize-Text $r.Snippet
}

$results | ConvertTo-Json -Depth 3
