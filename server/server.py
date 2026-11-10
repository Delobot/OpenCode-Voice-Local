#!/usr/bin/env python3
"""Local voice-hub TTS server (OpenAI-compatible) with voice management.

Used by the opencode voice plugin (engine "openai") and by the
voice-manager GUI plugin settings page.

Endpoints:
  GET  /health                     -> liveness + default voice
  GET  /v1/models                  -> OpenAI-style model list
  GET  /voices                     -> installed voices + catalog (ru only)
  POST /voices/select {voice}      -> set default voice
  POST /voices/download {voice}    -> download a catalog voice (piper)
  POST /voices/delete {voice}      -> delete an installed piper voice
  GET  /voices/preview?voice=x     -> short WAV sample of the voice
  POST /v1/audio/speech            -> OpenAI-compatible synthesis

Engines:
  piper  — onnx models in ~/.local/share/piper-voices (voice ids "ru_RU-*")
  silero — Silero v5_ru via torch (voice ids: aidar, baya, kseniya, xenia, eugene)

Everything stays on this machine.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME = os.path.expanduser("~")
PIPER_BIN = os.path.join(HOME, ".local/bin/piper")
PIPER_DIR = os.path.join(HOME, ".local/share/piper-voices")
SILERO_PY = os.path.join(HOME, ".config/opencode/silero-tts/venv/bin/python")
SILERO_SYNTH = os.path.join(HOME, ".config/opencode/silero-tts/synth.py")
CONFIG_PATH = os.path.join(HOME, ".config/opencode/piper-tts/config.json")
HOST = "127.0.0.1"
PORT = 8095

# Russian Piper voices on HuggingFace (the complete ru_RU set).
PIPER_CATALOG = {
    "ru_RU-denis-medium": {
        "engine": "piper",
        "label": "Денис (Piper, мужской)",
        "gender": "male",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx",
        "conf": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx.json",
    },
    "ru_RU-dmitri-medium": {
        "engine": "piper",
        "label": "Дмитрий (Piper, мужской)",
        "gender": "male",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx",
        "conf": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx.json",
    },
    "ru_RU-irina-medium": {
        "engine": "piper",
        "label": "Ирина (Piper, женский)",
        "gender": "female",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx",
        "conf": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx.json",
    },
    "ru_RU-ruslan-medium": {
        "engine": "piper",
        "label": "Руслан (Piper, мужской)",
        "gender": "male",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx",
        "conf": "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx.json",
    },
}

SILERO_VOICES = {
    "aidar": {"engine": "silero", "label": "Айдар (Silero, мужской, нейтральный)", "gender": "male"},
    "baya": {"engine": "silero", "label": "Бая (Silero, мужской, мягкий)", "gender": "male"},
    "kseniya": {"engine": "silero", "label": "Ксения (Silero, женский, деловой)", "gender": "female"},
    "xenia": {"engine": "silero", "label": "Ксения-2 (Silero, женский, дружелюбный)", "gender": "female"},
    "eugene": {"engine": "silero", "label": "Евгений (Silero, мужской, глубокий)", "gender": "male"},
}

_lock = threading.Lock()
_config_lock = threading.Lock()


def load_config() -> dict:
    try:
        with open(CONFIG_PATH) as fh:
            return json.load(fh)
    except Exception:
        return {"default_voice": "eugene"}


def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with _config_lock, open(CONFIG_PATH, "w") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)


def voice_info(voice_id: str) -> dict | None:
    """Voice metadata if the id is known (catalog or silero)."""
    return PIPER_CATALOG.get(voice_id) or SILERO_VOICES.get(voice_id)


def piper_installed(voice_id: str) -> bool:
    return os.path.exists(os.path.join(PIPER_DIR, voice_id + ".onnx"))


def resolve_voice(voice_id: str | None) -> tuple[str, str]:
    """(engine, id) for a requested voice, falling back to the default."""
    cfg = load_config()
    vid = (voice_id or "").strip() or cfg.get("default_voice", "eugene")
    info = voice_info(vid)
    if info is None:
        vid = cfg.get("default_voice", "eugene")
        info = voice_info(vid) or SILERO_VOICES["eugene"]
    engine = info["engine"]
    if engine == "piper" and not piper_installed(vid):
        # model missing: fall back to default if it differs
        default = cfg.get("default_voice", "eugene")
        if default != vid:
            return resolve_voice(default)
        raise RuntimeError(f"voice model missing on disk: {vid}")
    return engine, vid


def synth_piper(voice_id: str, text: str, speed: float, out: str) -> None:
    model = os.path.join(PIPER_DIR, voice_id + ".onnx")
    length_scale = round(1.0 / max(speed, 0.1), 3)
    with _lock:
        proc = subprocess.run(
            [PIPER_BIN, "-m", model, "-f", out, "--length-scale", str(length_scale)],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=300,
        )
    if proc.returncode != 0 or not os.path.exists(out):
        err = proc.stderr.decode("utf-8", "replace")[-500:]
        raise RuntimeError(f"piper failed: {err}")


def synth_silero(voice_id: str, text: str, speed: float, out: str) -> None:
    global _silero_model
    # Prefer in-process synthesis (model stays warm); fall back to a subprocess
    # with the dedicated venv python if torch is not importable here.
    try:
        sys.path.insert(0, os.path.dirname(SILERO_SYNTH))
        from synth import get_model  # type: ignore
        import numpy as np
        import torch

        if _silero_model is None:
            _silero_model = get_model()
        audio = _silero_model.apply_tts(text=text, speaker=voice_id, sample_rate=48000)
        if speed != 1.0 and speed > 0:
            n = int(len(audio) / speed)
            idx = np.linspace(0, len(audio) - 1, n)
            audio = torch.from_numpy(np.interp(idx, np.arange(len(audio)), audio.numpy()))
        samples = (audio.numpy() * 32767).astype("int16")
        import wave as wavmod
        with wavmod.open(out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(48000)
            w.writeframes(samples.tobytes())
        return
    except ImportError:
        pass
    with _lock:
        proc = subprocess.run(
            [SILERO_PY, SILERO_SYNTH, "--speaker", voice_id, "--speed", str(speed), "--out", out],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=300,
        )
    if proc.returncode != 0 or not os.path.exists(out):
        err = proc.stderr.decode("utf-8", "replace")[-800:]
        raise RuntimeError(f"silero failed: {err}")


_silero_model = None


def synth(engine: str, voice_id: str, text: str, speed: float, out: str) -> None:
    if engine == "piper":
        synth_piper(voice_id, text, speed, out)
    else:
        synth_silero(voice_id, text, speed, out)


def list_voices() -> dict:
    installed = []
    for vid, info in sorted(SILERO_VOICES.items()):
        installed.append({
            "id": vid, "label": info["label"], "engine": info["engine"],
            "gender": info["gender"], "installed": True, "deletable": False,
        })
    for vid, info in sorted(PIPER_CATALOG.items()):
        installed.append({
            "id": vid, "label": info["label"], "engine": info["engine"],
            "gender": info["gender"], "installed": piper_installed(vid),
            "deletable": piper_installed(vid), "size_mb": 63,
        })
    cfg = load_config()
    return {"voices": installed, "default_voice": cfg.get("default_voice", "eugene"),
            "silero_ready": os.path.exists(SILERO_PY)}


def download_voice(voice_id: str) -> dict:
    info = PIPER_CATALOG.get(voice_id)
    if info is None:
        raise RuntimeError(f"unknown voice: {voice_id}")
    if piper_installed(voice_id):
        return {"ok": True, "already": True}
    os.makedirs(PIPER_DIR, exist_ok=True)
    onnx = os.path.join(PIPER_DIR, voice_id + ".onnx")
    conf = os.path.join(PIPER_DIR, voice_id + ".onnx.json")
    urllib.request.urlretrieve(info["url"], onnx)
    urllib.request.urlretrieve(info["conf"], conf)
    return {"ok": True, "already": False}


def delete_voice(voice_id: str) -> dict:
    if voice_id not in PIPER_CATALOG:
        raise RuntimeError(f"voice cannot be deleted: {voice_id}")
    if not piper_installed(voice_id):
        return {"ok": True, "already": True}
    for suffix in (".onnx", ".onnx.json"):
        try:
            os.remove(os.path.join(PIPER_DIR, voice_id + suffix))
        except FileNotFoundError:
            pass
    cfg = load_config()
    if cfg.get("default_voice") == voice_id:
        cfg["default_voice"] = "eugene"
        save_config(cfg)
    return {"ok": True, "already": False}


PREVIEW_TEXT = "Привет! Так звучит этот голос. Проверка синтеза речи на русском языке."


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _headers(self, code: int, ctype: str, length: int) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self._headers(code, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def _error(self, code: int, message: str) -> None:
        self._json(code, {"error": {"message": message}})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def _wav(self, path: str) -> None:
        with open(path, "rb") as fh:
            audio = fh.read()
        self._headers(200, "audio/wav", len(audio))
        self.wfile.write(audio)

    def do_OPTIONS(self):
        self._headers(204, "text/plain", 0)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        try:
            if path == "/health":
                cfg = load_config()
                self._json(200, {"health": "ok", "default_voice": cfg.get("default_voice"),
                                 "silero_ready": os.path.exists(SILERO_PY)})
            elif path in ("/v1/models", "/models"):
                self._json(200, {"object": "list",
                                 "data": [{"id": "voice-hub", "object": "model", "owned_by": "local"}]})
            elif path == "/voices":
                self._json(200, list_voices())
            elif path == "/voices/preview":
                params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
                engine, vid = resolve_voice(params.get("voice", "").strip())
                with tempfile.TemporaryDirectory(prefix="voice-hub-") as td:
                    out = os.path.join(td, "out.wav")
                    synth(engine, vid, PREVIEW_TEXT, 1.0, out)
                    self._wav(out)
            else:
                self._error(404, f"not found: {path}")
        except Exception as exc:  # noqa: BLE001
            self._error(500, str(exc))

    def do_POST(self):
        try:
            if self.path.rstrip("/").endswith("/audio/speech"):
                payload = self._read_body()
                text = (payload.get("input") or "").strip()
                if not text:
                    return self._error(400, "input is empty")
                try:
                    speed = float(payload.get("speed") or 1)
                except (TypeError, ValueError):
                    speed = 1.0
                # The settings page is the single source of truth: synthesis
                # always uses the server default voice, ignoring the stale
                # voice id the plugin may send.
                engine, vid = resolve_voice(None)
                with tempfile.TemporaryDirectory(prefix="voice-hub-") as td:
                    out = os.path.join(td, "out.wav")
                    synth(engine, vid, text, speed, out)
                    self._wav(out)
                return
            payload = self._read_body()
            voice = (payload.get("voice") or "").strip()
            if not voice:
                return self._error(400, "voice is required")
            if self.path.rstrip("/").endswith("/voices/select"):
                if voice_info(voice) is None:
                    return self._error(400, f"unknown voice: {voice}")
                cfg = load_config()
                cfg["default_voice"] = voice
                save_config(cfg)
                return self._json(200, {"ok": True, "default_voice": voice})
            if self.path.rstrip("/").endswith("/voices/download"):
                return self._json(200, download_voice(voice))
            if self.path.rstrip("/").endswith("/voices/delete"):
                return self._json(200, delete_voice(voice))
            self._error(404, f"not found: {self.path}")
        except json.JSONDecodeError:
            self._error(400, "invalid JSON body")
        except Exception as exc:  # noqa: BLE001
            self._error(500, str(exc))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    cfg = load_config()
    print(f"voice-hub on http://{HOST}:{PORT} (default voice: {cfg.get('default_voice')})")
    server.serve_forever()


if __name__ == "__main__":
    main()
