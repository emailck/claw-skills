# Feishu MiMo Voice - Quick Reference

## 当前默认参数

- voice: `default_zh`
- output format: `wav`
- delivery: Feishu `msg_type=audio`

## 当前用户私聊发送模板

```powershell
$env:MIMO_API_KEY="<key>"
python skills/feishu-mimo-voice/send_mimo_feishu_voice.py --text "爸爸，这是测试语音。" --receive-id ou_5de4807445c5776ac4caf91f982470dd --receive-id-type open_id
```

## 适合直接触发的用户表达

- 用语音回复我：xxx
- 发语音给我：xxx
- 这句用语音发我
- 朗读这段话并发给我
- 用语音说这句话：xxx

## 不适合直接执行的表达

- 发语音（但没给文本）
- 试试语音功能（但没给内容）
- 以后都用语音回复（这是偏好，不是一次性执行指令）
