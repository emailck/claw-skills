---
name: feishu-mimo-voice
description: |
  用小米 MiMo TTS 生成语音，并以飞书原生语音条（audio message）发送。用于用户明确要求“用语音回复我 XXX”“发语音给我”“把这段话朗读并发到飞书”“语音回复这句”等场景。尤其适合当前会话是 Feishu，且需要把文本转成飞书里可直接播放的原生语音条，而不是普通文件附件。
---

# Feishu MiMo Voice

## 功能

把一段文本：
1. 用 Xiaomi MiMo TTS 生成 WAV
2. 上传到飞书 IM 文件接口
3. 发送为 `msg_type: audio` 的原生语音条

## 何时使用

当用户明确要求：
- 用语音回复
- 发语音给我
- 把这段话朗读出来并发到飞书

## 当前实现边界

- 当前优先支持 **Feishu 私聊/群聊**
- 当前 TTS 使用 `mimo_tts.py`
- 当前发送链路使用 `feishu_send_audio_from_wav.py`
- 目前默认中文音色：`default_zh`
- 当前默认风格词：`少女感 夹子音 清冷感`
- 当前默认会附带 MiMo `user` 消息做上下文约束：`请用自然、稳定、适合飞书语音条收听的方式读出 assistant 文本。`
- 当前默认显式传 `max_completion_tokens=8192`，与官网文档里 `mimo-v2-tts` 默认上限保持一致
- `preset` 改为可选；默认优先使用这组已验证 style，而不是 `gentle-cute`
- 默认输出 WAV，再走飞书 audio message 发送

## 依赖

需要以下条件：
- 可用的 `MIMO_API_KEY`
- 本地已配置 Feishu `appId/appSecret`
- Python 可运行 `requests`

## 执行步骤

### 1. 生成语音

运行：

```powershell
python mimo_tts.py --text "要朗读的文本" --output tmp.wav --voice default_zh --format wav --api-key "$MIMO_API_KEY"
```

### 2. 发送飞书语音条

运行：

```powershell
$env:FEISHU_APP_ID='...'
$env:FEISHU_APP_SECRET='...'
python feishu_send_audio_from_wav.py tmp.wav --receive-id ou_xxx --receive-id-type open_id
```

## 推荐交互规则

- 如果用户只说“发语音”，但没给文本：先追问要朗读什么
- 如果用户说“用语音回复我 XXX”/“发语音给我 XXX”/“把这句话语音发我：XXX”：直接提取 `XXX` 作为朗读文本并执行，不要再重复确认
- 如果当前就是飞书私聊：默认发回当前用户
- 如果用户指定其他飞书对象：再使用对应 `open_id` / `chat_id`
- 成功后，只需简短确认“已发语音”即可，不要重复整段文本

## 自动触发执行约定

当满足以下条件时，应直接使用本技能：
1. 当前会话为 Feishu
2. 用户明确要求“用语音回复”或“发语音”
3. 用户已经给出了要朗读的文本

推荐执行命令：

```powershell
$env:MIMO_API_KEY="<本地可用 key>"
python skills/feishu-mimo-voice/send_mimo_feishu_voice.py --text "要朗读的文本" --receive-id <当前用户open_id> --receive-id-type open_id
```

如果当前会话的用户 open_id 已知，就直接拿当前会话用户作为 `receive-id`。

## 注意

- `MIMO_API_KEY` 不要写进技能文档或提交到仓库
- 若未来要长期使用，建议把 key 放进本地环境变量或独立配置文件
- 当前 `feishu_send_audio_from_wav.py` 已验证可用，是最小闭环版本
