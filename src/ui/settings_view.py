import tkinter as tk
from tkinter import ttk, scrolledtext

class SettingsView(ttk.Frame):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        
        self.create_widgets()

    def create_widgets(self):
        title_label = ttk.Label(self, text="Paramètres", font=("Segoe UI Variable", 16, "bold"))
        title_label.pack(pady=10)

        ext_label = ttk.Label(self, text="Extensions de fichiers à ignorer (ex: .exe)", 
                              style="Secondary.TLabel")
        ext_label.pack(pady=(5, 0))
        self.extensions_text = scrolledtext.ScrolledText(self, width=60, height=8, font=("Consolas", 9))
        self.extensions_text.pack(pady=5, padx=10)

        folder_label = ttk.Label(self, text="Noms de dossiers à ignorer (ex: node_modules)", 
                                 style="Secondary.TLabel")
        folder_label.pack(pady=(10, 0))
        self.folders_text = scrolledtext.ScrolledText(self, width=60, height=8, font=("Consolas", 9))
        self.folders_text.pack(pady=5, padx=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        save_btn = ttk.Button(btn_frame, text="💾 Enregistrer", command=self.save_settings, style="Accent.TButton")
        save_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = ttk.Button(btn_frame, text="Annuler", command=self.controller.show_favorites_screen)
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def load_settings(self):
        exts = self.controller.ignored_extensions
        self.extensions_text.delete('1.0', tk.END)
        self.extensions_text.insert('1.0', "\n".join(exts))
        folders = self.controller.ignored_folders
        self.folders_text.delete('1.0', tk.END)
        self.folders_text.insert('1.0', "\n".join(folders))

    def save_settings(self):
        raw_ext = self.extensions_text.get('1.0', tk.END).strip()
        new_extensions = [line.strip() for line in raw_ext.split('\n') if line.strip()]
        raw_folders = self.folders_text.get('1.0', tk.END).strip()
        new_folders = [line.strip() for line in raw_folders.split('\n') if line.strip()]

        self.controller.update_settings(new_extensions, new_folders)