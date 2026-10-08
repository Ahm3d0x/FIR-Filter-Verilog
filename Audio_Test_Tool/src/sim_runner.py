"""
FIR Audio Test Tool - ModelSim Simulation Runner with Live Output Streaming.
"""

import os
import shutil
import subprocess
from typing import Callable, Optional


def find_vsim() -> Optional[str]:
    """
    Locate vsim executable on the system.
    """
    vsim_path = shutil.which("vsim")
    if vsim_path:
        return vsim_path

    candidates = [
        r"G:\Altera\questa_fse\win64\vsim.exe",
        r"G:\modelsim\modelsim_ase\win32aloem\vsim.exe",
        r"C:\modeltech64_20.4\win64\vsim.exe",
        r"C:\intelFPGA_lite\20.1\modelsim_ase\win32aloem\vsim.exe"
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def run_modelsim_audio_sim(project_root: str,
                           line_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
    """
    Execute ModelSim batch simulation for fir_audio_tb.v with live line streaming.
    
    Args:
        project_root: Root directory of FIR_Project (containing sim/ directory).
        line_callback: Optional function called for each line produced by ModelSim.
        
    Returns:
        tuple (is_pass, complete_log_output)
    """
    vsim_exe = find_vsim()
    if not vsim_exe:
        msg = "[ERROR] ModelSim (vsim) executable not found in PATH or standard directories."
        if line_callback:
            line_callback(msg)
        return False, msg

    sim_dir = os.path.join(project_root, "sim")
    do_script = "run_audio.do"

    cmd = [vsim_exe, "-c", "-do", do_script]
    start_msg = f"[INFO] Launching ModelSim: {' '.join(cmd)} in {sim_dir}"
    if line_callback:
        line_callback(start_msg)

    log_lines = [start_msg]
    is_pass = False

    try:
        process = subprocess.Popen(
            cmd,
            cwd=sim_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for line in iter(process.stdout.readline, ''):
            if not line and process.poll() is not None:
                break
            stripped = line.rstrip()
            if stripped:
                log_lines.append(stripped)
                if line_callback:
                    line_callback(stripped)
                if "BIT-EXACT HARDWARE MATCH" in stripped:
                    is_pass = True

        process.stdout.close()
        process.wait(timeout=30)

        full_log = "\n".join(log_lines)
        if not is_pass:
            is_pass = "BIT-EXACT HARDWARE MATCH" in full_log

        return is_pass, full_log

    except subprocess.TimeoutExpired:
        process.kill()
        timeout_msg = "[ERROR] ModelSim simulation timed out."
        if line_callback:
            line_callback(timeout_msg)
        return False, timeout_msg
    except Exception as e:
        err_msg = f"[ERROR] Failed to execute ModelSim: {e}"
        if line_callback:
            line_callback(err_msg)
        return False, err_msg
