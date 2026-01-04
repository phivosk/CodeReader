# src/logic/config_manager.py
import os
import json
from tkinter import messagebox
from src.utils.constants import APP_CONFIG_DIR, SAVED_PATHS_FILE as FAVORITES_FILE

# Constante pour le nouveau fichier de configuration des commentaires
KEPT_COMMENTS_FILE = os.path.join(APP_CONFIG_DIR, 'kept_comments.json')

class ConfigManager:
    """Gère le chargement et la sauvegarde des configurations de l'application."""

    @staticmethod
    def load_saved_paths():
        """Charge les chemins favoris depuis le fichier JSON."""
        try:
            if os.path.exists(FAVORITES_FILE):
                with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Compatibilité avec l'ancien format (liste de chaînes)
                if data and isinstance(data[0], str):
                    saved_paths = [{'name': os.path.basename(p), 'path': p} for p in data]
                    ConfigManager.save_paths_to_file(saved_paths) # Met à jour vers le nouveau format
                    return saved_paths
                return data
        except (IOError, json.JSONDecodeError, IndexError):
            return []
        return []

    @staticmethod
    def save_paths_to_file(paths):
        """Sauvegarde la liste des chemins favoris dans le fichier JSON."""
        try:
            os.makedirs(APP_CONFIG_DIR, exist_ok=True)
            with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
                json.dump(paths, f, indent=4)
        except IOError as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder les favoris : {e}")

    @staticmethod
    def load_kept_comments():
        """Charge les hashes des commentaires à conserver."""
        try:
            if os.path.exists(KEPT_COMMENTS_FILE):
                with open(KEPT_COMMENTS_FILE, "r") as f:
                    return set(json.load(f))
        except (IOError, json.JSONDecodeError):
            return set()
        return set()

    @staticmethod
    def save_kept_comments(hashes_set):
        """Sauvegarde les hashes des commentaires à conserver."""
        try:
            os.makedirs(APP_CONFIG_DIR, exist_ok=True)
            with open(KEPT_COMMENTS_FILE, "w") as f:
                json.dump(list(hashes_set), f, indent=4)
        except IOError as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder les commentaires : {e}")