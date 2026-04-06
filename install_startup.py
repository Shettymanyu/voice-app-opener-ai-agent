"""
Adds the agent to Windows Startup so it runs automatically on login.
Run once: python install_startup.py
To remove: python install_startup.py --remove
"""
import os
import sys

STARTUP_FOLDER = os.path.join(
    os.environ["APPDATA"],
    r"Microsoft\Windows\Start Menu\Programs\Startup",
)
SHORTCUT_NAME = "VoiceAppOpener.bat"
SHORTCUT_PATH = os.path.join(STARTUP_FOLDER, SHORTCUT_NAME)

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(AGENT_DIR, "main.py")
PYTHON_EXE = sys.executable


def install():
    bat_content = (
        f'@echo off\n'
        f'cd /d "{AGENT_DIR}"\n'
        f'start "" /min "{PYTHON_EXE}" "{MAIN_SCRIPT}"\n'
    )
    with open(SHORTCUT_PATH, "w") as f:
        f.write(bat_content)
    print(f"[Setup] Startup entry created:\n  {SHORTCUT_PATH}")
    print("[Setup] The agent will now start automatically on next login.")


def remove():
    if os.path.exists(SHORTCUT_PATH):
        os.remove(SHORTCUT_PATH)
        print(f"[Setup] Startup entry removed: {SHORTCUT_PATH}")
    else:
        print("[Setup] No startup entry found.")


if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    else:
        install()
