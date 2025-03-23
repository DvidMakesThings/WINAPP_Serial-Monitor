import customtkinter as ctk

class FilterPanel(ctk.CTkFrame):
    def __init__(self, master, on_filter_change, **kwargs):
        """
        Create a filter/search panel.
        
        on_filter_change: a callback function that receives the current filter text.
        """
        super().__init__(master, **kwargs)
        self.on_filter_change = on_filter_change
        self.filter_entry = ctk.CTkEntry(self, placeholder_text="Filter messages...", font=("Helvetica", 14))
        self.filter_entry.pack(fill="x", padx=5, pady=5)
        self.filter_entry.bind("<KeyRelease>", self.filter_changed)

    def filter_changed(self, event):
        text = self.filter_entry.get()
        self.on_filter_change(text)
