# Codex 中文乱码修复操作说明（Windows PowerShell 5.1 + PowerShell 7 通用）
关键词：#Codex #Windows #PowerShell #UTF8 #终端 #编码修复 #配置

## 一、目的
解决 Codex 在 Windows 下中文乱码问题，并让配置长期生效，同时兼容 PowerShell 5.1 与 PowerShell 7。

## 二、适用范围
- 操作系统：Windows
- Shell：powershell.exe（5.1）和 pwsh（7）
- 用户目录示例：C:\Users\email

## 三、配置 Codex 为 UTF-8
编辑 `.codex/config.toml`，确认包含：

```toml
[windows]
sandbox = "unelevated"
powershell_utf8 = true
```

## 四、同时写入 PS5/PS7 的 UTF-8 启动配置
在 PowerShell 中执行以下脚本（可重复执行，自动覆盖旧配置块）：

```powershell
$utf8Block = @'
# >>> codex-utf8-begin >>>
try { chcp 65001 | Out-Null } catch {}
try {
  $utf8 = [System.Text.UTF8Encoding]::new($false)
  [Console]::InputEncoding = $utf8
  [Console]::OutputEncoding = $utf8
  $OutputEncoding = $utf8
} catch {}
try { $PSDefaultParameterValues['*:Encoding'] = 'utf8' } catch {}
# <<< codex-utf8-end <<<
'@

$profiles = @(
  "$HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1", # PS 5.1
  "$HOME\Documents\PowerShell\Microsoft.PowerShell_profile.ps1" # PS 7
)

foreach ($p in $profiles) {
  New-Item -ItemType Directory -Force -Path (Split-Path $p) | Out-Null
  if (-not (Test-Path $p)) { New-Item -ItemType File -Force -Path $p | Out-Null }

  $raw = Get-Content $p -Raw -ErrorAction SilentlyContinue
  $raw = [regex]::Replace(
    $raw,
    '(?s)# >>> codex-utf8-begin >>>.*?# <<< codex-utf8-end <<<\r?\n?',
    ''
  )

  if ($raw -and -not $raw.EndsWith("`r`n")) { $raw += "`r`n" }

  Set-Content -Path $p -Value ($raw + $utf8Block + "`r`n") -Encoding utf8
  Write-Host "Updated: $p"
}
```

涉及文件：
- PS 5.1 配置文件
- PS 7 配置文件

## 五、重启生效
关闭所有 PowerShell / Codex 终端后重新打开，再启动 Codex。

## 六、验证步骤

### 1）验证当前 PowerShell 会话
```powershell
$PSVersionTable.PSVersion
[Console]::InputEncoding.WebName
[Console]::OutputEncoding.WebName
$PSDefaultParameterValues['*:Encoding']
chcp
```

预期：
- InputEncoding = utf-8
- OutputEncoding = utf-8
- *:Encoding = utf8
- code page = 65001

### 2）验证中文读写
```powershell
$tmp = Join-Path $env:TEMP 'codex-utf8-test.txt'
$text='中文编码测试：你好，世界，编码正常。'
Set-Content -Path $tmp -Value $text -Encoding utf8
Get-Content -Path $tmp -Raw
```

预期：输出原文，不出现 `�`。

## 七、注意事项
- 这是永久配置（写入 profile + config.toml）。
- 如果使用 `-NoProfile` 启动，profile 不会加载，可能再次乱码。
- 历史已损坏的乱码内容不会自动恢复，需要从 Git/历史版本回滚或手工修复。

## 八、回滚方法
1. 删除 `.codex/config.toml` 中的 `powershell_utf8 = true`。
2. 删除两个 profile 中 `# >>> codex-utf8-begin >>>` 到 `# <<< codex-utf8-end <<<` 的配置块。
3. 重新打开终端。
