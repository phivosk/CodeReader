# src/app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os

# Thèmes et style
import sv_ttk
import darkdetect
from src.utils.windows_style import apply_windows_titlebar_style

# Modules de l'application
from src.logic.config_manager import ConfigManager
from src.logic import file_processor, comment_processor
from src.ui.favorites_view import FavoritesView
from src.ui.text_view import TextView
from src.ui.comment_remover_view import CommentRemoverView


class DirectoryReaderApp(tk.Tk):
    def __init__(self):
        super().__init__()

        sv_ttk.set_theme(darkdetect.theme() or "light")
        apply_windows_titlebar_style(self)
        self.title("Lecteur & Nettoyeur de Code")
        self.geometry("800x650")

        # Variables d'état pour le lecteur de dossier
        self.current_directory = None
        self.mode = 'content'
        self.saved_paths = ConfigManager.load_saved_paths()

        # Variables d'état pour le nettoyeur de commentaires
        self.kept_comments = ConfigManager.load_kept_comments()
        self.comment_files_to_process = []
        self.current_comment_file_index = 0
        self.current_comment_iterator = None
        self.current_comment_info = None

        self.create_widgets()
        self.show_favorites_screen()

    def create_widgets(self):
        style = ttk.Style()
        style.configure('Danger.TButton', foreground='red')

        top_frame = ttk.Frame(self, padding=(10, 5))
        top_frame.pack(fill=tk.X)

        self.home_button = ttk.Button(top_frame, text="🏠 Accueil", command=self.show_favorites_screen)
        self.select_button = ttk.Button(top_frame, text="📂 Lire un dossier", command=self.select_directory_for_content,
                                        style="Accent.TButton")
        self.select_button.pack(side=tk.LEFT)
        self.copy_button = ttk.Button(top_frame, text="📋 Copier", command=self.copy_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=10)

        right_frame = ttk.Frame(top_frame)
        right_frame.pack(side=tk.RIGHT)
        self.save_button = ttk.Button(right_frame, text="💾 Enregistrer", command=self.save_current_path,
                                      state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)
        self.refresh_button = ttk.Button(right_frame, text="🔄 Refresh", command=self.refresh_directory,
                                         state=tk.DISABLED)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(right_frame, text="Prêt")
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.main_container = ttk.Frame(self)
        self.main_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        self.favorites_view = FavoritesView(self.main_container, self, self.saved_paths)
        self.text_view = TextView(self.main_container)
        self.comment_remover_view = CommentRemoverView(self.main_container, self)

    def show_favorites_screen(self):
        self.text_view.pack_forget()
        self.comment_remover_view.pack_forget()
        self.home_button.pack_forget()

        self.select_button.pack(side=tk.LEFT, before=self.copy_button)  # Rendre le bouton visible

        self.favorites_view.saved_paths = self.saved_paths
        self.favorites_view.create_widgets()
        self.favorites_view.pack(expand=True, fill=tk.BOTH)

        self.status_label.config(text="Prêt")
        for btn in [self.copy_button, self.refresh_button, self.save_button]:
            btn.config(state=tk.DISABLED)

    def show_text_area_screen(self):
        self.favorites_view.pack_forget()
        self.comment_remover_view.pack_forget()
        self.home_button.pack(side=tk.LEFT, padx=(0, 10), before=self.select_button)
        self.select_button.pack(side=tk.LEFT, before=self.copy_button)  # Rendre visible
        self.text_view.pack(expand=True, fill=tk.BOTH)

    def show_comment_remover_screen(self):
        self.text_view.pack_forget()
        self.favorites_view.pack_forget()
        self.home_button.pack(side=tk.LEFT, padx=(0, 10), before=self.select_button)

        self.select_button.pack_forget()  # Cacher le bouton "Lire un dossier" qui n'est pas pertinent ici

        self.comment_remover_view.pack(expand=True, fill=tk.BOTH)
        self.status_label.config(text="Nettoyeur de commentaires")
        for btn in [self.copy_button, self.refresh_button, self.save_button]:
            btn.config(state=tk.DISABLED)

    def start_comment_scan(self):
        project_path = filedialog.askdirectory(title="Choisissez un projet Flutter/Dart")
        if not project_path: return

        self.comment_files_to_process = comment_processor.find_dart_files(project_path)
        if not self.comment_files_to_process:
            messagebox.showinfo("Information", "Aucun fichier .dart n'a été trouvé dans ce dossier.")
            return

        self.current_comment_file_index = 0
        self.process_next_comment_file()

    def process_next_comment_file(self):
        if self.current_comment_file_index < len(self.comment_files_to_process):
            file_path = self.comment_files_to_process[self.current_comment_file_index]
            self.current_comment_iterator = comment_processor.find_comments_in_file(file_path, self.kept_comments)
            self.show_next_comment()
        else:
            self.comment_remover_view.show_final_message("Tous les fichiers ont été traités !")
            messagebox.showinfo("Terminé", "Le traitement de tous les fichiers est terminé.")

    def show_next_comment(self):
        try:
            self.current_comment_info = next(self.current_comment_iterator)
            file_path = self.current_comment_info["file_path"]
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.comment_remover_view.update_display(file_path, self.current_comment_info, lines)
        except StopIteration:
            self.current_comment_file_index += 1
            self.process_next_comment_file()
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue en lisant les commentaires: {e}")

    def keep_comment(self):
        if self.current_comment_info:
            self.kept_comments.add(self.current_comment_info["hash"])
            ConfigManager.save_kept_comments(self.kept_comments)
            self.show_next_comment()

    def discard_comment(self):
        if self.current_comment_info:
            if comment_processor.remove_comment_from_file(self.current_comment_info):
                current_file = self.current_comment_info["file_path"]
                self.current_comment_iterator = comment_processor.find_comments_in_file(current_file,
                                                                                        self.kept_comments)
                self.show_next_comment()
            else:
                messagebox.showerror("Erreur", "La suppression du commentaire a échoué. Passage au suivant.")
                self.show_next_comment()

    def select_directory(self, mode):
        directory_path = filedialog.askdirectory(title="Choisissez un répertoire")
        if directory_path:
            self.current_directory = directory_path
            self.mode = mode
            self.load_directory_content()

    def select_directory_for_content(self):
        self.select_directory('content')

    def select_directory_for_architecture(self):
        self.select_directory('architecture')

    def select_directory_for_folders_only(self):
        self.select_directory('folders_only')

    def select_directory_for_project_scan(self):
        self.select_directory('project_scan')

    def load_favorite(self, path):
        if os.path.isdir(path):
            self.current_directory = path;
            self.mode = 'content'
            self.load_directory_content()
        else:
            if messagebox.askyesno("Erreur", f"Le chemin n'existe plus :\n{path}\n\nVoulez-vous le supprimer?"):
                self.delete_favorite(path)

    def save_current_path(self):
        if not self.current_directory: return
        if any(item['path'] == self.current_directory for item in self.saved_paths):
            messagebox.showinfo("Déjà sauvegardé", "Ce chemin est déjà dans vos favoris.")
            return
        default_name = os.path.basename(self.current_directory)
        fav_name = simpledialog.askstring("Nom du favori", "Entrez un nom pour ce favori :", initialvalue=default_name)
        if fav_name:
            self.saved_paths.append({'name': fav_name, 'path': self.current_directory})
            ConfigManager.save_paths_to_file(self.saved_paths)
            messagebox.showinfo("Sauvegardé", "Le chemin a été ajouté à vos favoris.")

    def delete_favorite(self, path_to_delete):
        if messagebox.askyesno("Confirmer", f"Supprimer ce favori ?\n\n{path_to_delete}"):
            self.saved_paths = [item for item in self.saved_paths if item['path'] != path_to_delete]
            ConfigManager.save_paths_to_file(self.saved_paths)
            self.show_favorites_screen()

    def refresh_directory(self):
        if self.current_directory: self.load_directory_content()

    def copy_to_clipboard(self):
        content = self.text_view.get_content()
        if not content:
            messagebox.showwarning("Presse-papiers", "Il n'y a rien à copier.")
            return
        self.clipboard_clear();
        self.clipboard_append(content)
        messagebox.showinfo("Copié", "Le contenu a été copié dans le presse-papiers.")

    def load_directory_content(self):
        self.show_text_area_screen()
        self.text_view.clear()
        for btn in [self.copy_button, self.refresh_button, self.save_button]:
            btn.config(state=tk.DISABLED)
        self.update_idletasks()

        processor = None
        if self.mode in ['content', 'project_scan']:
            self.status_label.config(text="Lignes lues : 0")
            processor = file_processor.process_project_directory(
                self.current_directory) if self.mode == 'project_scan' else file_processor.process_directory_content(
                self.current_directory)
        elif self.mode in ['architecture', 'folders_only']:
            self.status_label.config(text="Éléments listés : 0")
            processor = file_processor.process_directory_architecture(self.current_directory,
                                                                      self.mode == 'folders_only')

        if processor:
            for type, *args in processor:
                if type == "data":
                    if self.mode in ['content', 'project_scan']:
                        header, content, total_lines = args
                        self.text_view.append_text(header + content)
                        self.status_label.config(text=f"Lignes lues : {total_lines}")
                    else:
                        line, count = args
                        self.text_view.append_text(line)
                        self.status_label.config(text=f"Éléments listés : {count}")
                self.update_idletasks()

        for btn in [self.copy_button, self.refresh_button, self.save_button]:
            btn.config(state=tk.NORMAL)