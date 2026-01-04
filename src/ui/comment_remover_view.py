# src/ui/comment_remover_view.py
import tkinter as tk
from tkinter import ttk, scrolledtext

class CommentRemoverView(ttk.Frame):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller

        self.select_button = ttk.Button(self, text="📂 Sélectionner un projet à nettoyer",
                                        command=self.controller.start_comment_scan, style="Accent.TButton")
        self.select_button.pack(pady=10)

        self.file_path_label = ttk.Label(self, text="Aucun projet sélectionné", style="Secondary.TLabel")
        self.file_path_label.pack(pady=(0, 5))

        context_label = ttk.Label(self, text="Contexte du commentaire :", font=("Segoe UI Variable", 14))
        context_label.pack()

        self.context_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=20, width=100, font=("Courier New", 10))
        self.context_text.pack(pady=10, fill=tk.BOTH, expand=True)
        self.context_text.tag_config("comment", background="#FDDC5C", foreground="black") # Jaune plus doux

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        self.keep_button = ttk.Button(button_frame, text="✅ Garder", command=self.controller.keep_comment)
        self.keep_button.pack(side=tk.LEFT, padx=10)

        self.discard_button = ttk.Button(button_frame, text="❌ Jeter", command=self.controller.discard_comment, style="Danger.TButton")
        self.discard_button.pack(side=tk.RIGHT, padx=10)

        self.disable_buttons()

    def disable_buttons(self):
        self.keep_button.config(state=tk.DISABLED)
        self.discard_button.config(state=tk.DISABLED)

    def enable_buttons(self):
        self.keep_button.config(state=tk.NORMAL)
        self.discard_button.config(state=tk.NORMAL)

    def update_display(self, file_path, comment_info, lines):
        """Met à jour l'affichage avec le prochain commentaire à traiter."""
        self.file_path_label.config(text=f"Fichier : {file_path}")
        start = comment_info["start_line"]
        end = comment_info["end_line"]

        context_start = max(0, start - 5)
        context_end = min(len(lines), end + 6)

        self.context_text.config(state=tk.NORMAL)
        self.context_text.delete(1.0, tk.END)
        for i in range(context_start, context_end):
            if start <= i <= end:
                self.context_text.insert(tk.END, f"{i + 1:4d} > {lines[i]}", "comment")
            else:
                self.context_text.insert(tk.END, f"{i + 1:4d}   {lines[i]}")
        self.context_text.config(state=tk.DISABLED)
        self.enable_buttons()

    def show_final_message(self, message):
        """Affiche un message de fin dans la zone de texte."""
        self.file_path_label.config(text="Terminé !")
        self.context_text.config(state=tk.NORMAL)
        self.context_text.delete(1.0, tk.END)
        self.context_text.insert(tk.END, message)
        self.context_text.config(state=tk.DISABLED)
        self.disable_buttons()