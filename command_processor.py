"""
Command Processor — matches transcribed text to a command in the config.
Supports exact match and partial/substring match for flexibility.
"""


class CommandProcessor:
    def __init__(self, commands: dict):
        # Sort keys by length descending so longer phrases match first
        # (e.g. "vs code" before "code")
        self.commands = commands
        self._sorted_keys = sorted(commands.keys(), key=len, reverse=True)

    def match(self, text: str) -> tuple[str, dict] | tuple[None, None]:
        """
        Find the best matching command for the given transcribed text.
        Returns (command_name, command_entry) or (None, None) if no match.
        """
        text = text.lower().strip()

        # 1. Exact match
        if text in self.commands:
            return text, self.commands[text]

        # 2. Partial / substring match (longest command key that appears in text)
        for key in self._sorted_keys:
            if key in text:
                return key, self.commands[key]

        return None, None

    def list_commands(self) -> list[str]:
        return list(self.commands.keys())
