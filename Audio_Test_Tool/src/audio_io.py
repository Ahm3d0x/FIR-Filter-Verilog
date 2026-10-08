"""
FIR Audio Test Tool - Audio I/O, Microphone Recording, and Playback Module.
Supports:
- Real-time live microphone recording with instant Stop & Keep functionality
- Sample rate conversion to 48 kHz mono
- Live audio playback with sounddevice / winsound
- Peak normalization and DC bias removal
"""

import os
import math
import time
import threading
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

TARGET_FS = 48000


def load_audio(filepath: str, target_fs: int = TARGET_FS) -> tuple[np.ndarray, int]:
    """
    Load a WAV audio file, downmix to mono, resample to 48 kHz, and normalize.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    fs, data = wavfile.read(filepath)

    if data.dtype == np.int16:
        audio = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        audio = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        audio = (data.astype(np.float32) - 128.0) / 128.0
    elif np.issubdtype(data.dtype, np.floating):
        audio = data.astype(np.float32)
    else:
        audio = data.astype(np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val

    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if fs != target_fs:
        gcd = math.gcd(fs, target_fs)
        up = target_fs // gcd
        down = fs // gcd
        audio = resample_poly(audio, up, down).astype(np.float32)

    audio = audio - np.mean(audio)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.92

    return audio.astype(np.float32), target_fs


def save_audio(filepath: str, audio: np.ndarray, fs: int = TARGET_FS) -> None:
    """
    Save 1D audio array to a 16-bit PCM WAV file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    if np.issubdtype(audio.dtype, np.floating):
        clipped = np.clip(audio, -1.0, 1.0)
        int16_data = np.round(clipped * 32767.0).astype(np.int16)
    elif audio.dtype == np.int16:
        int16_data = audio
    else:
        int16_data = np.clip(audio, -32768, 32767).astype(np.int16)

    wavfile.write(filepath, fs, int16_data)


def record_microphone(max_duration_sec: float = 20.0,
                      fs: int = TARGET_FS,
                      stop_event: threading.Event = None,
                      progress_callback=None) -> np.ndarray:
    """
    Record live audio from physical microphone with instant Stop capability.
    
    Args:
        max_duration_sec: Maximum duration in seconds.
        fs: Sampling rate (48000 Hz).
        stop_event: threading.Event object. When set(), stops recording immediately.
        progress_callback: Callable(elapsed, max_sec, remaining) for UI updates.
        
    Returns:
        1D np.float32 array containing recorded speech normalized cleanly.
    """
    import sounddevice as sd

    chunk_size = int(fs * 0.1)  # 100 ms chunks for high responsiveness
    frames = []

    start_time = time.time()
    print(f"\n[MIC] 🎙️ Microphone active (Max: {max_duration_sec:.0f}s). Speak now...")

    with sd.InputStream(samplerate=fs, channels=1, dtype='float32') as stream:
        while True:
            chunk, overflowed = stream.read(chunk_size)
            frames.append(chunk)

            elapsed = time.time() - start_time
            remaining = max(0.0, max_duration_sec - elapsed)

            if progress_callback:
                progress_callback(elapsed, max_duration_sec, remaining)

            if stop_event and stop_event.is_set():
                print(f"\n[MIC] ⏹ Stop requested by user at {elapsed:.2f}s!")
                break

            if elapsed >= max_duration_sec:
                print(f"\n[MIC] ✔ Reached maximum duration of {max_duration_sec:.1f}s.")
                break

    if len(frames) == 0:
        return np.zeros(fs, dtype=np.float32)

    audio = np.concatenate(frames).flatten()

    # Post-process: remove DC offset and normalize gain
    audio = audio - np.mean(audio)
    peak = np.max(np.abs(audio))

    if peak > 0.002:
        gain = 0.90 / peak
        gain = min(gain, 40.0)  # avoid blowing up silence
        audio = (audio * gain).astype(np.float32)
    elif peak > 0:
        audio = (audio / peak * 0.50).astype(np.float32)

    return audio


def generate_synthetic_speech(duration_sec: float = 2.5, fs: int = TARGET_FS) -> np.ndarray:
    """
    Generate synthetic test signal for verification without a microphone.
    """
    t = np.linspace(0, duration_sec, int(fs * duration_sec), endpoint=False)
    f0 = 220.0 + 5.0 * np.sin(2 * np.pi * 5.0 * t)
    phase = 2 * np.pi * np.cumsum(f0) / fs

    signal = (0.60 * np.sin(phase) +
              0.40 * np.sin(2 * phase) +
              0.30 * np.sin(3 * phase) +
              0.25 * np.sin(4 * phase) +
              0.15 * np.sin(6 * phase) +
              0.10 * np.sin(10 * phase))

    envelope = np.power(0.5 * (1.0 + np.sin(2 * np.pi * 3.0 * t - np.pi/2)), 1.5)
    fade_len = int(0.05 * fs)
    envelope[:fade_len] *= np.linspace(0, 1, fade_len)
    envelope[-fade_len:] *= np.linspace(1, 0, fade_len)

    audio = signal * envelope
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = (audio / peak * 0.90).astype(np.float32)

    return audio


def play_audio(audio_data: np.ndarray, fs: int = TARGET_FS) -> None:
    """
    Start audio playback asynchronously using sounddevice.
    """
    import sounddevice as sd
    sd.play(audio_data, samplerate=fs)


def stop_audio() -> None:
    """
    Immediately stop any ongoing sound playback.
    """
    import sounddevice as sd
    sd.stop()
