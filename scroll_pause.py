import tkinter as tk

class ScrollController:
    def __init__(self, text_widget):
        """
        text_widget: the tkinter Text widget used as the terminal.
        """
        self.text_widget = text_widget
        self.paused = False
        self.buffer = ""

    def pause(self):
        """Pause auto‐scrolling."""
        self.paused = True

    def resume(self):
        """Resume auto‐scrolling and flush any buffered messages."""
        self.paused = False
        self.flush_buffer()

    def flush_buffer(self):
        """Insert any buffered text (which already contains \n) into the terminal."""
        if not self.buffer:
            return
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, self.buffer)
        self.text_widget.see(tk.END)
        self.text_widget.config(state="disabled")
        self.buffer = ""

    def append(self, text):
        """
        Append *exact* text into the terminal. Incoming text may include '\n'.
        If paused, buffer it verbatim.
        """
        if self.paused:
            self.buffer += text
        else:
            self.text_widget.config(state="normal")
            self.text_widget.insert(tk.END, text)
            self.text_widget.see(tk.END)
            self.text_widget.config(state="disabled")

            # trim oldest lines if we're over the cap
            max_lines = 10000
            curr = int(self.text_widget.index('end-1c').split('.')[0])
            if curr > max_lines:
                self.text_widget.config(state="normal")
                self.text_widget.delete('1.0', f'{curr-max_lines}.0')
                self.text_widget.config(state="disabled")
