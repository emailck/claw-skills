import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
ROOT = SKILL_DIR.parents[1]
MIMO_TTS = SKILL_DIR / 'scripts' / 'mimo_tts.py'
FEISHU_SEND = SKILL_DIR / 'scripts' / 'feishu_send_audio_from_wav.py'
OPENCLAW_JSON = Path.home() / '.openclaw' / 'openclaw.json'


def load_feishu_cfg():
    data = json.loads(OPENCLAW_JSON.read_text(encoding='utf-8'))
    feishu = data.get('channels', {}).get('feishu', {})
    app_id = feishu.get('appId')
    app_secret = feishu.get('appSecret')
    if not app_id or not app_secret:
        raise RuntimeError('Missing Feishu appId/appSecret in openclaw.json')
    return app_id, app_secret


def main():
    p = argparse.ArgumentParser(description='Generate voice with MiMo and send as Feishu audio message')
    p.add_argument('--text', required=True, help='Text to synthesize')
    p.add_argument('--receive-id', required=True, help='Feishu open_id/chat_id/etc')
    p.add_argument('--receive-id-type', default='open_id', help='open_id | chat_id | user_id | union_id | email')
    p.add_argument('--voice', default='default_zh')
    p.add_argument('--preset', default=None, help='Optional MiMo preset; leave empty to use explicit style only')
    p.add_argument('--style', default='少女感 夹子音 清冷感', help='Default style with 少女感 plus a bit of夹子音 and 清冷感')
    p.add_argument('--output-wav', default=str(ROOT / 'tmp_mimo_feishu_voice.wav'))
    p.add_argument('--api-key', default=os.getenv('MIMO_API_KEY'))
    p.add_argument('--user-prompt', default='请用自然、稳定、适合飞书语音条收听的方式读出 assistant 文本。', help='Optional MiMo user message for style/context guidance')
    p.add_argument('--max-completion-tokens', type=int, default=8192)
    args = p.parse_args()

    if not args.api_key:
        raise SystemExit('Missing MIMO_API_KEY (pass --api-key or set env)')

    app_id, app_secret = load_feishu_cfg()

    output_wav = Path(args.output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    tts_cmd = [
        sys.executable,
        str(MIMO_TTS),
        '--text', args.text,
        '--output', str(output_wav),
        '--voice', args.voice,
        '--format', 'wav',
        '--api-key', args.api_key,
        '--user-prompt', args.user_prompt,
        '--max-completion-tokens', str(args.max_completion_tokens),
    ]
    if args.preset:
        tts_cmd.extend(['--preset', args.preset])
    if args.style:
        tts_cmd.extend(['--style', args.style])
    subprocess.run(tts_cmd, check=True)

    env = os.environ.copy()
    env['FEISHU_APP_ID'] = app_id
    env['FEISHU_APP_SECRET'] = app_secret

    send_cmd = [
        sys.executable,
        str(FEISHU_SEND),
        str(output_wav),
        '--receive-id', args.receive_id,
        '--receive-id-type', args.receive_id_type,
    ]
    subprocess.run(send_cmd, check=True, env=env)


if __name__ == '__main__':
    main()
