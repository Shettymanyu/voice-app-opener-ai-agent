"""
Clap Detector — listens for a single clap (one loud transient spike).
Uses sounddevice for continuous low-latency audio monitoring.
"""
import time
import threading
import numpy as np
import sounddevice as sd


class ClapDetector:
    def __init__(self, threshold: float, cooldown_sec: float,
                 sample_rate: int, block_size: int, on_clap):
        self.threshold = threshold
        self.cooldown_sec = cooldown_sec
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.on_clap = on_clap  # callback fired on each valid clap

        self._running = False
        self._stream = None
        self._cooldown_until = 0.0

    def _audio_callback(self, indata, frames, time_info, status):
        if not self._running:
            return

        now = time.monotonic()
        if now < self._cooldown_until:
            return

        rms = float(np.sqrt(np.mean(indata ** 2)))

        if rms > self.threshold:
            self._cooldown_until = now + self.cooldown_sec
            threading.Thread(target=self.on_clap, daemon=True).start()

    def start(self):
        self._running = True
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def pause(self):
        """Pause clap detection (while in active listening mode)."""
        self._running = False

    def resume(self):
        """Resume clap detection (back to idle)."""
        self._running = True
