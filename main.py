"""
Voice App Opener — AI Agent
============================
Clap once  →  agent starts listening continuously
Tab key    →  stop listening, go back to idle

While listening, say any command keyword → that app/URL opens instantly.
Edit commands.json to add more — no restart needed.
"""
import json
import os
import time
import threading
import winsound
from pynput import keyboard as kb

from clap_detector import ClapDetector
from voice_listener import VoiceListener
from command_processor import CommandProcessor
from app_launcher import AppLauncher


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "commands.json")

# Agent states
IDLE   = "idle"
ACTIVE = "active"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def beep(frequency: int, duration_ms: int):
    try:
        winsound.Beep(frequency, duration_ms)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class VoiceAgent:
    def __init__(self):
        self.state = IDLE
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()   # signals listening loop to exit
        self._listen_thread: threading.Thread | None = None

        config = load_config()
        s = config.get("settings", {})

        self._voice = VoiceListener(
            phrase_timeout_sec=s.get("listen_phrase_timeout_sec", 2),
            phrase_limit_sec=s.get("listen_phrase_limit_sec", 5),
            language=s.get("language", "en-US"),
        )
        self._launcher = AppLauncher()
        self._play_sounds = s.get("play_sounds", True)
        self._log_enabled = s.get("log_commands", True)

        self._detector = ClapDetector(
            threshold=s.get("clap_threshold", 0.25),
            cooldown_sec=s.get("clap_cooldown_sec", 1.5),
            sample_rate=s.get("sample_rate", 44100),
            block_size=s.get("block_size", 1024),
            on_clap=self._on_clap,
        )

    def start(self):
        self._detector.start()
        print("[Agent] Ready — clap to start listening.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Agent] Shutting down...")
        finally:
            self._detector.stop()
            self._stop_event.set()
            print("[Agent] Stopped.")

    # ------------------------------------------------------------------
    # Clap handler — toggles between IDLE and ACTIVE
    # ------------------------------------------------------------------

    def _on_clap(self):
        with self._state_lock:
            if self.state == IDLE:
                self.state = ACTIVE
                self._stop_event.clear()
                self._listen_thread = threading.Thread(
                    target=self._listening_loop, daemon=True
                )
                self._listen_thread.start()
            # If already active, clap does nothing — use Tab to stop

    # ------------------------------------------------------------------
    # Continuous listening loop — runs until stop_event is set
    # ------------------------------------------------------------------

    def _stop_listening(self):
        """Called when Tab is pressed — ends the active session."""
        with self._state_lock:
            if self.state == ACTIVE:
                self.state = IDLE
                self._stop_event.set()
                print("\n[Agent] Stopped (Tab pressed). Clap to start again.\n")
                if self._play_sounds:
                    threading.Thread(
                        target=lambda: (beep(700, 100), time.sleep(0.08), beep(500, 200)),
                        daemon=True,
                    ).start()

    def _listening_loop(self):
        print("\n[Agent] Listening started — say a command any time.")
        print("[Agent] Press Tab to stop.\n")

        # Watch for Tab key in a background thread
        def on_press(key):
            if key == kb.Key.tab:
                self._stop_listening()
                return False  # stops the pynput listener

        kb_listener = kb.Listener(on_press=on_press)
        kb_listener.start()

        if self._play_sounds:
            beep(900, 120)
            time.sleep(0.06)
            beep(1200, 150)

        while not self._stop_event.is_set():
            text = self._voice.listen()

            if self._stop_event.is_set():
                break

            if not text:
                continue  # silence or unrecognised — keep going

            print(f"[Agent] Heard: \"{text}\"")

            # Reload commands.json live so edits take effect without restart
            try:
                cfg = load_config()
                processor = CommandProcessor(cfg["commands"])
            except Exception as e:
                print(f"[Agent] Config reload error: {e}")
                continue

            cmd_name, cmd_entry = processor.match(text)

            if cmd_entry:
                desc = cmd_entry.get("description", cmd_name)
                print(f"[Agent] → Opening: {desc}")
                success = self._launcher.launch(cmd_name, cmd_entry)
                if self._play_sounds:
                    threading.Thread(
                        target=lambda ok=success: beep(1300 if ok else 400, 180),
                        daemon=True,
                    ).start()
                if self._log_enabled:
                    _log(text, cmd_name, success)
            else:
                print(f"[Agent] No match for \"{text}\" — still listening...")

        kb_listener.stop()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(spoken: str, matched: str, success: bool):
    log_path = os.path.join(os.path.dirname(__file__), "agent.log")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status = "OK" if success else "FAIL"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] heard='{spoken}' matched='{matched}' status={status}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  Voice App Opener")
    print("  Clap       →  start listening")
    print("  Tab key    →  stop listening")
    print("  Ctrl+C     →  quit")
    print("=" * 55)
    config = load_config()
    commands = config.get("commands", {})
    print(f"\n[Agent] Commands loaded: {', '.join(commands.keys())}\n")
    VoiceAgent().start()
