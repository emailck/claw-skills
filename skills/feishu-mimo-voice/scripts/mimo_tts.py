#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Missing dependency: requests\nInstall with: pip install requests", file=sys.stderr)
    raise

API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
DEFAULT_MODEL = "mimo-v2-tts"
DEFAULT_VOICE = "mimo_default"
DEFAULT_FORMAT = "wav"
VALID_VOICES = {"mimo_default", "default_zh", "default_en"}
VALID_FORMATS = {"wav", "mp3", "pcm"}
PRESETS = {
    "gentle-cute": {
        "voice": "default_zh",
        "style": "温柔 轻声 夹子音 变慢",
    },
    "gentle": {
        "voice": "default_zh",
        "style": "温柔 轻声 变慢",
    },
    "sweet": {
        "voice": "default_zh",
        "style": "温柔 轻声 撒娇 夹子音 变慢",
    },
}


def read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    data = sys.stdin.read().strip()
    if data:
        return data
    raise ValueError("No text provided. Use --text, --text-file, or stdin.")


def ensure_output_path(output: Optional[str], audio_format: str) -> Path:
    suffix = f".{audio_format}"
    if output:
        path = Path(output)
        if path.suffix.lower() != suffix:
            path = path.with_suffix(suffix)
    else:
        path = Path.cwd() / f"mimo_tts_output{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def apply_style(text: str, style: Optional[str]) -> str:
    clean = text.strip()
    if not style:
        return clean
    if clean.startswith("<style>"):
        return clean
    return f"<style>{style}</style>{clean}"


def build_payload(text: str, voice: str, audio_format: str, user_prompt: Optional[str], model: str, max_completion_tokens: Optional[int] = None) -> dict:
    messages = []
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    messages.append({"role": "assistant", "content": text})
    payload = {
        "model": model,
        "messages": messages,
        "audio": {
            "format": audio_format,
            "voice": voice,
        },
    }
    if max_completion_tokens is not None:
        payload["max_completion_tokens"] = max_completion_tokens
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Xiaomi MiMo TTS minimal client")
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--text-file", help="Read text from a UTF-8 file")
    parser.add_argument("--user-prompt", help="Optional user message for style/context")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Voice: mimo_default | default_zh | default_en")
    parser.add_argument("--format", default=DEFAULT_FORMAT, help="Audio format: wav | mp3 | pcm")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id, default mimo-v2-tts")
    parser.add_argument("--style", help="Style words to inject as <style>...</style> prefix")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), help="Ready-made style preset")
    parser.add_argument("--list-presets", action="store_true", help="List available presets and exit")
    parser.add_argument("--output", help="Output audio file path")
    parser.add_argument("--api-key", help="MiMo API key; defaults to env MIMO_API_KEY")
    parser.add_argument("--header-mode", choices=["api-key", "bearer"], default="api-key", help="Auth header mode")
    parser.add_argument("--max-completion-tokens", type=int, default=8192, help="MiMo TTS max_completion_tokens, default 8192 per docs")
    parser.add_argument("--dump-response", action="store_true", help="Print raw JSON response metadata")
    args = parser.parse_args()

    if args.list_presets:
        print(json.dumps(PRESETS, ensure_ascii=False, indent=2))
        return 0

    api_key = args.api_key or os.getenv("MIMO_API_KEY")
    if not api_key:
        print("Missing MIMO API key. Set MIMO_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    try:
        text = read_text(args)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2

    if not text:
        print("Text is empty.", file=sys.stderr)
        return 2

    preset = PRESETS.get(args.preset) if args.preset else None
    voice = (args.voice or "").strip() or DEFAULT_VOICE
    style = args.style

    if preset:
        if args.voice == DEFAULT_VOICE:
            voice = preset["voice"]
        if not style:
            style = preset["style"]

    if voice not in VALID_VOICES:
        print(f"Invalid voice: {voice}. Valid: {', '.join(sorted(VALID_VOICES))}", file=sys.stderr)
        return 2

    audio_format = args.format.strip().lower()
    if audio_format not in VALID_FORMATS:
        print(f"Invalid format: {audio_format}. Valid: {', '.join(sorted(VALID_FORMATS))}", file=sys.stderr)
        return 2

    final_text = apply_style(text, style)
    payload = build_payload(text=final_text, voice=voice, audio_format=audio_format, user_prompt=args.user_prompt, model=args.model, max_completion_tokens=args.max_completion_tokens)

    headers = {"Content-Type": "application/json"}
    if args.header_mode == "api-key":
        headers["api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1

    if resp.status_code >= 400:
        print(f"HTTP {resp.status_code}\n{resp.text}", file=sys.stderr)
        return 1

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("Response is not valid JSON:", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        return 1

    if args.dump_response:
        print(json.dumps(data, ensure_ascii=False, indent=2))

    try:
        audio_b64 = data["choices"][0]["message"]["audio"]["data"]
    except Exception:
        print("Could not find choices[0].message.audio.data in response.", file=sys.stderr)
        print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        print(f"Failed to decode audio base64: {e}", file=sys.stderr)
        return 1

    output_path = ensure_output_path(args.output, audio_format)
    output_path.write_bytes(audio_bytes)

    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
