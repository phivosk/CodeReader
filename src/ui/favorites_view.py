# src/ui/favorites_view.py
import tkinter as tk
from tkinter import ttk


class FavoritesView(ttk.Frame):
    def __init__(self, parent, controller, saved_paths, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.saved_paths = saved_paths

        self.create_widgets()

    def _truncate_text(self, text, max_length):
        """Tronque le texte s'il dépasse une longueur maximale et ajoute '...'."""
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

    def create_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()

        main_fav_frame = ttk.Frame(self)
        main_fav_frame.pack(expand=True, fill=tk.BOTH)

        title_label = ttk.Label(main_fav_frame, text="Dossiers favoris", font=("Segoe UI Variable", 16, "bold"))
        title_label.pack(pady=10)

        if not self.saved_paths:
            no_fav_label = ttk.Label(
                main_fav_frame,
                text="Aucun favori.\nSélectionnez un dossier et cliquez sur 💾 pour en ajouter un.",
                justify=tk.CENTER,
                style="Secondary.TLabel"
            )
            no_fav_label.pack(pady=20)
        else:
            for fav_item in self.saved_paths:
                item_frame = ttk.Frame(main_fav_frame, style="Card.TFrame", padding=10)
                content_frame = ttk.Frame(item_frame)

                truncated_name = self._truncate_text(fav_item['name'], 50)
                truncated_path = self._truncate_text(fav_item['path'], 70)

                name_label = ttk.Label(content_frame, text=truncated_name, font=("Segoe UI Variable", 12, "bold"),
                                       anchor='w')
                path_label = ttk.Label(content_frame, text=truncated_path, style="Secondary.TLabel", anchor='w')
                name_label.pack(fill=tk.X)
                path_label.pack(fill=tk.X)

                for widget in [content_frame, name_label, path_label]:
                    widget.bind("<Button-1>", lambda e, p=fav_item['path']: self.controller.load_favorite(p))

                content_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                delete_button = ttk.Button(
                    item_frame, text="❌",
                    command=lambda p=fav_item['path']: self.controller.delete_favorite(p),
                    style='Danger.TButton'
                )
                delete_button.pack(side=tk.RIGHT, padx=(10, 0))
                item_frame.pack(fill=tk.X, padx=50, pady=4)

        bottom_frame = ttk.Frame(self, padding=(10, 10))
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        comment_remover_button = ttk.Button(
            bottom_frame, text="Nettoyer les commentaires...",
            command=self.controller.show_comment_remover_screen
        )
        comment_remover_button.pack(side=tk.LEFT)

        project_scan_button = ttk.Button(
            bottom_frame, text="Scanner un projet (Py/C#)...",
            command=self.controller.select_directory_for_project_scan
        )
        project_scan_button.pack(side=tk.LEFT, padx=(10, 0))

        folders_only_button = ttk.Button(
            bottom_frame, text="Afficher les dossiers seuls...",
            command=self.controller.select_directory_for_folders_only
        )
        folders_only_button.pack(side=tk.RIGHT, padx=(5, 0))

        architecture_button = ttk.Button(
            bottom_frame, text="Afficher l'architecture complète...",
            command=self.controller.select_directory_for_architecture
        )
        architecture_button.pack(side=tk.RIGHT)