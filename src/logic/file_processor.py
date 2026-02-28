import os


def process_directory_content(base_path, ignored_extensions=None, ignored_folders=None):
    if ignored_extensions is None:
        ignored_extensions = []
    if ignored_folders is None:
        ignored_folders = []

    ignored_folders_set = set(ignored_folders)

    is_first_file = True
    total_lines = 0
    
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignored_folders_set]

        for filename in sorted(files):
            if any(filename.lower().endswith(ext.lower()) for ext in ignored_extensions):
                continue

            file_path = os.path.join(root, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                content = "".join(lines)
                relative_path = os.path.relpath(file_path, base_path).replace('\\', '/')

                header = f"-- {relative_path} --\n"
                if not is_first_file:
                    header = "\n" + header
                is_first_file = False

                total_lines += len(lines)
                yield "data", header, content + "\n", total_lines
            except Exception as e:
                print(f"Erreur lecture fichier {file_path}: {e}")


def process_directory_architecture(base_path, folders_only=False, ignored_extensions=None, ignored_folders=None):
    if ignored_extensions is None:
        ignored_extensions = []
    if ignored_folders is None:
        ignored_folders = []

    ignored_folders_set = set(ignored_folders)

    element_count = 1
    yield "data", f"{os.path.basename(base_path)}/\n", element_count

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in ignored_folders_set]
        dirs.sort()

        level = root.replace(base_path, '').count(os.sep)
        indent = '│   ' * level

        if not folders_only and ignored_extensions:
            files = [f for f in files if not any(f.lower().endswith(ext.lower()) for ext in ignored_extensions)]
            files.sort()

        entries = dirs
        if not folders_only:
            entries = dirs + files

        for i, name in enumerate(entries):
            is_last = i == (len(entries) - 1)
            prefix = '└── ' if is_last else '├── '
            display_name = name
            
            if os.path.isdir(os.path.join(root, name)):
                display_name += '/'

            element_count += 1
            yield "data", f"{indent}{prefix}{display_name}\n", element_count


def process_project_directory(base_path, ignored_extensions=None, ignored_folders=None):
    if ignored_extensions is None:
        ignored_extensions = []
    if ignored_folders is None:
        ignored_folders = []

    ignored_folders_set = set(ignored_folders)

    backend_exclude = {'venv', '__pycache__'}
    frontend_exclude = {'bin', 'obj', 'AppIcon', 'Fonts', 'Images', 'Raw', 'Splash', 'Properties'}
    uploads_exclude = {'annals', 'tutorials'}
    
    is_first_file = True
    total_lines = 0

    for root, dirs, files in os.walk(base_path, topdown=True):
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        dirs[:] = [d for d in dirs if d not in ignored_folders_set]

        if 'backend' in root:
            dirs[:] = [d for d in dirs if d not in backend_exclude]
        elif 'frontend' in root:
            dirs[:] = [d for d in dirs if d not in frontend_exclude]
        elif 'uploads' in root:
            dirs[:] = [d for d in dirs if d not in uploads_exclude]

        for filename in sorted(files):
            if filename.startswith('.'):
                continue

            if any(filename.lower().endswith(ext.lower()) for ext in ignored_extensions):
                continue

            file_path = os.path.join(root, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                content = "".join(lines)
                relative_path = os.path.relpath(file_path, base_path).replace('\\', '/')

                header = f"-- {relative_path} --\n"
                if not is_first_file:
                    header = "\n" + header
                is_first_file = False

                total_lines += len(lines)
                yield "data", header, content + "\n", total_lines
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {file_path}: {e}")


# === Mode Flutter ===
def process_flutter_project(base_path, ignored_extensions=None, ignored_folders=None):
    if ignored_extensions is None:
        ignored_extensions = []
    if ignored_folders is None:
        ignored_folders = []

    # Ignorer les dossiers de build et caches Flutter classiques
    flutter_ignored = {
        '.dart_tool', 'build', '.pub-cache', '.fvm', 
        'ios/Pods', 'macos/Pods', '.git', '.idea'
    }
    ignored_folders_set = set(ignored_folders).union(flutter_ignored)

    # Extensions utiles pour un projet Flutter complet
    relevant_extensions = {
        '.dart',       # Code source
        '.yaml',       # pubspec.yaml, analysis_options.yaml
        '.gradle',     # build.gradle (Android)
        '.xml',        # AndroidManifest.xml
        '.plist',      # Info.plist (iOS)
        '.properties', # android.properties
        '.json',       # Configs diverses
        '.arb'         # Fichiers de traduction (l10n)
    }

    is_first_file = True
    total_lines = 0

    for root, dirs, files in os.walk(base_path):
        # Filtrage des dossiers
        dirs[:] = [d for d in dirs if d not in ignored_folders_set and not d.startswith('.')]

        for filename in sorted(files):
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, base_path).replace('\\', '/')
            
            # Gestion du dossier ASSETS (et sous-dossiers)
            # Si le chemin contient "assets/" ou "images/" ou "fonts/", on affiche juste le nom
            path_parts = relative_path.lower().split('/')
            is_asset = any(x in path_parts for x in ['assets', 'images', 'fonts', 'raw'])
            
            # Si c'est un asset (et pas un fichier de code égaré dedans), on liste juste le nom
            if is_asset and not filename.endswith('.dart'):
                header = f"-- [ASSET] {relative_path} --\n"
                if not is_first_file:
                    header = "\n" + header
                is_first_file = False
                # On yield un contenu vide pour les assets
                yield "data", header, "(Contenu binaire ou statique ignoré)\n", total_lines
                continue

            # Vérification des extensions ignorées globalement
            if any(filename.lower().endswith(ext.lower()) for ext in ignored_extensions):
                continue

            # Vérification si c'est un fichier pertinent pour Flutter
            is_relevant = any(filename.lower().endswith(ext) for ext in relevant_extensions)
            
            # Cas particuliers (fichiers sans extensions ou spécifiques)
            if filename == 'Podfile' or filename == 'Gemfile':
                is_relevant = True

            if is_relevant:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    content = "".join(lines)
                    header = f"-- {relative_path} --\n"
                    if not is_first_file:
                        header = "\n" + header
                    is_first_file = False

                    total_lines += len(lines)
                    yield "data", header, content + "\n", total_lines
                except Exception as e:
                    print(f"Erreur lecture {file_path}: {e}")