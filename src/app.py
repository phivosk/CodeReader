import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import threading
import queue

import sv_ttk
import darkdetect
from src.utils.windows_style import apply_windows_titlebar_style

from src.logic.config_manager import ConfigManager
from src.logic import file_processor, comment_processor
from src.ui.favorites_view import FavoritesView
from src.ui.text_view import TextView
from src.ui.comment_remover_view import CommentRemoverView
from src.ui.settings_view import SettingsView


class DirectoryReaderApp(tk.Tk):
    def __init__(self):
        super().__init__()

        sv_ttk.set_theme(darkdetect.theme() or "light")
        apply_windows_titlebar_style(self)
        self.title("Lecteur & Nettoyeur de Code")
        self.geometry("900x700")

        self.current_directory = None
        self.mode = 'content'
        
        self.saved_paths = ConfigManager.load_saved_paths()
        self.kept_comments = ConfigManager.load_kept_comments()
        self.ignored_extensions = ConfigManager.load_ignored_extensions()
        self.ignored_folders = ConfigManager.load_ignored_folders()

        self.comment_files_to_process = []
        self.current_comment_file_index = 0
        self.current_comment_iterator = None
        self.current_comment_info = None

        self.msg_queue = queue.Queue()
        self.is_processing = False

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
        
        self.status_frame = ttk.Frame(right_frame)
        self.status_frame.pack(side=tk.LEFT, padx=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Prêt")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='indeterminate', length=100)

        self.main_container = ttk.Frame(self)
        self.main_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        self.favorites_view = FavoritesView(self.main_container, self, self.saved_paths)
        self.text_view = TextView(self.main_container)
        self.comment_remover_view = CommentRemoverView(self.main_container, self)
        self.settings_view = SettingsView(self.main_container, self)


    def show_favorites_screen(self):
        self._hide_all_views()
        self.home_button.pack_forget()
        self.select_button.pack(side=tk.LEFT, before=self.copy_button)
        
        self.favorites_view.saved_paths = self.saved_paths
        self.favorites_view.create_widgets()
        self.favorites_view.pack(expand=True, fill=tk.BOTH)
        
        self.status_label.config(text="Prêt")
        self._disable_action_buttons()

    def show_text_area_screen(self):
        self._hide_all_views()
        self.home_button.pack(side=tk.LEFT, padx=(0, 10), before=self.select_button)
        self.select_button.pack(side=tk.LEFT, before=self.copy_button)
        self.text_view.pack(expand=True, fill=tk.BOTH)

    def show_comment_remover_screen(self):
        self._hide_all_views()
        self.home_button.pack(side=tk.LEFT, padx=(0, 10), before=self.select_button)
        self.select_button.pack_forget()
        self.comment_remover_view.pack(expand=True, fill=tk.BOTH)
        self.status_label.config(text="Nettoyeur de commentaires")
        self._disable_action_buttons()

    def show_settings_screen(self):
        self._hide_all_views()
        self.home_button.pack_forget()
        self.select_button.pack_forget()
        self._disable_action_buttons()
        
        self.settings_view.load_settings()
        self.settings_view.pack(expand=True, fill=tk.BOTH)
        self.status_label.config(text="Configuration")

    def _hide_all_views(self):
        self.favorites_view.pack_forget()
        self.text_view.pack_forget()
        self.comment_remover_view.pack_forget()
        self.settings_view.pack_forget()
        
    def _disable_action_buttons(self):
        for btn in [self.copy_button, self.refresh_button, self.save_button]:
            btn.config(state=tk.DISABLED)
            
    def _enable_action_buttons(self):
        for btn in [self.copy_button, self.refresh_button, self.save_button]:
            btn.config(state=tk.NORMAL)

    def start_comment_scan(self):
        project_path = filedialog.askdirectory(title="Choisissez un projet (Dart/Python)")
        if not project_path: return
        self.comment_files_to_process = comment_processor.find_code_files(project_path)
        if not self.comment_files_to_process:
            messagebox.showinfo("Information", "Aucun fichier .dart ou .py n'a été trouvé.")
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
            messagebox.showinfo("Terminé", "Traitement terminé.")

    def show_next_comment(self):
        try:
            self.current_comment_info = next(self.current_comment_iterator)
            file_path = self.current_comment_info["file_path"]
            with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
            self.comment_remover_view.update_display(file_path, self.current_comment_info, lines)
        except StopIteration:
            self.current_comment_file_index += 1
            self.process_next_comment_file()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lecture commentaires: {e}")

    def keep_comment(self):
        if self.current_comment_info:
            self.kept_comments.add(self.current_comment_info["hash"])
            ConfigManager.save_kept_comments(self.kept_comments)
            self.show_next_comment()

    def discard_comment(self):
        if self.current_comment_info:
            if comment_processor.remove_comment_from_file(self.current_comment_info):
                current_file = self.current_comment_info["file_path"]
                self.current_comment_iterator = comment_processor.find_comments_in_file(current_file, self.kept_comments)
                self.show_next_comment()
            else:
                self.show_next_comment()


    def select_directory(self, mode):
        directory_path = filedialog.askdirectory(title="Choisissez un répertoire")
        if directory_path:
            self.current_directory = directory_path
            self.mode = mode
            self.load_directory_content()

    def select_directory_for_content(self): self.select_directory('content')
    def select_directory_for_architecture(self): self.select_directory('architecture')
    def select_directory_for_folders_only(self): self.select_directory('folders_only')
    def select_directory_for_project_scan(self): self.select_directory('project_scan')
    def select_directory_for_flutter_scan(self):
        self.select_directory('flutter')

    def load_favorite(self, path, mode='content'):
        """Charge un favori avec son mode spécifique."""
        if os.path.isdir(path):
            self.current_directory = path
            self.mode = mode  # On applique le mode sauvegardé (ex: 'flutter')
            self.load_directory_content()
        else:
            if messagebox.askyesno("Erreur", f"Chemin introuvable :\n{path}\nSupprimer ?"):
                self.delete_favorite(path)

    def update_settings(self, new_extensions, new_folders):
        self.ignored_extensions = new_extensions
        self.ignored_folders = new_folders
        ConfigManager.save_ignored_extensions(self.ignored_extensions)
        ConfigManager.save_ignored_folders(self.ignored_folders)
        messagebox.showinfo("Succès", "Paramètres sauvegardés.")
        self.show_favorites_screen()

    
    def load_directory_content(self):
        self.show_text_area_screen()
        self.text_view.clear()
        self._disable_action_buttons()
        
        self.status_label.config(text="Chargement en cours...")
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        self.progress_bar.start(10)

        self.is_processing = True
        
        threading.Thread(target=self._background_scan_task, daemon=True).start()
        
        self.after(100, self._process_queue_msg)

    def _background_scan_task(self):
        try:
            processor = None
            if self.mode == 'project_scan':
                processor = file_processor.process_project_directory(
                    self.current_directory, self.ignored_extensions, self.ignored_folders
                )
            elif self.mode == 'flutter':
                processor = file_processor.process_flutter_project(
                    self.current_directory, self.ignored_extensions, self.ignored_folders
                )
            elif self.mode == 'content':
                processor = file_processor.process_directory_content(
                    self.current_directory, self.ignored_extensions, self.ignored_folders
                )
            elif self.mode in ['architecture', 'folders_only']:
                processor = file_processor.process_directory_architecture(
                    self.current_directory, self.mode == 'folders_only',
                    self.ignored_extensions, self.ignored_folders
                )

            if processor:
                batch_text = []
                count = 0
                
                for type, *args in processor:
                    if not self.is_processing: break
                    
                    if type == "data":
                        if self.mode in ['content', 'project_scan', 'flutter']:
                            header, content, total_lines = args
                            self.msg_queue.put(("append", header + content))
                            self.msg_queue.put(("status", f"Lignes lues : {total_lines}"))
                        else:
                            line, total_elements = args
                            self.msg_queue.put(("append", line))
                            self.msg_queue.put(("status", f"Éléments : {total_elements}"))

            self.msg_queue.put(("done", None))

        except Exception as e:
            self.msg_queue.put(("error", str(e)))

    def _process_queue_msg(self):
        try:
            for _ in range(50): 
                msg_type, data = self.msg_queue.get_nowait()
                
                if msg_type == "append":
                    self.text_view.append_text(data)
                elif msg_type == "status":
                    self.status_label.config(text=data)
                elif msg_type == "error":
                    messagebox.showerror("Erreur", f"Erreur durant le scan : {data}")
                elif msg_type == "done":
                    self._finish_loading()
                    return
                
            if self.is_processing:
                self.after(50, self._process_queue_msg)
                
        except queue.Empty:
            if self.is_processing:
                self.after(50, self._process_queue_msg)

    def _finish_loading(self):
        self.is_processing = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self._enable_action_buttons()
        if self.text_view.get_content() == "":
            self.text_view.append_text("Aucun contenu trouvé avec les filtres actuels.")

    def save_current_path(self):
        if not self.current_directory: return
        # Vérification si déjà existant (sur le path uniquement)
        if any(item['path'] == self.current_directory for item in self.saved_paths):
            messagebox.showinfo("Info", "Ce dossier est déjà dans les favoris.")
            return
        default_name = os.path.basename(self.current_directory)
        fav_name = simpledialog.askstring("Favori", "Nom :", initialvalue=default_name)
        if fav_name:
            # ON SAUVEGARDE LE MODE ACTUEL (self.mode)
            self.saved_paths.append({
                'name': fav_name, 
                'path': self.current_directory, 
                'mode': self.mode 
            })
            ConfigManager.save_paths_to_file(self.saved_paths)
            messagebox.showinfo("Sauvegardé", f"Ajouté aux favoris en mode '{self.mode}'.")

    def delete_favorite(self, path):
        if messagebox.askyesno("Confirmer", "Supprimer ce favori ?"):
            self.saved_paths = [i for i in self.saved_paths if i['path'] != path]
            ConfigManager.save_paths_to_file(self.saved_paths)
            self.show_favorites_screen()

    def refresh_directory(self):
        if self.current_directory: self.load_directory_content()

    def copy_to_clipboard(self):
        content = self.text_view.get_content()
        if not content: return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copié", "Contenu copié.")

if __name__ == "__main__":
    app = DirectoryReaderApp()
    app.mainloop()