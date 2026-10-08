"""
FIR Audio Test Tool - Configurable Noise Generator Module.
"""

import numpy as np

DEFAULT_FS = 48000


def add_single_tone(signal: np.ndarray,
                    tone_freq: float = 18000.0,
                    amplitude: float = 0.30,
                    fs: int = DEFAULT_FS) -> tuple[np.ndarray, np.ndarray]:
    """
    Add single continuous high-frequency sinusoidal tone in the stopband.
    """
    n_samples = len(signal)
    t = np.arange(n_samples) / fs
    noise = amplitude * np.sin(2.0 * np.pi * tone_freq * t).astype(np.float32)
    noisy = signal + noise
    return _safe_scale(noisy), noise


def add_dual_tone(signal: np.ndarray,
                  freq1: float = 12000.0,
                  freq2: float = 18000.0,
                  amp1: float = 0.20,
                  amp2: float = 0.20,
                  fs: int = DEFAULT_FS) -> tuple[np.ndarray, np.ndarray]:
    """
    Add two separate tones in the FIR stopband (e.g. 12 kHz + 18 kHz).
    """
    n_samples = len(signal)
    t = np.arange(n_samples) / fs
    tone1 = amp1 * np.sin(2.0 * np.pi * freq1 * t).astype(np.float32)
    tone2 = amp2 * np.sin(2.0 * np.pi * freq2 * t).astype(np.float32)
    noise = tone1 + tone2
    noisy = signal + noise
    return _safe_scale(noisy), noise


def add_white_gaussian_noise(signal: np.ndarray,
                             target_snr_db: float = 12.0) -> tuple[np.ndarray, np.ndarray]:
    """
    Add zero-mean White Gaussian Noise (WGN) calibrated to match the target SNR.
    """
    signal_power = np.mean(signal ** 2)
    if signal_power <= 0:
        signal_power = 1e-6

    snr_linear = 10.0 ** (target_snr_db / 10.0)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power)

    noise = np.random.normal(0.0, noise_std, size=signal.shape).astype(np.float32)
    noisy = signal + noise
    return _safe_scale(noisy), noise


def _safe_scale(noisy_signal: np.ndarray, headroom: float = 0.96) -> np.ndarray:
    """
    Scale if peak exceeds headroom to guarantee that Q1.15
    fixed-point conversion will not cause overflow distortion.
    """
    peak = np.max(np.abs(noisy_signal))
    if peak > headroom:
        scale_factor = headroom / peak
        return (noisy_signal * scale_factor).astype(np.float32)
    return noisy_signal.astype(np.float32)
