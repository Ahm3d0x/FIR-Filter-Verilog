"""
FIR Audio Test Tool - Q1.15 Fixed-Point Arithmetic and Hex Utilities.
Provides bit-exact conversions between floating-point [-1.0, 1.0)
and signed 16-bit Q1.15 two's complement hex representations.
"""

import numpy as np
from typing import List, Union

Q15_SCALE = 32768.0  # 2^15
INT16_MIN = -32768
INT16_MAX = 32767


def float_to_q15(audio_float: np.ndarray, clip: bool = True) -> np.ndarray:
    """
    Convert floating-point audio [-1.0, 1.0] to signed 16-bit Q1.15 integers.
    """
    scaled = audio_float * Q15_SCALE
    if clip:
        scaled = np.clip(scaled, INT16_MIN, INT16_MAX)
    return np.round(scaled).astype(np.int16)


def q15_to_float(audio_int16: np.ndarray) -> np.ndarray:
    """
    Convert signed 16-bit Q1.15 integers back to floating point [-1.0, 1.0).
    """
    return audio_int16.astype(np.float32) / Q15_SCALE


def int16_to_hex(val: int) -> str:
    """
    Convert signed 16-bit integer to 4-character uppercase two's complement hex string.
    """
    unsigned_val = val & 0xFFFF
    return f"{unsigned_val:04X}"


def hex_to_int16(hex_str: str) -> int:
    """
    Convert 4-character two's complement hex string to signed 16-bit integer.
    """
    val = int(hex_str.strip(), 16) & 0xFFFF
    if val >= 0x8000:
        val -= 0x10000
    return val


def export_hex_file(filepath: str, audio_int16: Union[np.ndarray, List[int]]) -> int:
    """
    Save signed 16-bit integers to a text file with one 4-digit hex value per line.
    Compatible with Verilog $readmemh.
    """
    with open(filepath, 'w') as f:
        for sample in audio_int16:
            f.write(int16_to_hex(int(sample)) + '\n')
    return len(audio_int16)


def import_hex_file(filepath: str) -> np.ndarray:
    """
    Read 4-digit two's complement hex values from a file into a signed int16 numpy array.
    Compatible with Verilog $fwrite / $readmemh format.
    """
    samples = []
    with open(filepath, 'r') as f:
        for line in f:
            clean = line.strip()
            if clean and not clean.startswith('//') and not clean.startswith('#'):
                token = clean.split()[0]
                samples.append(hex_to_int16(token))
    return np.array(samples, dtype=np.int16)
