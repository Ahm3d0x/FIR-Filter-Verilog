"""
FIR Audio Test Tool - Bit-Exact Golden Model.
Replicates the exact fixed-point Direct-Form FIR RTL implementation:
- 16 Taps Q1.15 signed coefficients
- 16 Multipliers with Q2.30 products
- 36-bit signed Q6.30 accumulator tree
- Truncation to Q1.15 via acc[30:15] (arithmetic right-shift by 15)
"""

import numpy as np

COEFFS_Q15 = np.array([
    -242,  -691, -1095,  -842,
     631,  3307,  6324,  8338,
    8338,  6324,  3307,   631,
    -842, -1095,  -691,  -242
], dtype=np.int32)

NUM_TAPS = len(COEFFS_Q15)


def compute_golden_fir(stimulus_int16: np.ndarray) -> np.ndarray:
    """
    Run bit-exact simulation of the RTL FIR filter.
    """
    n_samples = len(stimulus_int16)
    stim = stimulus_int16.astype(np.int64)
    y_golden = np.zeros(n_samples, dtype=np.int16)

    delay_line = np.zeros(NUM_TAPS, dtype=np.int64)

    for i in range(n_samples):
        delay_line[1:] = delay_line[:-1]
        delay_line[0] = stim[i]

        acc_36 = np.sum(delay_line * COEFFS_Q15)
        y_val = int(acc_36 >> 15)
        y_signed = ((y_val + 32768) % 65536) - 32768
        y_golden[i] = y_signed

    return y_golden


def compare_rtl_vs_golden(rtl_samples: np.ndarray,
                          golden_samples: np.ndarray) -> dict:
    """
    Compare RTL output samples against Golden Model sample-by-sample.
    """
    min_len = min(len(rtl_samples), len(golden_samples))
    if min_len == 0:
        return {
            "total_samples": 0,
            "mismatches": 0,
            "max_error": 0,
            "match_percentage": 0.0,
            "status": "EMPTY"
        }

    rtl = rtl_samples[:min_len]
    gold = golden_samples[:min_len]

    diff = np.abs(rtl.astype(np.int32) - gold.astype(np.int32))
    mismatches = int(np.sum(diff != 0))
    max_error = int(np.max(diff))
    match_pct = 100.0 * (1.0 - mismatches / min_len)

    return {
        "total_samples": min_len,
        "mismatches": mismatches,
        "max_error": max_error,
        "match_percentage": match_pct,
        "status": "PASS" if mismatches == 0 else "FAIL"
    }
