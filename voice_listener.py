"""
Voice Listener — records audio with sounddevice (no PyAudio needed).
Implements simple energy-based VAD:
  - waits up to phrase_timeout_sec for speech to begin
  - records until 1 second of silence after speech ends
  - sends raw PCM bytes to Google Speech API via SpeechRecognition
"""
import time
import queue
import numpy as np
import sounddevice as sd
import speech_recognition as sr

SAMPLE_RATE  = 16000   # Hz  (16 kHz is ideal for speech)
CHUNK_FRAMES = 1024    # frames per audio block


class VoiceListener:
    def __init__(self, phrase_timeout_sec: int, phrase_limit_sec: int, language: str):
        self.phrase_timeout_sec = phrase_timeout_sec
        self.phrase_limit_sec   = phrase_limit_sec
        self.language           = language
        self._recognizer        = sr.Recognizer()

        # Energy threshold for int16 samples (tune in commands.json if needed)
        self._energy = 600

        # Silence = this many consecutive silent chunks → end of phrase
        # ~1.0 second of silence
        self._silence_limit = int(SAMPLE_RATE / CHUNK_FRAMES * 1.0)

    def listen(self) -> str | None:
        """
        Block until a phrase is captured, then return lowercase transcription.
        Returns None on silence-timeout, unrecognised audio, or API error.
        """
        audio_q: queue.Queue = queue.Queue()

        def _cb(indata, frames, time_info, status):
            audio_q.put(indata.copy())

        chunks          = []
        speech_started  = False
        speech_start    = 0.0
        silence_count   = 0
        wait_start      = time.monotonic()

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_FRAMES,
            callback=_cb,
        ):
            while True:
                now = time.monotonic()

                # Timed out waiting for speech to start
                if not speech_started and (now - wait_start) > self.phrase_timeout_sec:
                    return None

                # Phrase too long — cut off
                if speech_started and (now - speech_start) > self.phrase_limit_sec:
                    break

                try:
                    chunk = audio_q.get(timeout=0.15)
                except queue.Empty:
                    continue

                rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

                if rms > self._energy:
                    if not speech_started:
                        speech_started = True
                        speech_start   = time.monotonic()
                    silence_count = 0
                    chunks.append(chunk)

                elif speech_started:
                    # Still collecting — might be a short pause mid-sentence
                    chunks.append(chunk)
                    silence_count += 1
                    if silence_count >= self._silence_limit:
                        break  # clean end of utterance

        if not chunks:
            return None

        # Build an sr.AudioData from raw int16 PCM bytes
        pcm_bytes  = np.concatenate(chunks, axis=0).flatten().tobytes()
        audio_data = sr.AudioData(pcm_bytes, SAMPLE_RATE, sample_width=2)

        try:
            text = self._recognizer.recognize_google(audio_data, language=self.language)
            return text.lower().strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[Voice] Google Speech API error: {e}")
            return None
        except Exception as e:
            print(f"[Voice] Unexpected error: {e}")
            return None
