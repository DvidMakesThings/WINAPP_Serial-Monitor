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
        """Pause auto-scrolling."""
        self.paused = True

    def resume(self):
        """Resume auto-scrolling and flush any buffered messages."""
        self.paused = False
        self.flush_buffer()

    def flush_buffer(self):
        """Insert any buffered text into the terminal."""
        if self.buffer:
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.buffer = ""

    def append(self, text):
        """
        Append text to the terminal. If paused, store it in a buffer.
        Otherwise, insert immediately.
        """
        if self.paused:
            self.buffer += text + "\n"
        else:
            self.text_widget.insert(tk.END, text + "\n")
            self.text_widget.see(tk.END)
