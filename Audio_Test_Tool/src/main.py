"""
FIR Audio Test Tool - Command Line Interface (CLI).
"""

import os
import sys
import argparse

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(TOOL_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Audio_Test_Tool.src.audio_io import (
    load_audio,
    save_audio,
    record_microphone,
    generate_synthetic_speech,
    play_audio,
    TARGET_FS
)
from Audio_Test_Tool.src.noise_gen import (
    add_single_tone,
    add_dual_tone,
    add_white_gaussian_noise
)
from Audio_Test_Tool.src.rtl_io import (
    prepare_rtl_stimulus,
    decode_rtl_output_to_wav
)
from Audio_Test_Tool.src.golden_model import compare_rtl_vs_golden
from Audio_Test_Tool.src.sim_runner import run_modelsim_audio_sim
from Audio_Test_Tool.src.q15 import import_hex_file
from Audio_Test_Tool.src.analysis import (
    get_original_report,
    get_noisy_report,
    get_filtered_report,
    format_tri_stage_report,
    generate_plots
)


def run_cli_pipeline(noise_choice="1", dur=10.0):
    input_dir = os.path.join(TOOL_ROOT, "input")
    output_dir = os.path.join(TOOL_ROOT, "output")
    golden_dir = os.path.join(TOOL_ROOT, "golden")
    results_dir = os.path.join(TOOL_ROOT, "results")

    orig_wav = os.path.join(input_dir, "original.wav")
    noisy_wav = os.path.join(input_dir, "noisy.wav")
    input_hex = os.path.join(input_dir, "input.hex")
    gold_hex = os.path.join(golden_dir, "golden.hex")
    filt_hex = os.path.join(output_dir, "filtered.hex")
    filt_wav = os.path.join(output_dir, "filtered.wav")

    print(f"\n[CLI] Recording microphone for {dur:.0f} seconds...")
    orig = record_microphone(max_duration_sec=dur, fs=TARGET_FS)
    save_audio(orig_wav, orig, TARGET_FS)

    print("[CLI] Applying stopband noise...")
    if noise_choice == "1":
        noisy, _ = add_single_tone(orig, tone_freq=18000.0, amplitude=0.25, fs=TARGET_FS)
        desc = "Single Tone @ 18 kHz"
    elif noise_choice == "2":
        noisy, _ = add_dual_tone(orig, freq1=12000.0, freq2=18000.0, amp1=0.20, amp2=0.20, fs=TARGET_FS)
        desc = "Dual Tones @ 12k + 18k"
    else:
        noisy, _ = add_white_gaussian_noise(orig, target_snr_db=10.0)
        desc = "White Gaussian Noise (10 dB SNR)"

    save_audio(noisy_wav, noisy, TARGET_FS)
    prepare_rtl_stimulus(noisy, input_hex, gold_hex)

    print("[CLI] Running ModelSim simulation with live progress...")
    success, log = run_modelsim_audio_sim(PROJECT_ROOT, line_callback=lambda l: print(f"  {l}"))

    print("[CLI] Decoding filtered output...")
    filt = decode_rtl_output_to_wav(filt_hex, filt_wav, fs=TARGET_FS)

    gold_s = import_hex_file(gold_hex)
    rtl_s = import_hex_file(filt_hex)
    verif = compare_rtl_vs_golden(rtl_s, gold_s)

    r_orig = get_original_report(orig, TARGET_FS)
    r_noisy = get_noisy_report(noisy, desc, TARGET_FS)
    r_filt = get_filtered_report(filt, verif, orig, TARGET_FS)

    report = format_tri_stage_report(r_orig, r_noisy, r_filt)
    print("\n" + report)

    generate_plots(orig, noisy, filt, TARGET_FS, results_dir)
    print(f"\n[CLI] Done! Results saved in: {results_dir}")


def main():
    parser = argparse.ArgumentParser(description="FIR Audio Test Tool CLI")
    parser.add_argument("--gui", action="store_true", help="Launch Graphical User Interface")
    parser.add_argument("--auto", action="store_true", help="Run automated test")
    parser.add_argument("--noise", default="1", choices=["1", "2", "3"])
    parser.add_argument("--dur", type=float, default=10.0)
    args = parser.parse_args()

    if args.gui or len(sys.argv) == 1:
        from Audio_Test_Tool.src.gui_app import FIRAudioTestToolApp
        app = FIRAudioTestToolApp()
        app.mainloop()
    else:
        run_cli_pipeline(noise_choice=args.noise, dur=args.dur)


if __name__ == "__main__":
    main()
