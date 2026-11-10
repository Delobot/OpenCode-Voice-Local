#!/usr/bin/env python3
"""Silero v5_ru synthesis helper for the voice-hub server.

Reads text from stdin, writes a 48 kHz mono 16-bit WAV to --out.
"""
import argparse
import os
import sys
import wave

import torch

_model = None


def get_model():
    global _model
    if _model is None:
        device = torch.device("cpu")
        torch.set_num_threads(max(1, (os.cpu_count() or 4) // 2))
        _model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ru",
            speaker="v5_ru",
            device=device,
            trust_repo=True,
        )
    return _model


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--sample-rate", type=int, default=48000)
    args = ap.parse_args()

    text = sys.stdin.read().strip()
    if not text:
        raise SystemExit("empty input text")

    model = get_model()
    # Silero: put_stress_and_homo flags handled by the model defaults.
    audio = model.apply_tts(text=text, speaker=args.speaker, sample_rate=args.sample_rate)
    if args.speed != 1.0 and args.speed > 0:
        # resample-based tempo change via simple linear interpolation
        import numpy as np
        n = int(len(audio) / args.speed)
        idx = np.linspace(0, len(audio) - 1, n)
        audio = torch.from_numpy(np.interp(idx, np.arange(len(audio)), audio.numpy()))

    samples = (audio.numpy() * 32767).astype("int16")
    with wave.open(args.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(args.sample_rate)
        w.writeframes(samples.tobytes())


if __name__ == "__main__":
    main()
