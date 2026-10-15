#!/usr/bin/env python3
"""Synthesize original demo scores. Development tool: numpy and ffmpeg required.
No recordings, third-party samples or existing song melodies are used.
"""
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

RATE = 22050
SECONDS = 72


def voice(midi, duration, kind):
    t = np.arange(int(duration * RATE), dtype=np.float64) / RATE
    f = 440 * 2 ** ((midi - 69) / 12)
    if kind == "pluck":
        sound = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.6 + h * .7)) / h ** 1.8 for h in range(1, 7))
        env = np.minimum(t / .008, 1) * np.minimum((duration - t) / .12, 1)
    elif kind == "flute":
        phase = 2 * np.pi * f * t + .035 * np.sin(2 * np.pi * 5.2 * t)
        sound = np.sin(phase) + .12 * np.sin(2 * phase) + .035 * np.sin(3 * phase)
        env = np.minimum(t / .2, 1) * np.minimum((duration - t) / .3, 1)
    elif kind == "pad":
        sound = (np.sin(2 * np.pi * f * .999 * t) + np.sin(2 * np.pi * f * 1.001 * t)) * .5
        env = np.minimum(t / .7, 1) * np.minimum((duration - t) / .8, 1)
    else:
        sound = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1 + h * .45)) / h ** 2.4 for h in range(1, 5))
        env = np.minimum(t / .012, 1) * np.minimum((duration - t) / .15, 1)
    return sound * np.maximum(env, 0)


def make(style, destination):
    samples = np.zeros((SECONDS * RATE, 2), dtype=np.float64)
    beat = {'redwhite': .78, 'floral': 1.0, 'gold': .9}[style]
    def note(start, midi, length, kind, level, pan=0):
        begin = int(start * RATE)
        sig = voice(midi, length, kind)
        size = min(len(sig), len(samples) - begin)
        if size <= 0: return
        left, right = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        samples[begin:begin+size, 0] += sig[:size] * level * left
        samples[begin:begin+size, 1] += sig[:size] * level * right
    motifs = {
        "redwhite": [[72, 76, 79, 76, 74, 72, 69, 72], [74, 76, 79, 81, 79, 76, 74, 72]],
        "floral": [[76, 79, 81, 79, 76, 74, 72, 69], [74, 76, 79, 76, 74, 72, 69, 72]],
        "gold": [[72, 74, 76, 79, 76, 74, 72, 67], [69, 72, 74, 76, 79, 76, 74, 72]],
    }
    chords = [[48, 55, 60, 64], [45, 52, 57, 60], [53, 60, 65, 69], [55, 62, 67, 71]]
    for bar in range(int(SECONDS / (beat * 4)) + 1):
        start = .2 + bar * beat * 4
        chord = chords[(bar // 2) % 4]
        for idx, pitch in enumerate(chord):
            note(start + idx * beat, pitch, 2.8, "piano", .10, -.25)
            if style == "gold": note(start, pitch + 12, beat * 4.6, "pad", .025, .3)
        motif = motifs[style][(bar // 2) % 2]
        for k in range(4):
            pitch = motif[(bar % 2) * 4 + k]
            kind = "flute" if style == "floral" else "pluck" if style == "redwhite" else "piano"
            phrasing = .84 + .08 * (k % 3)
            note(start + k * beat, pitch, 1.55 if kind == "flute" else 2.2, kind, .12 * phrasing, .18)
            if style == "redwhite" and k in (1, 3): note(start + k * beat + beat * .5, pitch - 12, 1.5, "pluck", .045, -.35)
    # Short stereo reflections and gentle start/end envelopes support quiet looping.
    dry = samples.copy()
    for delay, gain in ((.071, .10), (.13, .08), (.23, .06), (.37, .035), (.53, .02)):
        offset = int(delay * RATE)
        samples[offset:] += dry[:-offset, ::-1] * gain
    fade = np.ones(len(samples))
    fade[:2*RATE] = np.linspace(0, 1, 2*RATE)
    fade[-3*RATE:] = np.linspace(1, 0, 3*RATE)
    samples *= fade[:, None]
    samples /= max(np.max(np.abs(samples)), .001)
    pcm = (samples * .82 * 32767).astype('<i2')
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / 'score.wav'
        with wave.open(str(wav_path), 'wb') as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(RATE); f.writeframes(pcm.tobytes())
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav_path), '-af', 'loudnorm=I=-20:TP=-1.5:LRA=8', '-ar', '44100', '-codec:a', 'libmp3lame', '-b:a', '128k', str(destination)], check=True)


if __name__ == '__main__':
    directory = Path(__file__).resolve().parents[1] / 'assets' / 'music'
    directory.mkdir(exist_ok=True)
    for style in ('redwhite', 'floral', 'gold'):
        target = directory / f'{style}.mp3'
        make(style, target)
        print(style, target.stat().st_size)
