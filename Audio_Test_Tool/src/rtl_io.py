"""
FIR Audio Test Tool - RTL Hex File I/O and WAV Decoder.
"""

import os
import numpy as np
from Audio_Test_Tool.src.q15 import float_to_q15, q15_to_float, export_hex_file, import_hex_file
from Audio_Test_Tool.src.audio_io import save_audio
from Audio_Test_Tool.src.golden_model import compute_golden_fir


def prepare_rtl_stimulus(audio_float: np.ndarray,
                         hex_path: str,
                         golden_hex_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert float audio to Q1.15, compute golden reference, and export both to hex files.
    """
    os.makedirs(os.path.dirname(os.path.abspath(hex_path)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(golden_hex_path)), exist_ok=True)

    stimulus_q15 = float_to_q15(audio_float, clip=True)
    export_hex_file(hex_path, stimulus_q15)

    golden_q15 = compute_golden_fir(stimulus_q15)
    export_hex_file(golden_hex_path, golden_q15)

    return stimulus_q15, golden_q15


def decode_rtl_output_to_wav(filtered_hex_path: str,
                             output_wav_path: str,
                             fs: int = 48000) -> np.ndarray:
    """
    Read the RTL-filtered hex dump produced by Verilog and save as a WAV file.
    """
    if not os.path.exists(filtered_hex_path):
        raise FileNotFoundError(f"RTL output file not found: {filtered_hex_path}")

    filtered_q15 = import_hex_file(filtered_hex_path)
    if len(filtered_q15) == 0:
        raise ValueError(f"RTL output file is empty: {filtered_hex_path}")

    filtered_float = q15_to_float(filtered_q15)
    save_audio(output_wav_path, filtered_float, fs=fs)

    return filtered_float
