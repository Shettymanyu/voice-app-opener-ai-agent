"""
App Launcher — executes a command entry from commands.json.
Supports three action types:
  - "app"     : launch an .exe by absolute path
  - "url"     : open a URL in the default browser
  - "command" : run a shell command / program name (resolved via PATH)
"""
import os
import subprocess
import webbrowser


class AppLauncher:
    def launch(self, name: str, entry: dict) -> bool:
        """
        Launch an app/URL based on its config entry.
        Returns True on success, False on failure.
        """
        action_type = entry.get("type", "command")

        try:
            if action_type == "url":
                return self._open_url(name, entry["url"])

            elif action_type == "app":
                return self._open_app(name, entry)

            elif action_type == "command":
                return self._run_command(name, entry["cmd"])

            else:
                print(f"[Launcher] Unknown action type '{action_type}' for '{name}'")
                return False

        except Exception as e:
            print(f"[Launcher] Failed to launch '{name}': {e}")
            return False

    def _open_url(self, name: str, url: str) -> bool:
        print(f"[Launcher] Opening URL for '{name}': {url}")
        webbrowser.open(url)
        return True

    def _open_app(self, name: str, entry: dict) -> bool:
        path = os.path.expandvars(entry.get("path", ""))
        fallback = os.path.expandvars(entry.get("fallback", ""))

        if path and os.path.exists(path):
            print(f"[Launcher] Launching app '{name}': {path}")
            subprocess.Popen([path], shell=False)
            return True

        if fallback and os.path.exists(fallback):
            print(f"[Launcher] Launching app '{name}' (fallback): {fallback}")
            subprocess.Popen([fallback], shell=False)
            return True

        # Last resort: try running as a command name
        print(f"[Launcher] App path not found for '{name}', trying as command...")
        cmd = entry.get("cmd", name)
        return self._run_command(name, cmd)

    def _run_command(self, name: str, cmd: str) -> bool:
        print(f"[Launcher] Running command for '{name}': {cmd}")
        subprocess.Popen(cmd, shell=True)
        return True
