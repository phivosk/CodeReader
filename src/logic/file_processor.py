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