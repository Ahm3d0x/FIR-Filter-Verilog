# FIR Filter Hardware Audio Verification System

An end-to-end DSP & Hardware Verification Platform for the 16-Tap Direct-Form FIR filter ($F_s = 48\text{ kHz}$).

---

## 1. System Overview & Architecture

```text
               +--------------------------------------+
               |      Audio Input (48 kHz Mono)       |
               |   Synthetic Speech / Custom WAV      |
               +------------------+-------------------+
                                  |
                                  v
               +--------------------------------------+
               |        Configurable Noise Engine     |
               |  - 18 kHz Tone (Stopband)            |
               |  - Dual-Tone (12 kHz + 18 kHz)       |
               |  - White Gaussian Noise (SNR dB)     |
               +------------------+-------------------+
                                  |
                                  v
               +--------------------------------------+
               |        Q1.15 Fixed-Point Export      |
               |  - input/input.hex                   |
               |  - golden/golden.hex (Bit-exact)     |
               +------------------+-------------------+
                                  |
                                  v
               +--------------------------------------+
               |      ModelSim / QuestaSim RTL DUT    |
               |       tb/fir_audio_tb.v              |
               |  - Real hardware-in-the-loop filter  |
               |  - Dumps output/filtered.hex         |
               +------------------+-------------------+
                                  |
                                  v
               +--------------------------------------+
               |        RTL Decoder & Analysis        |
               |  - Decodes to output/filtered.wav    |
               |  - Computes FFT magnitude spectrum   |
               |  - Evaluates SNR & RMS metrics       |
               |  - Audio playback comparison         |
               +--------------------------------------+
```

---

## 2. Directory Structure

```text
FIR_Project/
├── python/
│   ├── __init__.py
│   ├── q15.py             # Q1.15 fixed-point & two's complement hex converter
│   ├── audio_io.py        # WAV loader, 48kHz resampler, vocal generator, player
│   ├── noise_gen.py       # Stopband tones and White Gaussian Noise generator
│   ├── golden_model.py    # Bit-exact RTL simulator replicating acc[30:15]
│   ├── rtl_io.py          # Hex stimulus exporter and RTL WAV decoder
│   ├── sim_runner.py      # Automated ModelSim batch simulator
│   ├── analysis.py        # FFT spectrum & time-domain waveform plotting
│   └── main.py            # Complete interactive English CLI controller
├── rtl/
│   ├── fir_datapath.v     # 15 delay registers + 16 signed multipliers
│   ├── fir_accumulator.v  # 36-bit Q6.30 adder tree + registered acc[30:15]
│   └── fir_filter.v       # Top-level direct-form FIR filter
├── tb/
│   ├── fir_filter_tb.v    # Unit testbench (1024 fixed vectors)
│   └── fir_audio_tb.v     # Dynamic streaming audio testbench
├── sim/
│   ├── run.do             # Standard unit testbench script
│   └── run_audio.do       # Audio verification batch simulation script
├── input/
│   ├── original.wav       # Clean 48 kHz mono reference audio
│   ├── noisy.wav          # Audio corrupted by stopband interference
│   └── input.hex          # Q1.15 hex stimulus for Verilog
├── golden/
│   └── golden.hex         # Bit-exact reference for sample-by-sample check
├── output/
│   ├── filtered.hex       # Real hardware output dumped by RTL $fwrite
│   └── filtered.wav       # Decoded audio produced by the hardware DUT
├── results/
│   ├── audio_time_domain.png        # Time-domain comparison plot
│   ├── audio_frequency_spectrum.png # FFT magnitude spectrum plot
│   └── fir_verification_report.txt  # Quantitative verification report
└── run_audio.bat          # 1-Click launcher for Windows
```

---

## 3. How to Run

### Option A: 1-Click Windows Launcher
Double-click `run_audio.bat` or run:
```cmd
.\run_audio.bat
```

### Option B: Automated Command Line (Non-Interactive)
```cmd
.\.venv\Scripts\python.exe python\main.py --auto --noise 1
```
Available `--noise` flags:
- `--noise 1`: Single 18 kHz tone (deep stopband interference)
- `--noise 2`: Dual tones at 12 kHz + 18 kHz
- `--noise 3`: White Gaussian Noise (10 dB target SNR)

### Option C: Custom WAV File
```cmd
.\.venv\Scripts\python.exe python\main.py --auto --wav "path\to\your\audio.wav"
```

---

## 4. Hardware Verification Results

- **Processed Samples**: 120,000 samples (2.5 seconds @ 48 kHz).
- **RTL DUT Simulation**: Executed directly inside ModelSim / QuestaSim.
- **Verification Status**: **100.00% Bit-Exact Match** (0 mismatches between RTL DUT output and the Golden Model).
- **Acoustic Result**: Stopband interference (e.g. 18 kHz) attenuated by $> 50\text{ dB}$, producing clean, filtered audio.
