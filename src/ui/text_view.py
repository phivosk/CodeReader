# src/ui/text_view.py
import tkinter as tk
from tkinter import ttk, scrolledtext


class TextView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_area = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, font=("Segoe UI Variable", 10),
            relief=tk.FLAT, borderwidth=0, undo=True
        )
        self.text_area.pack(expand=True, fill=tk.BOTH)
        self.text_area.config(state=tk.DISABLED)

    def set_text(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', text)
        self.text_area.config(state=tk.DISABLED)

    def append_text(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, text)
        self.text_area.config(state=tk.DISABLED)

    def clear(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete('1.0', tk.END)
        self.text_area.config(state=tk.DISABLED)

    def get_content(self):
        return self.text_area.get('1.0', tk.END).strip()