"""
Calibration tool — shows live mic levels and auto-detects the right clap threshold.
Run this BEFORE main.py if clap detection isn't working.

Usage:  python calibrate.py
"""
import time
import json
import os
import numpy as np
import sounddevice as sd

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "commands.json")
SAMPLE_RATE = 44100
BLOCK_SIZE  = 1024

# ── 1. List all input devices ────────────────────────────────────────────────
print("\n=== Audio Input Devices ===")
devices = sd.query_devices()
default_input = sd.default.device[0]
for i, d in enumerate(devices):
    if d["max_input_channels"] > 0:
        marker = " << DEFAULT" if i == default_input else ""
        print(f"  [{i}] {d['name']}{marker}")

print(f"\nUsing device [{default_input}]: {devices[default_input]['name']}")
print("(If wrong device, set SOUNDDEVICE_DEFAULT_DEVICE env var or edit sounddevice default)\n")

# ── 2. Live level meter ───────────────────────────────────────────────────────
print("=== Live Mic Level (stay quiet first, then clap several times) ===")
print("Format:  RMS level  |  bar\n")

samples = []

def callback(indata, frames, time_info, status):
    rms = float(np.sqrt(np.mean(indata ** 2)))
    samples.append(rms)
    bar_len = int(rms * 200)
    bar = "#" * min(bar_len, 60)
    clap_marker = " << CLAP?" if rms > 0.05 else ""
    print(f"  {rms:.4f}  |  {bar:<60}{clap_marker}", end="\r", flush=True)

stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    channels=1,
    dtype="float32",
    callback=callback,
)

stream.start()
print("Monitoring for 10 seconds — stay quiet for 2s then clap 4–5 times...\n")
time.sleep(10)
stream.stop()
stream.close()

# ── 3. Auto-calculate threshold ───────────────────────────────────────────────
if not samples:
    print("\n[!] No audio captured — check your microphone.")
    exit(1)

samples_arr = np.array(samples)

# Noise floor = median of the quietest 50%
noise_floor = float(np.percentile(samples_arr, 50))

# Clap level = average of the loudest 5%
clap_level  = float(np.percentile(samples_arr, 95))

# Threshold = halfway between noise floor and clap peak
threshold   = round((noise_floor + clap_level) / 2, 4)
threshold   = max(threshold, noise_floor * 3)   # at least 3x noise floor
threshold   = round(threshold, 4)

print(f"\n\n=== Results ===")
print(f"  Noise floor (quiet) : {noise_floor:.4f}")
print(f"  Clap level  (loud)  : {clap_level:.4f}")
print(f"  Recommended threshold: {threshold:.4f}")

# ── 4. Write threshold back to commands.json ─────────────────────────────────
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    old = config["settings"]["clap_threshold"]
    config["settings"]["clap_threshold"] = threshold

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"\n[OK] commands.json updated: clap_threshold {old} -> {threshold}")
    print("    Run  python main.py  now — clap detection should work.\n")

except Exception as e:
    print(f"\n[!] Could not update commands.json: {e}")
    print(f"    Manually set  clap_threshold: {threshold}  in commands.json\n")
