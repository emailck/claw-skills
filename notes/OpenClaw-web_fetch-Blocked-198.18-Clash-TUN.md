# OpenClaw `web_fetch` 报错：Blocked: resolves to private/internal/special-use IP address
关键词：#OpenClaw #web_fetch #Clash #TUN #DNS #fake-ip #故障排查

## 现象
- 在 OpenClaw 中调用 `web_fetch`（或依赖它的技能，如 `multi-search-engine`）抓取搜索引擎/网站时失败。
- 典型报错：`Blocked: resolves to private/internal/special-use IP address`

## 根因（为什么会被拦）
- `web_fetch` 在发起请求前会做 DNS 解析与安全校验（SSRF 防护）。
- 当前系统 DNS 解析结果被改写到了 `198.18.0.0/15` 网段（保留的基准测试/特殊用途网段，不是正常公网地址）。
- 因为它属于“internal/special-use IP”，`web_fetch` 为安全起见直接拦截。

### 本机验证结果（关键线索）
- `nslookup duckduckgo.com` → `198.18.0.244`
- `nslookup cn.bing.com` → `198.18.0.30`
- `nslookup www.baidu.com` → `198.18.1.25`
- DNS Server 显示：`198.18.0.2`

## 与 Clash TUN 的关系
- 用户开启 Clash 的 **TUN 模式**后，DNS/流量常被接管。
- 若 DNS 启用 `fake-ip`（或类似“伪装 IP”策略），Clash 可能会把域名解析成 `198.18.*` 这类保留网段，用于透明代理与规则分流。
- 浏览器可能仍能访问，但 `web_fetch` 会因安全策略拒绝。

## 解决目标
- 让 DNS 返回 **真实公网 IP**，避免解析到 `198.18.*` / 私网段。
- 验证标准：再次运行 `nslookup cn.bing.com` / `nslookup duckduckgo.com`，不再出现 `198.18.*`。

## 推荐解决方案（按优先级）
### 方案 1（推荐）：保留 TUN，关闭 fake-ip（改用 redir-host）
- 在 Clash 客户端的 DNS 设置中，将 `enhanced-mode` 从 `fake-ip` 改为 `redir-host`（或把“Fake-IP”切换为“Redir-Host”）。
- 保存/应用配置。
- 重启 Clash（或重启 TUN）。

### 方案 2：关闭 DNS 接管 / 改为使用系统 DNS
- 关闭 DNS 相关的“劫持/接管”开关（不同客户端名字不同）。
- 或启用“Respect system DNS / Use system DNS”。
- 重启 Clash 后用 `nslookup` 验证。

### 方案 3（临时验证）：关闭 TUN
- 临时关闭 TUN 模式。
- 运行 `nslookup` 看是否立刻恢复为公网 IP。
- 确认根因后再按方案 1 修正并重新开启 TUN。

## 配置文件参考（YAML 方向）
> 关键是 `enhanced-mode: redir-host`，其余按自身网络环境调整。

```yaml
dns:
  enable: true
  enhanced-mode: redir-host
  nameserver:
    - 223.5.5.5
    - 223.6.6.6
  fallback:
    - 1.1.1.1
    - 8.8.8.8
```

## 修复后检查
1) `nslookup duckduckgo.com` / `nslookup cn.bing.com`
2) 再尝试 OpenClaw：`web_fetch` 抓取任意外网搜索结果页
3) `multi-search-engine` 技能应可恢复正常工作
