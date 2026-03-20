import argparse
import io
import json
import os
import struct
import sys
import tempfile
import wave
from pathlib import Path

import requests
import av

TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
FILE_URL = 'https://open.feishu.cn/open-apis/im/v1/files'
MSG_URL = 'https://open.feishu.cn/open-apis/im/v1/messages'


def get_tenant_token(app_id: str, app_secret: str) -> str:
    resp = requests.post(TOKEN_URL, json={"app_id": app_id, "app_secret": app_secret}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(f"token error: {data}")
    return data['tenant_access_token']


def read_wav_pcm16_mono(path: Path):
    with wave.open(str(path), 'rb') as w:
        channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        framerate = w.getframerate()
        nframes = w.getnframes()
        frames = w.readframes(nframes)
    if sampwidth != 2:
        raise ValueError(f'only 16-bit wav supported, got sampwidth={sampwidth}')
    if channels == 2:
        samples = struct.unpack('<' + 'h' * (len(frames)//2), frames)
        mono = []
        for i in range(0, len(samples), 2):
            mono.append(int((samples[i] + samples[i+1]) / 2))
        frames = struct.pack('<' + 'h' * len(mono), *mono)
        channels = 1
    if channels != 1:
        raise ValueError(f'only mono/stereo wav supported, got channels={channels}')
    return frames, framerate, nframes, channels


def resample_linear_pcm16(raw: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate:
        return raw
    samples = struct.unpack('<' + 'h' * (len(raw)//2), raw)
    src_len = len(samples)
    dst_len = max(1, round(src_len * dst_rate / src_rate))
    out = []
    for i in range(dst_len):
        pos = i * (src_len - 1) / max(1, dst_len - 1)
        left = int(pos)
        right = min(left + 1, src_len - 1)
        frac = pos - left
        val = int(samples[left] * (1 - frac) + samples[right] * frac)
        out.append(val)
    return struct.pack('<' + 'h' * len(out), *out)


def wav_to_real_opus_ogg(path: Path) -> tuple[bytes, int]:
    with wave.open(str(path), 'rb') as w:
        duration_ms = round(w.getnframes() / w.getframerate() * 1000)

    with tempfile.NamedTemporaryFile(suffix='.opus', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        in_container = av.open(str(path))
        stream = in_container.streams.audio[0]
        out_container = av.open(str(tmp_path), mode='w', format='ogg')
        out_stream = out_container.add_stream('libopus', rate=48000)
        out_stream.layout = 'mono'
        out_stream.bit_rate = 32000
        resampler = av.audio.resampler.AudioResampler(format='s16', layout='mono', rate=48000)

        for frame in in_container.decode(stream):
            frame = resampler.resample(frame)
            frames = frame if isinstance(frame, list) else [frame]
            for fr in frames:
                for packet in out_stream.encode(fr):
                    out_container.mux(packet)

        for packet in out_stream.encode(None):
            out_container.mux(packet)

        out_container.close()
        in_container.close()
        data = tmp_path.read_bytes()
        return data, duration_ms
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def upload_audio(token: str, audio_bytes: bytes, duration_ms: int, file_name: str = 'voice.opus') -> str:
    headers = {'Authorization': f'Bearer {token}'}
    files = {
        'file': (file_name, io.BytesIO(audio_bytes), 'audio/ogg'),
    }
    data = {
        'file_type': 'opus',
        'file_name': file_name,
        'duration': str(duration_ms),
    }
    resp = requests.post(FILE_URL, headers=headers, data=data, files=files, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    if body.get('code') != 0:
        raise RuntimeError(f'upload error: {body}')
    return body['data']['file_key']


def send_audio_message(token: str, receive_id: str, file_key: str, receive_id_type: str = 'open_id'):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=utf-8',
    }
    payload = {
        'receive_id': receive_id,
        'msg_type': 'audio',
        'content': json.dumps({'file_key': file_key}, ensure_ascii=False),
    }
    resp = requests.post(f'{MSG_URL}?receive_id_type={receive_id_type}', headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if body.get('code') != 0:
        raise RuntimeError(f'send error: {body}')
    return body


def main():
    p = argparse.ArgumentParser()
    p.add_argument('wav_path')
    p.add_argument('--receive-id', required=True)
    p.add_argument('--receive-id-type', default='open_id')
    p.add_argument('--app-id', default=os.getenv('FEISHU_APP_ID'))
    p.add_argument('--app-secret', default=os.getenv('FEISHU_APP_SECRET'))
    args = p.parse_args()

    if not args.app_id or not args.app_secret:
        raise SystemExit('Missing FEISHU_APP_ID / FEISHU_APP_SECRET')

    wav_path = Path(args.wav_path)
    audio_bytes, duration_ms = wav_to_real_opus_ogg(wav_path)
    token = get_tenant_token(args.app_id, args.app_secret)
    file_key = upload_audio(token, audio_bytes, duration_ms)
    result = send_audio_message(token, args.receive_id, file_key, args.receive_id_type)
    print(json.dumps({'ok': True, 'file_key': file_key, 'duration_ms': duration_ms, 'result': result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
