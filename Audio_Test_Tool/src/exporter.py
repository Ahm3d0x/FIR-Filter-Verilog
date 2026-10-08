"""
FIR Audio Test Tool - Comprehensive Exporter Module.
Exports audio in multiple engineering formats:
1. Audio: 16-bit PCM WAV (48 kHz Mono)
2. Hardware Data: 4-digit Q1.15 Two's Complement HEX ($readmemh compatible)
3. Tabular Data: CSV with [sample_index, time_seconds, q15_int, hex_value, float_amplitude]
4. Raw Decimal Data: Signed 16-bit integer TXT
"""

import os
import csv
import numpy as np
from Audio_Test_Tool.src.q15 import float_to_q15, int16_to_hex, export_hex_file
from Audio_Test_Tool.src.audio_io import save_audio


def export_signal_bundle(signal_float: np.ndarray,
                         base_name: str,
                         output_dir: str,
                         fs: int = 48000) -> dict:
    """
    Export a signal into WAV, HEX, CSV, and TXT files.
    
    Args:
        signal_float: 1D float array [-1.0, 1.0].
        base_name: Base filename (e.g. 'original', 'noisy', 'filtered').
        output_dir: Directory where files will be created.
        fs: Sampling rate (48000 Hz).
        
    Returns:
        dict with paths of created files.
    """
    os.makedirs(output_dir, exist_ok=True)
    n_samples = len(signal_float)

    # 1. Convert to Q1.15 signed integers
    q15_ints = float_to_q15(signal_float, clip=True)

    # File paths
    wav_path = os.path.join(output_dir, f"{base_name}.wav")
    hex_path = os.path.join(output_dir, f"{base_name}.hex")
    csv_path = os.path.join(output_dir, f"{base_name}.csv")
    txt_path = os.path.join(output_dir, f"{base_name}_int16.txt")

    # 1. Save WAV Audio
    save_audio(wav_path, signal_float, fs=fs)

    # 2. Save Verilog $readmemh HEX
    export_hex_file(hex_path, q15_ints)

    # 3. Save Raw Signed Decimal TXT
    with open(txt_path, 'w') as f_txt:
        for val in q15_ints:
            f_txt.write(f"{int(val)}\n")

    # 4. Save Comprehensive CSV Data
    with open(csv_path, 'w', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["sample_index", "time_seconds", "q15_integer", "hex_value", "normalized_float"])

        # Write lines
        time_step = 1.0 / fs
        for idx in range(n_samples):
            t_sec = idx * time_step
            q_val = int(q15_ints[idx])
            h_val = int16_to_hex(q_val)
            flt_val = float(signal_float[idx])
            writer.writerow([idx, f"{t_sec:.6f}", q_val, h_val, f"{flt_val:.6f}"])

    return {
        "wav": wav_path,
        "hex": hex_path,
        "csv": csv_path,
        "txt": txt_path,
        "sample_count": n_samples
    }


def export_complete_project_package(original: np.ndarray,
                                    noisy: np.ndarray,
                                    filtered: np.ndarray,
                                    target_dir: str,
                                    fs: int = 48000) -> dict:
    """
    Export all stages (Original, Noisy, Filtered) into a designated folder.
    """
    os.makedirs(target_dir, exist_ok=True)
    results = {}

    if original is not None and len(original) > 0:
        results["original"] = export_signal_bundle(original, "original", target_dir, fs=fs)

    if noisy is not None and len(noisy) > 0:
        results["noisy"] = export_signal_bundle(noisy, "noisy", target_dir, fs=fs)

    if filtered is not None and len(filtered) > 0:
        results["filtered"] = export_signal_bundle(filtered, "filtered", target_dir, fs=fs)

    return results
