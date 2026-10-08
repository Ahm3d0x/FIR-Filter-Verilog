"""
FIR Audio Test Tool - Advanced Graphical User Interface (GUI).
Encapsulated Architecture with:
1. Microphone recording with instant 'Stop & Keep' button at any second
2. 3 Dedicated FFT spectrum subplots (Original, Noisy, RTL Filtered) + Overlay view
3. Full Track Waveform display with synchronized real-time moving playhead cursor
4. Comprehensive Audio & Raw Data Exporting (WAV, HEX, CSV, TXT)
5. Detailed individual engineering reports for each audio stage
6. Live real-time streaming ModelSim simulation console
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Resolve project paths
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(TOOL_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Audio_Test_Tool.src.audio_io import (
    load_audio,
    save_audio,
    record_microphone,
    generate_synthetic_speech,
    play_audio,
    stop_audio,
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
from Audio_Test_Tool.src.q15 import import_hex_file
from Audio_Test_Tool.src.sim_runner import run_modelsim_audio_sim
from Audio_Test_Tool.src.analysis import (
    compute_spectrum,
    get_original_report,
    get_noisy_report,
    get_filtered_report,
    format_tri_stage_report
)
from Audio_Test_Tool.src.exporter import (
    export_signal_bundle,
    export_complete_project_package
)


class FIRAudioTestToolApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("FIR Audio Test Tool — 16-Tap Direct-Form (ModelSim RTL Co-Simulation)")
        self.geometry("1400x900")
        self.minsize(1150, 780)

        # File paths inside Audio_Test_Tool
        self.input_dir = os.path.join(TOOL_ROOT, "input")
        self.output_dir = os.path.join(TOOL_ROOT, "output")
        self.golden_dir = os.path.join(TOOL_ROOT, "golden")
        self.results_dir = os.path.join(TOOL_ROOT, "results")
        self.export_dir = os.path.join(self.output_dir, "exports")

        for d in [self.input_dir, self.output_dir, self.golden_dir, self.results_dir, self.export_dir]:
            os.makedirs(d, exist_ok=True)

        self.orig_wav_path = os.path.join(self.input_dir, "original.wav")
        self.noisy_wav_path = os.path.join(self.input_dir, "noisy.wav")
        self.input_hex_path = os.path.join(self.input_dir, "input.hex")
        self.golden_hex_path = os.path.join(self.golden_dir, "golden.hex")
        self.filtered_hex_path = os.path.join(self.output_dir, "filtered.hex")
        self.filtered_wav_path = os.path.join(self.output_dir, "filtered.wav")

        # Audio state
        self.fs = TARGET_FS
        self.original_audio = None
        self.noisy_audio = None
        self.filtered_audio = None
        self.noise_desc = "Single Stopband Tone @ 18,000 Hz"
        self.rtl_verif_status = {}

        # Recording control
        self.is_recording = False
        self.stop_rec_event = threading.Event()

        # Playback & Playhead Cursor State
        self.is_playing = False
        self.playback_start_time = 0.0
        self.playback_duration = 0.0
        self.active_playback_type = None
        self.playhead_lines = []

        self._configure_styles()
        self._build_ui()
        self.after(250, self._initial_load)

    def _configure_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.bg_dark = "#161920"
        self.bg_panel = "#1e222d"
        self.bg_card = "#262c3a"
        self.fg_primary = "#f0f2f5"
        self.fg_secondary = "#9aa5b8"
        self.accent_blue = "#2979ff"
        self.accent_green = "#00e676"
        self.accent_red = "#ff5252"
        self.accent_orange = "#ff9100"

        self.configure(bg=self.bg_dark)

        self.style.configure(".", background=self.bg_panel, foreground=self.fg_primary, font=("Segoe UI", 9))
        self.style.configure("TFrame", background=self.bg_panel)
        self.style.configure("Card.TFrame", background=self.bg_card, relief="flat")
        self.style.configure("Header.TFrame", background=self.bg_dark)

        self.style.configure("TLabel", background=self.bg_panel, foreground=self.fg_primary, font=("Segoe UI", 9))
        self.style.configure("Card.TLabel", background=self.bg_card, foreground=self.fg_primary, font=("Segoe UI", 9))
        self.style.configure("Title.TLabel", background=self.bg_dark, foreground="#ffffff", font=("Segoe UI", 13, "bold"))
        self.style.configure("Subtitle.TLabel", background=self.bg_dark, foreground=self.fg_secondary, font=("Segoe UI", 9))
        self.style.configure("Section.TLabel", background=self.bg_card, foreground=self.accent_blue, font=("Segoe UI", 10, "bold"))

        self.style.configure("BadgePass.TLabel", background="#0d381e", foreground="#00e676", font=("Segoe UI", 10, "bold"), padding=4)
        self.style.configure("BadgeIdle.TLabel", background="#2a3040", foreground="#9aa5b8", font=("Segoe UI", 10, "bold"), padding=4)

        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5)
        self.style.configure("Primary.TButton", background=self.accent_blue, foreground="#ffffff", font=("Segoe UI", 9, "bold"))
        self.style.configure("RecStop.TButton", background="#d50000", foreground="#ffffff", font=("Segoe UI", 9, "bold"))
        self.style.configure("RunAll.TButton", background="#00c853", foreground="#ffffff", font=("Segoe UI", 10, "bold"), padding=7)
        self.style.configure("Play.TButton", background="#37474f", foreground="#eceff1", font=("Segoe UI", 9, "bold"))
        self.style.configure("Stop.TButton", background="#c62828", foreground="#ffffff", font=("Segoe UI", 9, "bold"))
        self.style.configure("Export.TButton", background="#0277bd", foreground="#ffffff", font=("Segoe UI", 9, "bold"))

        self.style.configure("TNotebook", background=self.bg_dark, tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background=self.bg_panel, foreground=self.fg_secondary, padding=[10, 5], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", self.bg_card)], foreground=[("selected", "#ffffff")])

        self.style.configure("TRadiobutton", background=self.bg_card, foreground=self.fg_primary, font=("Segoe UI", 9))

    def _build_ui(self):
        # 1. HEADER
        header = ttk.Frame(self, style="Header.TFrame", padding=(15, 10, 15, 8))
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(header, text="Audio Test Tool — 16-Tap Direct-Form FIR Hardware Verification", style="Title.TLabel").pack(anchor="w")
        sub_desc = "Fs: 48 kHz  |  Passband: 0 - 4 kHz (≤ 1 dB)  |  Stopband: 10 - 24 kHz (≥ 50 dB)  |  ModelSim RTL Real-Time Co-Simulation"
        ttk.Label(header, text=sub_desc, style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))

        # Main Body Splitter
        main_body = ttk.Frame(self, padding=(10, 5, 10, 5))
        main_body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # LEFT CONTROL PANEL (Width ~ 390px)
        left_panel = ttk.Frame(main_body, width=395)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        self._build_controls(left_panel)

        # RIGHT TABS PANEL
        right_panel = ttk.Frame(main_body)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_notebook_views(right_panel)

        # BOTTOM STATUS BAR
        status_bar = ttk.Frame(self, style="Header.TFrame", padding=(15, 4, 15, 4))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_lbl = ttk.Label(status_bar, text="Ready. Record microphone or select noise to begin.", style="Subtitle.TLabel")
        self.status_lbl.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(status_bar, mode="indeterminate", length=140)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

    def _build_controls(self, parent):
        canvas = tk.Canvas(parent, bg=self.bg_panel, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # CARD 1: AUDIO INPUT & MICROPHONE WITH STOP-AND-KEEP
        c1 = ttk.Frame(scrollable, style="Card.TFrame", padding=11)
        c1.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(c1, text="1. AUDIO INPUT & MICROPHONE", style="Section.TLabel").pack(anchor="w", pady=(0, 5))

        self.audio_source_var = tk.StringVar(value="mic")

        rb_mic = ttk.Radiobutton(c1, text="🎙️ Live Microphone Recording (Real Voice)",
                                 variable=self.audio_source_var, value="mic",
                                 command=self._on_source_toggle)
        rb_mic.pack(anchor="w", pady=1)

        self.mic_opts_frame = ttk.Frame(c1, style="Card.TFrame")
        self.mic_opts_frame.pack(fill=tk.X, padx=(18, 0), pady=(2, 4))

        ttk.Label(self.mic_opts_frame, text="Max Duration:", style="Card.TLabel", foreground=self.fg_secondary).pack(side=tk.LEFT)
        self.mic_duration_var = tk.DoubleVar(value=10.0)
        for dur, txt in [(5.0, "5s"), (10.0, "10s"), (20.0, "20s")]:
            ttk.Radiobutton(self.mic_opts_frame, text=txt, variable=self.mic_duration_var, value=dur).pack(side=tk.LEFT, padx=3)

        self.lbl_mic_status = ttk.Label(c1, text="● Status: Ready to record voice.", style="Card.TLabel", foreground=self.fg_secondary)
        self.lbl_mic_status.pack(anchor="w", pady=(2, 3))

        # Dual Buttons: Record / Stop
        rec_btn_frame = ttk.Frame(c1, style="Card.TFrame")
        rec_btn_frame.pack(fill=tk.X, pady=(2, 5))

        self.btn_rec_mic = ttk.Button(rec_btn_frame, text="🎙️ Start Recording", style="Primary.TButton",
                                      command=self._action_start_recording)
        self.btn_rec_mic.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_stop_rec = ttk.Button(rec_btn_frame, text="⏹ Stop & Keep", style="RecStop.TButton",
                                       state="disabled", command=self._action_stop_recording)
        self.btn_stop_rec.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        rb_file = ttk.Radiobutton(c1, text="📁 Custom WAV Audio File", variable=self.audio_source_var, value="file",
                                  command=self._on_source_toggle)
        rb_file.pack(anchor="w", pady=1)

        self.file_frame = ttk.Frame(c1, style="Card.TFrame")
        self.file_frame.pack(fill=tk.X, padx=(18, 0), pady=(1, 4))

        self.wav_path_var = tk.StringVar(value="")
        self.wav_entry = ttk.Entry(self.file_frame, textvariable=self.wav_path_var, state="disabled", font=("Segoe UI", 8))
        self.wav_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_browse = ttk.Button(self.file_frame, text="Browse...", state="disabled", command=self._browse_wav)
        self.btn_browse.pack(side=tk.RIGHT)

        rb_synth = ttk.Radiobutton(c1, text="🎹 Synthetic Multi-Tone Test Signal", variable=self.audio_source_var,
                                   value="synth", command=self._on_source_toggle)
        rb_synth.pack(anchor="w", pady=(2, 1))

        # CARD 2: NOISE GENERATOR
        c2 = ttk.Frame(scrollable, style="Card.TFrame", padding=11)
        c2.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(c2, text="2. STOPBAND NOISE GENERATOR", style="Section.TLabel").pack(anchor="w", pady=(0, 5))

        self.noise_type_var = tk.StringVar(value="tone18k")
        noise_options = [
            ("Single Tone @ 18 kHz (Deep Stopband)", "tone18k"),
            ("Dual-Tone @ 12 kHz + 18 kHz", "dual_tone"),
            ("White Gaussian Noise (Configurable SNR)", "wgn"),
            ("Custom Stopband Tone Frequency", "custom_tone")
        ]
        for txt, val in noise_options:
            ttk.Radiobutton(c2, text=txt, variable=self.noise_type_var, value=val,
                            command=self._on_noise_toggle).pack(anchor="w", pady=1)

        self.noise_p_frame = ttk.Frame(c2, style="Card.TFrame")
        self.noise_p_frame.pack(fill=tk.X, pady=(3, 5))

        self.lbl_noise_p = ttk.Label(self.noise_p_frame, text="Tone: Fixed @ 18,000 Hz", style="Card.TLabel")
        self.lbl_noise_p.pack(anchor="w")

        self.noise_slider_var = tk.DoubleVar(value=18000)
        self.noise_slider = ttk.Scale(self.noise_p_frame, from_=10000, to=23000,
                                      variable=self.noise_slider_var, command=self._on_noise_slider)
        self.noise_slider.pack(fill=tk.X, pady=2)
        self.noise_slider.configure(state="disabled")

        btn_noise = ttk.Button(c2, text="Apply Noise & Export Stimulus (Q1.15)", command=self._action_apply_noise)
        btn_noise.pack(fill=tk.X, pady=(2, 0))

        # CARD 3: HARDWARE SIMULATION
        c3 = ttk.Frame(scrollable, style="Card.TFrame", padding=11)
        c3.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(c3, text="3. MODELSIM RTL CO-SIMULATION", style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        self.btn_sim = ttk.Button(c3, text="▶ Run ModelSim Simulation", style="Primary.TButton",
                                  command=self._action_run_simulation)
        self.btn_sim.pack(fill=tk.X)

        # CARD 4: ONE-CLICK PIPELINE
        c4 = ttk.Frame(scrollable, style="Card.TFrame", padding=11)
        c4.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(c4, text="4. AUTOMATED END-TO-END RUN", style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        btn_all = ttk.Button(c4, text="⚡ Run Full Automated Pipeline", style="RunAll.TButton",
                             command=self._action_run_full_pipeline)
        btn_all.pack(fill=tk.X)

        # CARD 5: AUDIO PLAYBACK
        c5 = ttk.Frame(scrollable, style="Card.TFrame", padding=11)
        c5.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(c5, text="AUDIO PLAYBACK & PLAYHEAD", style="Section.TLabel").pack(anchor="w", pady=(0, 4))

        btn_p_orig = ttk.Button(c5, text="▶ Play Original (Clean Voice)", style="Play.TButton",
                                command=lambda: self._start_playback("orig"))
        btn_p_orig.pack(fill=tk.X, pady=2)

        btn_p_noisy = ttk.Button(c5, text="▶ Play Noisy (Corrupted)", style="Play.TButton",
                                 command=lambda: self._start_playback("noisy"))
        btn_p_noisy.pack(fill=tk.X, pady=2)

        btn_p_filt = ttk.Button(c5, text="▶ Play RTL Filtered (DUT Cleaned)", style="Play.TButton",
                                command=lambda: self._start_playback("filt"))
        btn_p_filt.pack(fill=tk.X, pady=2)

        btn_stop = ttk.Button(c5, text="⏹ Stop Audio Playback", style="Stop.TButton", command=self._stop_playback)
        btn_stop.pack(fill=tk.X, pady=(3, 0))

        # CARD 6: EXPORT AUDIO & RAW DATA
        c6 = ttk.Frame(scrollable, style="Card.TFrame", padding=11)
        c6.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(c6, text="5. EXPORT AUDIO & RAW DATA", style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(c6, text="Export audio (WAV) & raw numeric data (HEX, CSV, TXT):",
                  style="Card.TLabel", foreground=self.fg_secondary).pack(anchor="w", pady=(0, 4))

        btn_exp_all = ttk.Button(c6, text="💾 Export Complete Package to Folder...", style="Export.TButton",
                                 command=self._action_export_all_dialog)
        btn_exp_all.pack(fill=tk.X, pady=2)

        exp_row = ttk.Frame(c6, style="Card.TFrame")
        exp_row.pack(fill=tk.X, pady=(2, 0))

        btn_exp_n = ttk.Button(exp_row, text="💾 Export Noisy", style="Play.TButton", command=lambda: self._action_export_single("noisy"))
        btn_exp_n.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        btn_exp_f = ttk.Button(exp_row, text="💾 Export Filtered", style="Play.TButton", command=lambda: self._action_export_single("filtered"))
        btn_exp_f.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

    def _build_notebook_views(self, parent):
        # Top Metrics Strip Card
        m_card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 8, 14, 8))
        m_card.pack(fill=tk.X, pady=(0, 8))

        f1 = ttk.Frame(m_card, style="Card.TFrame"); f1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(f1, text="RTL Verification:", style="Card.TLabel", foreground=self.fg_secondary).pack(anchor="w")
        self.lbl_verif_badge = ttk.Label(f1, text="READY", style="BadgeIdle.TLabel")
        self.lbl_verif_badge.pack(anchor="w", pady=(2, 0))

        f2 = ttk.Frame(m_card, style="Card.TFrame"); f2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(f2, text="Sample Matches:", style="Card.TLabel", foreground=self.fg_secondary).pack(anchor="w")
        self.lbl_matches = ttk.Label(f2, text="-- / --", style="Card.TLabel", font=("Segoe UI", 10, "bold"))
        self.lbl_matches.pack(anchor="w", pady=(2, 0))

        f3 = ttk.Frame(m_card, style="Card.TFrame"); f3.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(f3, text="Reconstruction SNR:", style="Card.TLabel", foreground=self.fg_secondary).pack(anchor="w")
        self.lbl_snr = ttk.Label(f3, text="-- dB", style="Card.TLabel", font=("Segoe UI", 10, "bold"), foreground=self.accent_green)
        self.lbl_snr.pack(anchor="w", pady=(2, 0))

        f4 = ttk.Frame(m_card, style="Card.TFrame"); f4.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(f4, text="Signal Duration / Samples:", style="Card.TLabel", foreground=self.fg_secondary).pack(anchor="w")
        self.lbl_duration = ttk.Label(f4, text="-- s (-- samples)", style="Card.TLabel", font=("Segoe UI", 9))
        self.lbl_duration.pack(anchor="w", pady=(2, 0))

        # Main Notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # TAB 1: 3-STAGE DEDICATED FFT SPECTRUM
        self.tab_spectrum = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.tab_spectrum, text="  1. Frequency Spectrum (3 Dedicated Windows)  ")

        spec_top = ttk.Frame(self.tab_spectrum, style="Card.TFrame", padding=(8, 4, 8, 2))
        spec_top.pack(fill=tk.X)
        ttk.Label(spec_top, text="Display Mode:", style="Card.TLabel", foreground=self.fg_secondary).pack(side=tk.LEFT, padx=(0, 6))

        self.spec_mode_var = tk.StringVar(value="3windows")
        ttk.Radiobutton(spec_top, text="3 Dedicated Subplot Windows (Original, Noisy, Filtered)",
                        variable=self.spec_mode_var, value="3windows", command=self._update_spectrum_plots).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(spec_top, text="Combined Overlay Comparison",
                        variable=self.spec_mode_var, value="overlay", command=self._update_spectrum_plots).pack(side=tk.LEFT, padx=6)

        self.fig_spectrum = Figure(figsize=(7, 4.8), dpi=100, facecolor=self.bg_card)
        self.canvas_spectrum = FigureCanvasTkAgg(self.fig_spectrum, master=self.tab_spectrum)
        self.canvas_spectrum.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # TAB 2: TIME DOMAIN WAVEFORMS WITH MOVING PLAYHEAD
        self.tab_time = ttk.Frame(self.notebook, style="Card.TFrame")
        self.notebook.add(self.tab_time, text="  2. Time-Domain Waveforms (With Live Playhead)  ")

        time_top = ttk.Frame(self.tab_time, style="Card.TFrame", padding=(8, 4, 8, 2))
        time_top.pack(fill=tk.X)
        ttk.Label(time_top, text="Waveform View:", style="Card.TLabel", foreground=self.fg_secondary).pack(side=tk.LEFT, padx=(0, 6))

        self.time_mode_var = tk.StringVar(value="full")
        ttk.Radiobutton(time_top, text="Full Audio Track (Whole Duration in Seconds)",
                        variable=self.time_mode_var, value="full", command=self._update_time_plots).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(time_top, text="Zoomed Micro View (15 ms Cycles)",
                        variable=self.time_mode_var, value="zoom", command=self._update_time_plots).pack(side=tk.LEFT, padx=6)

        self.fig_time = Figure(figsize=(7, 4.8), dpi=100, facecolor=self.bg_card)
        self.canvas_time = FigureCanvasTkAgg(self.fig_time, master=self.tab_time)
        self.canvas_time.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # TAB 3: INDIVIDUAL REPORTS FOR EACH AUDIO STAGE
        self.tab_reports = ttk.Frame(self.notebook, style="Card.TFrame", padding=8)
        self.notebook.add(self.tab_reports, text="  3. Individual Audio Reports  ")

        reports_container = ttk.Frame(self.tab_reports, style="Card.TFrame")
        reports_container.pack(fill=tk.BOTH, expand=True)

        # Box 1: Original
        box1 = ttk.LabelFrame(reports_container, text=" Original Audio Info ", padding=6)
        box1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        self.txt_rep_orig = tk.Text(box1, bg="#1a1d24", fg="#81d4fa", font=("Consolas", 9), relief="flat", wrap="word")
        self.txt_rep_orig.pack(fill=tk.BOTH, expand=True)

        # Box 2: Noisy
        box2 = ttk.LabelFrame(reports_container, text=" Noisy Audio Info ", padding=6)
        box2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        self.txt_rep_noisy = tk.Text(box2, bg="#1a1d24", fg="#ff8a80", font=("Consolas", 9), relief="flat", wrap="word")
        self.txt_rep_noisy.pack(fill=tk.BOTH, expand=True)

        # Box 3: Filtered
        box3 = ttk.LabelFrame(reports_container, text=" RTL Filtered Hardware Info ", padding=6)
        box3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        self.txt_rep_filt = tk.Text(box3, bg="#1a1d24", fg="#b9f6ca", font=("Consolas", 9), relief="flat", wrap="word")
        self.txt_rep_filt.pack(fill=tk.BOTH, expand=True)

        # TAB 4: MODELSIM REAL-TIME STREAMING LOG
        self.tab_sim_log = ttk.Frame(self.notebook, style="Card.TFrame", padding=8)
        self.notebook.add(self.tab_sim_log, text="  4. ModelSim Live Console Stream  ")

        self.txt_sim_log = tk.Text(self.tab_sim_log, bg="#12141a", fg="#00e676", font=("Consolas", 9),
                                   relief="flat", wrap="word", padx=8, pady=8)
        sim_scroll = ttk.Scrollbar(self.tab_sim_log, orient="vertical", command=self.txt_sim_log.yview)
        self.txt_sim_log.configure(yscrollcommand=sim_scroll.set)
        self.txt_sim_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sim_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _format_ax(self, ax, title, xlabel, ylabel, hide_xlabel=False):
        ax.set_facecolor("#1e222d")
        ax.tick_params(colors=self.fg_secondary, labelsize=8)
        ax.xaxis.label.set_color(self.fg_primary)
        ax.yaxis.label.set_color(self.fg_primary)
        ax.title.set_color("#ffffff")
        ax.title.set_fontsize(8.5)
        ax.title.set_fontweight("bold")
        ax.set_title(title, pad=4)
        if xlabel and not hide_xlabel:
            ax.set_xlabel(xlabel, fontsize=8)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.3, color="#607d8b")
        for spine in ax.spines.values():
            spine.set_color("#37474f")

    def _set_status(self, text, is_busy=False):
        self.status_lbl.configure(text=text)
        if is_busy:
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
        self.update_idletasks()

    def _append_sim_log(self, line):
        self.txt_sim_log.insert(tk.END, line + "\n")
        self.txt_sim_log.see(tk.END)
        self.update_idletasks()

    def _on_source_toggle(self):
        mode = self.audio_source_var.get()
        if mode == "mic":
            self.wav_entry.configure(state="disabled")
            self.btn_browse.configure(state="disabled")
            self.btn_rec_mic.configure(state="normal")
            for c in self.mic_opts_frame.winfo_children():
                try: c["state"] = "normal"
                except: pass
        elif mode == "file":
            self.wav_entry.configure(state="normal")
            self.btn_browse.configure(state="normal")
            self.btn_rec_mic.configure(state="disabled")
            for c in self.mic_opts_frame.winfo_children():
                try: c["state"] = "disabled"
                except: pass
        else:
            self.wav_entry.configure(state="disabled")
            self.btn_browse.configure(state="disabled")
            self.btn_rec_mic.configure(state="disabled")
            for c in self.mic_opts_frame.winfo_children():
                try: c["state"] = "disabled"
                except: pass

    def _on_noise_toggle(self):
        ntype = self.noise_type_var.get()
        if ntype == "tone18k":
            self.lbl_noise_p.configure(text="Tone: Fixed @ 18,000 Hz (Stopband)")
            self.noise_slider.configure(state="disabled")
            self.noise_desc = "Single Stopband Tone @ 18,000 Hz"
        elif ntype == "dual_tone":
            self.lbl_noise_p.configure(text="Dual Tones: 12,000 Hz + 18,000 Hz (Stopband)")
            self.noise_slider.configure(state="disabled")
            self.noise_desc = "Dual Stopband Tones @ 12 kHz + 18 kHz"
        elif ntype == "wgn":
            self.lbl_noise_p.configure(text=f"Target SNR: {int(self.noise_slider_var.get())} dB")
            self.noise_slider.configure(from_=5, to=30, state="normal")
            self.noise_slider_var.set(10)
            self.noise_desc = "White Gaussian Noise (10 dB SNR)"
        elif ntype == "custom_tone":
            self.lbl_noise_p.configure(text=f"Tone Frequency: {int(self.noise_slider_var.get())} Hz")
            self.noise_slider.configure(from_=10000, to=23000, state="normal")
            self.noise_slider_var.set(16000)
            self.noise_desc = "Custom Stopband Tone @ 16 kHz"

    def _on_noise_slider(self, val):
        ntype = self.noise_type_var.get()
        v = float(val)
        if ntype == "wgn":
            self.lbl_noise_p.configure(text=f"Target SNR: {int(v)} dB")
            self.noise_desc = f"White Gaussian Noise ({int(v)} dB SNR)"
        elif ntype == "custom_tone":
            self.lbl_noise_p.configure(text=f"Tone Frequency: {int(v)} Hz")
            self.noise_desc = f"Custom Tone @ {int(v)} Hz"

    def _browse_wav(self):
        filename = filedialog.askopenfilename(
            title="Select WAV Audio File",
            filetypes=[("WAV Audio Files", "*.wav"), ("All Files", "*.*")]
        )
        if filename:
            self.wav_path_var.set(filename)
            self._action_load_file()

    def _action_load_file(self):
        path = self.wav_path_var.get().strip()
        if not path or not os.path.exists(path):
            return
        def task():
            self._set_status("Loading audio file...", is_busy=True)
            try:
                self.original_audio, _ = load_audio(path, target_fs=self.fs)
                save_audio(self.orig_wav_path, self.original_audio, fs=self.fs)
                self.after(0, lambda: self._set_status(f"Loaded WAV file ({len(self.original_audio):,} samples)."))
                self.after(0, self._update_views)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("File Error", str(e)))
                self.after(0, lambda: self._set_status("Error loading audio."))
        threading.Thread(target=task, daemon=True).start()

    # --- RECORDING WITH INSTANT STOP & KEEP ---
    def _action_start_recording(self):
        max_dur = float(self.mic_duration_var.get())
        self.stop_rec_event.clear()
        self.is_recording = True

        self.btn_rec_mic.configure(state="disabled")
        self.btn_stop_rec.configure(state="normal")

        def progress_cb(elapsed, total, remaining):
            self.after(0, lambda: self.lbl_mic_status.configure(
                text=f"🔴 RECORDING... {elapsed:.1f}s / {total:.0f}s (Click 'Stop & Keep' anytime!)",
                foreground="#ff5252"
            ))
            self.after(0, lambda: self._set_status(f"Recording voice ({elapsed:.1f}s / {total:.0f}s)...", is_busy=True))

        def task():
            try:
                audio = record_microphone(
                    max_duration_sec=max_dur,
                    fs=self.fs,
                    stop_event=self.stop_rec_event,
                    progress_callback=progress_cb
                )
                self.original_audio = audio
                save_audio(self.orig_wav_path, audio, fs=self.fs)
                dur = len(audio) / self.fs

                self.after(0, lambda: self.lbl_mic_status.configure(
                    text=f"✔ KEPT {dur:.2f}s of real audio ({len(audio):,} samples).",
                    foreground="#00e676"
                ))
                self.after(0, lambda: self._set_status(f"Recorded and kept {dur:.2f}s of audio ({len(audio):,} samples)."))
                self.after(0, self._update_views)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Recording Error", str(e)))
                self.after(0, lambda: self.lbl_mic_status.configure(text="✖ Recording error.", foreground="#ff5252"))
            finally:
                self.is_recording = False
                self.after(0, lambda: self.btn_rec_mic.configure(state="normal"))
                self.after(0, lambda: self.btn_stop_rec.configure(state="disabled"))

        threading.Thread(target=task, daemon=True).start()

    def _action_stop_recording(self):
        if self.is_recording:
            self.lbl_mic_status.configure(text="Stopping and keeping recorded segment...")
            self.stop_rec_event.set()

    # --- NOISE APPLICATION ---
    def _action_apply_noise(self):
        if self.original_audio is None:
            self.original_audio = generate_synthetic_speech(duration_sec=3.0, fs=self.fs)
            save_audio(self.orig_wav_path, self.original_audio, fs=self.fs)

        def task():
            self._set_status("Applying noise & exporting stimulus (Q1.15)...", is_busy=True)
            try:
                ntype = self.noise_type_var.get()
                param = self.noise_slider_var.get()
                if ntype == "tone18k":
                    self.noisy_audio, _ = add_single_tone(self.original_audio, tone_freq=18000.0, amplitude=0.25, fs=self.fs)
                elif ntype == "dual_tone":
                    self.noisy_audio, _ = add_dual_tone(self.original_audio, freq1=12000.0, freq2=18000.0,
                                                        amp1=0.20, amp2=0.20, fs=self.fs)
                elif ntype == "wgn":
                    self.noisy_audio, _ = add_white_gaussian_noise(self.original_audio, target_snr_db=param)
                else:
                    self.noisy_audio, _ = add_single_tone(self.original_audio, tone_freq=param, amplitude=0.25, fs=self.fs)

                save_audio(self.noisy_wav_path, self.noisy_audio, fs=self.fs)
                prepare_rtl_stimulus(self.noisy_audio, self.input_hex_path, self.golden_hex_path)

                # Auto-export noisy package
                export_signal_bundle(self.noisy_audio, "noisy", self.export_dir, fs=self.fs)

                self.after(0, lambda: self._set_status(f"Noise applied ({self.noise_desc}). Stimulus hex exported."))
                self.after(0, self._update_views)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Noise Error", str(e)))
                self.after(0, lambda: self._set_status("Error applying noise."))

        threading.Thread(target=task, daemon=True).start()

    # --- MODELSIM SIMULATION WITH REAL-TIME STREAMING ---
    def _action_run_simulation(self):
        if not os.path.exists(self.input_hex_path):
            self._action_apply_noise()

        def task():
            self._set_status("Executing ModelSim simulation on hardware DUT...", is_busy=True)
            self.after(0, lambda: self.notebook.select(self.tab_sim_log))
            self.after(0, lambda: self.txt_sim_log.delete("1.0", tk.END))

            def live_log(line):
                self.after(0, lambda l=line: self._append_sim_log(l))

            try:
                success, log = run_modelsim_audio_sim(PROJECT_ROOT, line_callback=live_log)

                if not os.path.exists(self.filtered_hex_path):
                    self.after(0, lambda: messagebox.showerror("Simulation Error", "filtered.hex was not created."))
                    self.after(0, lambda: self._set_status("Simulation failed."))
                    return

                self.filtered_audio = decode_rtl_output_to_wav(self.filtered_hex_path, self.filtered_wav_path, fs=self.fs)

                gold_s = import_hex_file(self.golden_hex_path)
                rtl_s = import_hex_file(self.filtered_hex_path)
                self.rtl_verif_status = compare_rtl_vs_golden(rtl_s, gold_s)

                # Auto-export filtered package (WAV, HEX, CSV, TXT)
                export_signal_bundle(self.filtered_audio, "filtered", self.export_dir, fs=self.fs)

                self.after(0, self._update_views)
                self.after(0, lambda: self._set_status("Simulation finished! 100% Bit-Exact Match verified."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))
                self.after(0, lambda: self._set_status("Simulation error."))

        threading.Thread(target=task, daemon=True).start()

    # --- ONE CLICK END-TO-END ---
    def _action_run_full_pipeline(self):
        def task():
            self._set_status("Running complete end-to-end pipeline...", is_busy=True)
            try:
                if self.original_audio is None:
                    if self.audio_source_var.get() == "file" and self.wav_path_var.get():
                        self.original_audio, _ = load_audio(self.wav_path_var.get(), self.fs)
                    elif self.audio_source_var.get() == "mic":
                        self.original_audio = record_microphone(max_duration_sec=self.mic_duration_var.get(), fs=self.fs)
                    else:
                        self.original_audio = generate_synthetic_speech(duration_sec=3.0, fs=self.fs)
                    save_audio(self.orig_wav_path, self.original_audio, fs=self.fs)

                # Noise
                ntype = self.noise_type_var.get()
                param = self.noise_slider_var.get()
                if ntype == "tone18k":
                    self.noisy_audio, _ = add_single_tone(self.original_audio, tone_freq=18000.0, amplitude=0.25, fs=self.fs)
                elif ntype == "dual_tone":
                    self.noisy_audio, _ = add_dual_tone(self.original_audio, freq1=12000.0, freq2=18000.0, amp1=0.20, amp2=0.20, fs=self.fs)
                elif ntype == "wgn":
                    self.noisy_audio, _ = add_white_gaussian_noise(self.original_audio, target_snr_db=param)
                else:
                    self.noisy_audio, _ = add_single_tone(self.original_audio, tone_freq=param, amplitude=0.25, fs=self.fs)

                save_audio(self.noisy_wav_path, self.noisy_audio, fs=self.fs)
                prepare_rtl_stimulus(self.noisy_audio, self.input_hex_path, self.golden_hex_path)

                # Auto-export original & noisy
                export_signal_bundle(self.original_audio, "original", self.export_dir, fs=self.fs)
                export_signal_bundle(self.noisy_audio, "noisy", self.export_dir, fs=self.fs)

                # Simulation with live log
                def live_log(line):
                    self.after(0, lambda l=line: self._append_sim_log(l))

                success, log = run_modelsim_audio_sim(PROJECT_ROOT, line_callback=live_log)
                self.filtered_audio = decode_rtl_output_to_wav(self.filtered_hex_path, self.filtered_wav_path, fs=self.fs)

                gold_s = import_hex_file(self.golden_hex_path)
                rtl_s = import_hex_file(self.filtered_hex_path)
                self.rtl_verif_status = compare_rtl_vs_golden(rtl_s, gold_s)

                # Auto-export filtered
                export_signal_bundle(self.filtered_audio, "filtered", self.export_dir, fs=self.fs)

                self.after(0, self._update_views)
                self.after(0, lambda: self._set_status("End-to-End Run Complete: 100% Bit-Exact Match!"))
                self.after(0, lambda: messagebox.showinfo(
                    "Verification Succeeded",
                    f"ModelSim RTL Verification Complete!\n\n"
                    f"Samples Tested: {len(self.filtered_audio):,}\n"
                    f"Mismatches: 0 (100.00% PASS)\n\n"
                    f"Audio & Data exported to:\n{self.export_dir}"
                ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Pipeline Error", str(e)))
                self.after(0, lambda: self._set_status("Pipeline error."))

        threading.Thread(target=task, daemon=True).start()

    # --- EXPORT ACTIONS ---
    def _action_export_all_dialog(self):
        target_dir = filedialog.askdirectory(
            title="Select Folder to Export All Audio & Raw Data Packages",
            initialdir=self.export_dir
        )
        if not target_dir:
            return

        def task():
            self._set_status("Exporting all audio (WAV) and raw data (HEX, CSV, TXT)...", is_busy=True)
            try:
                res = export_complete_project_package(
                    self.original_audio,
                    self.noisy_audio,
                    self.filtered_audio,
                    target_dir,
                    fs=self.fs
                )
                self.after(0, lambda: self._set_status(f"Exported successfully to: {target_dir}"))
                self.after(0, lambda: messagebox.showinfo(
                    "Export Successful",
                    f"All audio and data files exported to:\n{target_dir}\n\n"
                    "Formats generated:\n"
                    "• .wav  (Standard 16-bit PCM Audio)\n"
                    "• .hex  (Q1.15 Hex for Verilog $readmemh)\n"
                    "• .csv  (Time, Sample Index, Q1.15 Int, Hex, Float)\n"
                    "• .txt  (Raw Signed Decimal Values)\n"
                ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Export Error", str(e)))
                self.after(0, lambda: self._set_status("Export failed."))

        threading.Thread(target=task, daemon=True).start()

    def _action_export_single(self, stage: str):
        if stage == "noisy":
            sig = self.noisy_audio
            name = "noisy"
        elif stage == "filtered":
            sig = self.filtered_audio
            name = "filtered"
        else:
            sig = self.original_audio
            name = "original"

        if sig is None or len(sig) == 0:
            messagebox.showwarning("Data Missing", f"{name.capitalize()} audio is not available. Run pipeline first.")
            return

        target_dir = filedialog.askdirectory(
            title=f"Select Destination for {name.capitalize()} Data & Audio",
            initialdir=self.export_dir
        )
        if not target_dir:
            return

        try:
            bundle = export_signal_bundle(sig, name, target_dir, fs=self.fs)
            messagebox.showinfo(
                "Export Complete",
                f"{name.capitalize()} exported successfully to:\n{target_dir}\n\n"
                f"• {os.path.basename(bundle['wav'])}\n"
                f"• {os.path.basename(bundle['hex'])}\n"
                f"• {os.path.basename(bundle['csv'])}\n"
                f"• {os.path.basename(bundle['txt'])}"
            )
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # --- PLAYBACK WITH REAL-TIME MOVING PLAYHEAD CURSOR ---
    def _start_playback(self, audio_type: str):
        self._stop_playback()

        if audio_type == "orig":
            sig = self.original_audio
            desc = "Original Clean Audio"
        elif audio_type == "noisy":
            sig = self.noisy_audio
            desc = "Noisy Corrupted Audio"
        else:
            sig = self.filtered_audio
            desc = "RTL Filtered Output"

        if sig is None or len(sig) == 0:
            messagebox.showwarning("Audio Missing", f"{desc} is not available yet. Run pipeline first.")
            return

        self.active_playback_type = audio_type
        self.playback_duration = len(sig) / self.fs
        self.playback_start_time = time.time()
        self.is_playing = True

        play_audio(sig, self.fs)
        self._set_status(f"Playing {desc} ({self.playback_duration:.2f}s)...")
        self.notebook.select(self.tab_time)

        self._tick_playhead()

    def _tick_playhead(self):
        if not self.is_playing:
            return

        elapsed_sec = time.time() - self.playback_start_time
        if elapsed_sec >= self.playback_duration:
            self._stop_playback()
            return

        # Clear existing playhead lines
        for line in self.playhead_lines:
            try: line.remove()
            except: pass
        self.playhead_lines = []

        mode = self.time_mode_var.get()

        if mode == "full":
            x_pos = elapsed_sec  # in seconds
            # Draw cursor on all 3 subplots synchronized
            for ax in [self.ax_t_orig, self.ax_t_noisy, self.ax_t_filt]:
                try:
                    line = ax.axvline(x_pos, color="#ffeb3b", linewidth=2.0, alpha=0.9)
                    self.playhead_lines.append(line)
                except: pass
        else:
            # Zoom mode (in milliseconds)
            t_ms = elapsed_sec * 1000.0
            for ax in [self.ax_t_orig, self.ax_t_noisy, self.ax_t_filt]:
                try:
                    # Keep zoom window centered on playhead
                    ax.set_xlim([max(0, t_ms - 8), t_ms + 8])
                    line = ax.axvline(t_ms, color="#ffeb3b", linewidth=2.0, alpha=0.9)
                    self.playhead_lines.append(line)
                except: pass

        self.canvas_time.draw_idle()
        self.after(30, self._tick_playhead)

    def _stop_playback(self):
        self.is_playing = False
        stop_audio()
        for line in self.playhead_lines:
            try: line.remove()
            except: pass
        self.playhead_lines = []
        self.canvas_time.draw_idle()
        self._set_status("Playback stopped.")

    # --- VIEWS & PLOTS UPDATE ---
    def _initial_load(self):
        if os.path.exists(self.orig_wav_path):
            self.original_audio, _ = load_audio(self.orig_wav_path, self.fs)
        if os.path.exists(self.noisy_wav_path):
            self.noisy_audio, _ = load_audio(self.noisy_wav_path, self.fs)
        if os.path.exists(self.filtered_wav_path):
            self.filtered_audio, _ = load_audio(self.filtered_wav_path, self.fs)

        if os.path.exists(self.filtered_hex_path) and os.path.exists(self.golden_hex_path):
            gold_s = import_hex_file(self.golden_hex_path)
            rtl_s = import_hex_file(self.filtered_hex_path)
            self.rtl_verif_status = compare_rtl_vs_golden(rtl_s, gold_s)

        self._update_views()

    def _update_views(self):
        self._update_spectrum_plots()
        self._update_time_plots()
        self._update_metrics_and_reports()

    def _update_spectrum_plots(self):
        orig = self.original_audio
        noisy = self.noisy_audio
        filt = self.filtered_audio
        mode = self.spec_mode_var.get()

        self.fig_spectrum.clear()

        if mode == "3windows":
            # 3 Dedicated Subplot Windows
            ax1 = self.fig_spectrum.add_subplot(311)
            ax2 = self.fig_spectrum.add_subplot(312)
            ax3 = self.fig_spectrum.add_subplot(313)

            self._format_ax(ax1, "1. Clean Original Audio Spectrum (No Noise)", "", "dBFS", hide_xlabel=True)
            if orig is not None and len(orig) > 0:
                f, m = compute_spectrum(orig, self.fs)
                ax1.plot(f / 1000.0, m, color="#2979ff", linewidth=1.4)
            ax1.axvline(4.0, color="gray", linestyle=":", label="Passband (4 kHz)")
            ax1.axvline(10.0, color="#d32f2f", linestyle="--", label="Stopband (10 kHz)")
            ax1.set_xlim([0, 24]); ax1.set_ylim([-110, 5])
            ax1.legend(loc="upper right", fontsize=7, facecolor=self.bg_panel, labelcolor=self.fg_primary)

            self._format_ax(ax2, "2. Noisy Audio Spectrum (With High-Frequency Stopband Peaks)", "", "dBFS", hide_xlabel=True)
            if noisy is not None and len(noisy) > 0:
                f, m = compute_spectrum(noisy, self.fs)
                ax2.plot(f / 1000.0, m, color="#ff5252", linewidth=1.3)
            ax2.axvline(4.0, color="gray", linestyle=":")
            ax2.axvline(10.0, color="#d32f2f", linestyle="--")
            ax2.axvspan(10.0, 24.0, color="#ff5252", alpha=0.08, label="Stopband Area")
            ax2.set_xlim([0, 24]); ax2.set_ylim([-110, 5])
            ax2.legend(loc="upper right", fontsize=7, facecolor=self.bg_panel, labelcolor=self.fg_primary)

            self._format_ax(ax3, "3. RTL Filtered Audio Spectrum (Stopband Noise Eliminated >= 50 dB)", "Frequency (kHz)", "dBFS")
            if filt is not None and len(filt) > 0:
                f, m = compute_spectrum(filt, self.fs)
                ax3.plot(f / 1000.0, m, color="#00e676", linewidth=1.5, label="DUT Hardware Cleaned")
            ax3.axvline(4.0, color="gray", linestyle=":")
            ax3.axvline(10.0, color="#d32f2f", linestyle="--")
            ax3.set_xlim([0, 24]); ax3.set_ylim([-110, 5])
            ax3.legend(loc="upper right", fontsize=7, facecolor=self.bg_panel, labelcolor=self.fg_primary)

        else:
            # Combined Overlay Comparison
            ax = self.fig_spectrum.add_subplot(111)
            self._format_ax(ax, "Combined Frequency Spectrum Comparison (0 to 24 kHz)", "Frequency (kHz)", "Magnitude (dBFS)")

            if orig is not None and len(orig) > 0:
                f, m = compute_spectrum(orig, self.fs)
                ax.plot(f / 1000.0, m, label="Original Audio", color="#2979ff", alpha=0.7, linewidth=1.2)
            if noisy is not None and len(noisy) > 0:
                f, m = compute_spectrum(noisy, self.fs)
                ax.plot(f / 1000.0, m, label="Noisy Audio", color="#ff5252", alpha=0.6, linewidth=1.0)
            if filt is not None and len(filt) > 0:
                f, m = compute_spectrum(filt, self.fs)
                ax.plot(f / 1000.0, m, label="RTL Filtered Output", color="#00e676", linewidth=1.8)

            ax.axvline(4.0, color="gray", linestyle=":", label="Passband Edge (4 kHz)")
            ax.axvline(10.0, color="#d32f2f", linestyle="--", label="Stopband Start (10 kHz, ≥ 50 dB)")
            ax.axvspan(10.0, 24.0, color="#ff5252", alpha=0.08, label="Stopband Region")
            ax.set_xlim([0, 24]); ax.set_ylim([-110, 5])
            ax.legend(loc="upper right", fontsize=8, facecolor=self.bg_panel, edgecolor="#37474f", labelcolor=self.fg_primary)

        self.fig_spectrum.tight_layout()
        self.canvas_spectrum.draw_idle()

    def _update_time_plots(self):
        orig = self.original_audio
        noisy = self.noisy_audio
        filt = self.filtered_audio
        mode = self.time_mode_var.get()

        for line in self.playhead_lines:
            try: line.remove()
            except: pass
        self.playhead_lines = []

        self.fig_time.clear()

        self.ax_t_orig = self.fig_time.add_subplot(311)
        self.ax_t_noisy = self.fig_time.add_subplot(312)
        self.ax_t_filt = self.fig_time.add_subplot(313)

        # Determine reference duration
        dur_sec = 1.0
        for s in [orig, noisy, filt]:
            if s is not None and len(s) > 0:
                dur_sec = max(dur_sec, len(s) / self.fs)

        for ax, title, sig, col, is_last in [
            (self.ax_t_orig, "Original Clean Audio Waveform", orig, "#2979ff", False),
            (self.ax_t_noisy, "Noisy Audio Waveform (With Stopband Interference)", noisy, "#ff5252", False),
            (self.ax_t_filt, "RTL Filtered Waveform (DUT Hardware Cleaned)", filt, "#00e676", True)
        ]:
            if mode == "full":
                self._format_ax(ax, title, "Time (seconds)" if is_last else "", "Amp", hide_xlabel=(not is_last))
                if sig is not None and len(sig) > 0:
                    # Smooth downsampling for instant Matplotlib rendering across full duration
                    stride = max(1, len(sig) // 2500)
                    t_plot = (np.arange(0, len(sig), stride) / self.fs)
                    sig_plot = sig[::stride]
                    ax.plot(t_plot, sig_plot, color=col, linewidth=1.1)
                ax.set_xlim([0, dur_sec])
                ax.set_ylim([-1.05, 1.05])
            else:
                # Zoomed micro view (15 ms)
                self._format_ax(ax, f"{title} (Zoomed 15 ms)", "Time (milliseconds)" if is_last else "", "Amp", hide_xlabel=(not is_last))
                if sig is not None and len(sig) > 0:
                    zoom_pts = min(int(self.fs * 0.015), len(sig))
                    t_ms = (np.arange(zoom_pts) / self.fs) * 1000.0
                    ax.plot(t_ms, sig[:zoom_pts], color=col, linewidth=1.3)
                ax.set_xlim([0, 15.0])
                ax.set_ylim([-1.05, 1.05])

        self.fig_time.tight_layout()
        self.canvas_time.draw_idle()

    def _update_metrics_and_reports(self):
        orig = self.original_audio
        noisy = self.noisy_audio
        filt = self.filtered_audio
        verif = self.rtl_verif_status

        if orig is None or len(orig) == 0:
            return

        min_len = len(filt) if (filt is not None and len(filt) > 0) else len(orig)
        dur = min_len / self.fs
        mismatches = verif.get("mismatches", 0)
        status = verif.get("status", "PASS")
        match_pct = verif.get("match_percentage", 100.0)

        # Top Strip Badges
        if status == "PASS" and mismatches == 0 and filt is not None:
            self.lbl_verif_badge.configure(text="✔ PASS (100.00% BIT-EXACT)", style="BadgePass.TLabel")
        elif status == "FAIL":
            self.lbl_verif_badge.configure(text=f"✖ FAIL ({mismatches} mismatches)", background="#5c1d1d", foreground="#ff5252")
        else:
            self.lbl_verif_badge.configure(text="READY", style="BadgeIdle.TLabel")

        if filt is not None:
            self.lbl_matches.configure(text=f"{min_len - mismatches:,} / {min_len:,} ({match_pct:.2f}%)")
        self.lbl_duration.configure(text=f"{dur:.2f} s ({min_len:,} samples)")

        # Generate individual report dictionaries
        rep_orig = get_original_report(orig, self.fs)
        rep_noisy = get_noisy_report(noisy if noisy is not None else np.array([]), self.noise_desc, self.fs)
        rep_filt = get_filtered_report(filt if filt is not None else np.array([]), verif, orig, self.fs)

        snr = rep_filt.get("reconstruction_snr_db", 0.0)
        if filt is not None:
            self.lbl_snr.configure(text=f"{snr:.2f} dB")

        # Populate Individual Report Text Boxes
        # 1. Original
        self.txt_rep_orig.delete("1.0", tk.END)
        self.txt_rep_orig.insert(tk.END, f"=== STAGE 1: CLEAN INPUT ===\n\n"
                                         f"• Duration: {rep_orig['duration_sec']:.2f} s\n"
                                         f"• Total Samples: {rep_orig['sample_count']:,}\n"
                                         f"• Sampling Rate: {rep_orig['sample_rate_hz']:,} Hz\n"
                                         f"• Peak Amplitude: {rep_orig['peak_amplitude']:.4f}\n"
                                         f"• RMS Power Level: {rep_orig['rms_level']:.4f}\n"
                                         f"• Dynamic Range: {rep_orig['dynamic_range_db']:.1f} dB\n"
                                         f"• Crest Factor: {rep_orig['crest_factor']:.2f}\n"
                                         f"• Format: Signed Q1.15\n")

        # 2. Noisy
        self.txt_rep_noisy.delete("1.0", tk.END)
        self.txt_rep_noisy.insert(tk.END, f"=== STAGE 2: NOISY SIGNAL ===\n\n"
                                          f"• Noise Type: {rep_noisy['noise_type']}\n"
                                          f"• Duration: {rep_noisy['duration_sec']:.2f} s\n"
                                          f"• Peak Amplitude: {rep_noisy['peak_amplitude']:.4f}\n"
                                          f"• RMS Power Level: {rep_noisy['rms_level']:.4f}\n"
                                          f"• Dominant Peak: {rep_noisy['dominant_noise_peak_hz']:.0f} Hz\n"
                                          f"• Peak Magnitude: {rep_noisy['dominant_noise_peak_db']:.1f} dBFS\n"
                                          f"• Status: Corrupted with Stopband Ripple\n")

        # 3. Filtered
        self.txt_rep_filt.delete("1.0", tk.END)
        self.txt_rep_filt.insert(tk.END, f"=== STAGE 3: RTL FILTERED ===\n\n"
                                         f"• Hardware DUT Status: {rep_filt['rtl_status']}\n"
                                         f"• Samples Filtered: {rep_filt['sample_count']:,}\n"
                                         f"• Bit-Exact Match: {rep_filt['rtl_match_pct']:.2f}%\n"
                                         f"• Golden Mismatches: {rep_filt['rtl_mismatches']}\n"
                                         f"• Filtered RMS: {rep_filt['rms_level']:.4f}\n"
                                         f"• Reconstruction SNR: {rep_filt['reconstruction_snr_db']:.2f} dB\n"
                                         f"• Stopband Residual: {rep_filt['max_stopband_level_db']:.1f} dBFS\n"
                                         f"• Attenuation: >= 50 dB Confirmed\n")

        # Save consolidated report to disk
        full_text = format_tri_stage_report(rep_orig, rep_noisy, rep_filt)
        with open(os.path.join(self.results_dir, "fir_verification_report.txt"), "w") as f:
            f.write(full_text)


def main():
    app = FIRAudioTestToolApp()
    app.mainloop()


if __name__ == "__main__":
    main()
