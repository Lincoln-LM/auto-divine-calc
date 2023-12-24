"""Clipboard update listening thread"""

from threading import Thread

import pyperclip


class ClipboardListener(Thread):
    """Clipboard update listening thread"""

    def __init__(self, on_change) -> None:
        super().__init__(daemon=True)
        self.last_clipboard = pyperclip.paste()
        self.on_change = on_change

    def run(self):
        while True:
            clipboard = pyperclip.paste()
            if clipboard != self.last_clipboard:
                self.last_clipboard = clipboard
                self.on_change(clipboard)
