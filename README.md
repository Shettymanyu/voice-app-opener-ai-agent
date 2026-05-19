<!--
  Drop this file in: github.com/Shettymanyu/voice-app-opener-ai-agent/README.md
-->

<h1 align="center">Voice App Opener &mdash; AI Agent</h1>

<p align="center">
  <em>A hands-free desktop launcher: clap to wake, speak a command, the agent opens the right app.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Speech%20Recognition-4285F4?style=flat-square&logo=googleassistant&logoColor=white"/>
  <img src="https://img.shields.io/badge/Audio-PyAudio%20%2F%20Sounddevice-FF6F00?style=flat-square"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white"/>
</p>

---

## What it does

A lightweight Python agent that lives in the background on your machine. When it hears a **clap**, it wakes up, listens for a **spoken command**, matches it against a JSON of known apps, and launches the right one. Includes a calibration step for your microphone and a startup installer so it auto-runs at boot.

```
   [silence]  -->  clap detected  -->  "open vscode"  -->  VS Code opens
```

## Components

| File | Role |
| --- | --- |
| `main.py` | Entrypoint: wires the clap detector, voice listener, and command processor together |
| `clap_detector.py` | Detects sharp audio peaks above an ambient threshold |
| `voice_listener.py` | Captures speech after wake, sends it to the speech-to-text backend |
| `command_processor.py` | Maps recognized text to an action from `commands.json` |
| `app_launcher.py` | Actually opens the target application |
| `calibrate.py` | One-time script to tune the clap-detection threshold to your room |
| `install_startup.py` | Adds the agent to system startup so it runs on boot |
| `commands.json` | Your editable command -> app mapping |

## How it works

```
                +----------------+   loud peak?   +-----------------+
   microphone --> clap_detector  ----- yes -----> voice_listener     |
                +----------------+                 (speech-to-text)  |
                                                         |           |
                                                         v           |
                                                command_processor    |
                                                         |           |
                                                         v           |
                                                  app_launcher       |
                                                         |           |
                                                         v           |
                                                  target app opens   |
                                                                     |
                                                  (loop back) <------+
```

## Getting started

```bash
git clone https://github.com/Shettymanyu/voice-app-opener-ai-agent.git
cd voice-app-opener-ai-agent

python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Calibrate clap detection for your environment:

```bash
python calibrate.py
```

Edit `commands.json` to map spoken phrases to apps:

```json
{
  "open vscode": "C:/Users/<you>/AppData/Local/Programs/Microsoft VS Code/Code.exe",
  "open chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "play music":  "spotify:"
}
```

Run the agent:

```bash
python main.py
```

(Optional) auto-start on boot:

```bash
python install_startup.py
```

## Roadmap

- [ ] LLM-based fuzzy command matching ("open my code editor" -> VS Code)
- [ ] Wake word instead of clap (Porcupine / openWakeWord)
- [ ] Cross-platform launcher (macOS, Linux)
- [ ] System-tray UI for live logs and a kill switch

## Author

Built by **Manyu Shetty** &mdash; <a href="https://github.com/Shettymanyu">@Shettymanyu</a> &middot; <a href="mailto:shettymanyu@gmail.com">shettymanyu@gmail.com</a>
