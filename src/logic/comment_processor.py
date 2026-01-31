import os
import hashlib

def find_code_files(directory):
    """Trouve tous les fichiers .dart et .py dans un répertoire."""
    code_files = []
    supported_extensions = ('.dart', '.py')
    for root_dir, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_extensions):
                code_files.append(os.path.join(root_dir, file))
    return code_files

def get_comment_hash(comment_content):
    """Génère un hash SHA256 pour un contenu de commentaire."""
    return hashlib.sha256(comment_content.strip().encode('utf-8')).hexdigest()

def _is_in_string(line, index):
    """Vérifie si un index est à l'intérieur d'une chaîne (pour C-style/Dart)."""
    sub_line = line[:index]
    single_quotes = sub_line.count("'")
    double_quotes = sub_line.count('"')
    return single_quotes % 2 != 0 or double_quotes % 2 != 0

def find_comments_in_file(file_path, kept_comments_hashes):
    """Dispatche vers le bon parseur selon l'extension."""
    if file_path.endswith('.dart'):
        yield from _find_dart_comments(file_path, kept_comments_hashes)
    elif file_path.endswith('.py'):
        yield from _find_python_comments(file_path, kept_comments_hashes)

def _find_dart_comments(file_path, kept_comments_hashes):
    """Logique originale pour Dart (C-Style)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
        return

    in_multiline_comment = False
    comment_buffer = []
    comment_start_line = -1

    for i, line in enumerate(lines):
        if in_multiline_comment:
            comment_buffer.append(line)
            end_ml_index = line.find('*/')
            if end_ml_index != -1 and not _is_in_string(line, end_ml_index):
                in_multiline_comment = False
                full_comment = "".join(comment_buffer)
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "dart", "start_line": comment_start_line, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
                comment_buffer = []
        else:
            sl_index = line.find('//')
            start_ml_index = line.find('/*')

            if start_ml_index != -1 and (sl_index == -1 or start_ml_index < sl_index):
                if not _is_in_string(line, start_ml_index):
                    in_multiline_comment = True
                    comment_start_line = i
                    comment_buffer.append(line)
                    end_ml_index = line.find('*/', start_ml_index + 2)
                    if end_ml_index != -1 and not _is_in_string(line, end_ml_index):
                        in_multiline_comment = False
                        full_comment = "".join(comment_buffer)
                        comment_hash = get_comment_hash(full_comment)
                        if comment_hash not in kept_comments_hashes:
                            yield {"file_path": file_path, "type": "dart", "start_line": i, "end_line": i, "content": full_comment,
                                   "hash": comment_hash}
                        comment_buffer = []

            elif sl_index != -1:
                if not _is_in_string(line, sl_index):
                    comment_hash = get_comment_hash(line[sl_index:])
                    if comment_hash not in kept_comments_hashes:
                        yield {"file_path": file_path, "type": "dart", "start_line": i, "end_line": i, "content": line,
                               "hash": comment_hash}

def _find_python_comments(file_path, kept_comments_hashes):
    """Logique spécifique pour Python (# et Docstrings)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
        return

    in_docstring = False
    docstring_marker = None # """ ou '''
    comment_buffer = []
    comment_start_line = -1

    for i, line in enumerate(lines):
        # 1. Gestion des Docstrings (Multi-lignes)
        if in_docstring:
            comment_buffer.append(line)
            if docstring_marker in line:
                # Simplification: on suppose que si on trouve le marker, ça ferme le docstring
                in_docstring = False
                full_comment = "".join(comment_buffer)
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "python_doc", "start_line": comment_start_line, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
                comment_buffer = []
            continue

        # Détection début Docstring (""" ou ''')
        triple_single = "'''"
        triple_double = '"""'
        
        found_marker = None
        if triple_double in line: found_marker = triple_double
        elif triple_single in line: found_marker = triple_single

        if found_marker:
            start_idx = line.find(found_marker)
            end_idx = line.find(found_marker, start_idx + 3)
            
            if end_idx != -1:
                # Docstring sur une seule ligne
                full_comment = line
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "python_doc", "start_line": i, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
            else:
                # Début docstring multi-lignes
                in_docstring = True
                docstring_marker = found_marker
                comment_start_line = i
                comment_buffer.append(line)
            continue

        # 2. Gestion des commentaires simples (#)
        hash_index = line.find('#')
        if hash_index != -1:
            # Vérification basique si dans une string
            if not _is_in_string(line, hash_index):
                comment_hash = get_comment_hash(line[hash_index:])
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "python_single", "start_line": i, "end_line": i, "content": line,
                           "hash": comment_hash}

def remove_comment_from_file(comment_info):
    """Supprime un commentaire d'un fichier selon son type."""
    file_path = comment_info["file_path"]
    c_type = comment_info.get("type", "dart")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_line = comment_info["start_line"]
        end_line = comment_info["end_line"]

        # Suppression complète des lignes si c'est un bloc multi-lignes
        if start_line != end_line:
            new_lines = lines[:start_line] + lines[end_line + 1:]
        
        else:
            # Gestion Mono-ligne
            line_content = lines[start_line]
            
            if c_type == "python_doc":
                # Docstring sur une ligne -> on supprime toute la ligne
                new_lines = lines[:start_line] + lines[end_line + 1:]
            
            elif c_type == "python_single":
                # Commentaire Python (#)
                hash_index = line_content.find('#')
                if hash_index != -1:
                    # Si le # est au début (ou après des espaces), on vire la ligne
                    if line_content[:hash_index].strip() == "":
                         new_lines = lines[:start_line] + lines[end_line + 1:]
                    else:
                        # Commentaire inline (code = x # comment)
                        new_lines = lines[:start_line] + [line_content[:hash_index].rstrip() + '\n'] + lines[start_line + 1:]
                else:
                    new_lines = lines
            
            else: 
                # Logique C-Style / Dart
                if line_content.strip().startswith('//') or line_content.strip().startswith('/*'):
                     new_lines = lines[:start_line] + lines[end_line + 1:]
                else:
                    sl_index = line_content.find('//')
                    if sl_index != -1:
                        new_lines = lines[:start_line] + [line_content[:sl_index].rstrip() + '\n'] + lines[start_line + 1:]
                    else:
                         new_lines = lines[:start_line] + lines[end_line + 1:]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Erreur lors de la modification du fichier {file_path}: {e}")
        return False


def get_comment_hash(comment_content):
    """Génère un hash SHA256 pour un contenu de commentaire."""
    return hashlib.sha256(comment_content.strip().encode('utf-8')).hexdigest()


def _is_in_string(line, index):
    """Vérifie si un index est à l'intérieur d'une chaîne (pour C-style/Dart)."""
    sub_line = line[:index]
    single_quotes = sub_line.count("'")
    double_quotes = sub_line.count('"')
    return single_quotes % 2 != 0 or double_quotes % 2 != 0


def find_comments_in_file(file_path, kept_comments_hashes):
    """Dispatche vers le bon parseur selon l'extension."""
    if file_path.endswith('.dart'):
        yield from _find_dart_comments(file_path, kept_comments_hashes)
    elif file_path.endswith('.py'):
        yield from _find_python_comments(file_path, kept_comments_hashes)


def _find_dart_comments(file_path, kept_comments_hashes):
    """Logique originale pour Dart (C-Style)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
        return

    in_multiline_comment = False
    comment_buffer = []
    comment_start_line = -1

    for i, line in enumerate(lines):
        if in_multiline_comment:
            comment_buffer.append(line)
            end_ml_index = line.find('*/')
            if end_ml_index != -1 and not _is_in_string(line, end_ml_index):
                in_multiline_comment = False
                full_comment = "".join(comment_buffer)
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "dart", "start_line": comment_start_line, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
                comment_buffer = []
        else:
            sl_index = line.find('//')
            start_ml_index = line.find('/*')

            if start_ml_index != -1 and (sl_index == -1 or start_ml_index < sl_index):
                if not _is_in_string(line, start_ml_index):
                    in_multiline_comment = True
                    comment_start_line = i
                    comment_buffer.append(line)
                    end_ml_index = line.find('*/', start_ml_index + 2)
                    if end_ml_index != -1 and not _is_in_string(line, end_ml_index):
                        in_multiline_comment = False
                        full_comment = "".join(comment_buffer)
                        comment_hash = get_comment_hash(full_comment)
                        if comment_hash not in kept_comments_hashes:
                            yield {"file_path": file_path, "type": "dart", "start_line": i, "end_line": i, "content": full_comment,
                                   "hash": comment_hash}
                        comment_buffer = []

            elif sl_index != -1:
                if not _is_in_string(line, sl_index):
                    comment_hash = get_comment_hash(line[sl_index:])
                    if comment_hash not in kept_comments_hashes:
                        yield {"file_path": file_path, "type": "dart", "start_line": i, "end_line": i, "content": line,
                               "hash": comment_hash}


def _find_python_comments(file_path, kept_comments_hashes):
    """Logique spécifique pour Python (# et Docstrings)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
        return

    in_docstring = False
    docstring_marker = None # """ ou '''
    comment_buffer = []
    comment_start_line = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 1. Gestion des Docstrings (Multi-lignes)
        if in_docstring:
            comment_buffer.append(line)
            if docstring_marker in line:
                # Attention: il faut vérifier que le marker n'est pas le début d'une nouvelle string sur la même ligne
                # Simplification: on suppose que si on trouve le marker, ça ferme le docstring
                in_docstring = False
                full_comment = "".join(comment_buffer)
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "python_doc", "start_line": comment_start_line, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
                comment_buffer = []
            continue

        # Détection début Docstring
        # On cherche """ ou '''
        # Note: ceci est une heuristique, ça peut détecter des chaines assignées à des variables
        triple_single = "'''"
        triple_double = '"""'
        
        found_marker = None
        if triple_double in line: found_marker = triple_double
        elif triple_single in line: found_marker = triple_single

        if found_marker:
            # Vérifier si c'est une ouverture
            start_idx = line.find(found_marker)
            # Vérifier si ça ferme sur la même ligne
            end_idx = line.find(found_marker, start_idx + 3)
            
            if end_idx != -1:
                # Docstring sur une seule ligne
                full_comment = line
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "python_doc", "start_line": i, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
            else:
                # Début docstring multi-lignes
                in_docstring = True
                docstring_marker = found_marker
                comment_start_line = i
                comment_buffer.append(line)
            continue

        # 2. Gestion des commentaires simples (#)
        hash_index = line.find('#')
        if hash_index != -1:
            # Vérification basique si dans une string
            if not _is_in_string(line, hash_index):
                comment_hash = get_comment_hash(line[hash_index:])
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "type": "python_single", "start_line": i, "end_line": i, "content": line,
                           "hash": comment_hash}


def remove_comment_from_file(comment_info):
    """Supprime un commentaire d'un fichier selon son type."""
    file_path = comment_info["file_path"]
    c_type = comment_info.get("type", "dart") # par défaut dart pour compatibilité

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_line = comment_info["start_line"]
        end_line = comment_info["end_line"]

        # Suppression complète des lignes si c'est un bloc multi-lignes
        if start_line != end_line:
            new_lines = lines[:start_line] + lines[end_line + 1:]
        
        else:
            # Gestion Mono-ligne
            line_content = lines[start_line]
            
            if c_type == "python_doc":
                # Docstring sur une ligne -> on supprime toute la ligne
                new_lines = lines[:start_line] + lines[end_line + 1:]
            
            elif c_type == "python_single":
                # Commentaire Python (#)
                hash_index = line_content.find('#')
                if hash_index != -1:
                    # Si le # est au début (ou après des espaces), on vire la ligne
                    if line_content[:hash_index].strip() == "":
                         new_lines = lines[:start_line] + lines[end_line + 1:]
                    else:
                        # Commentaire inline (code = x # comment)
                        new_lines = lines[:start_line] + [line_content[:hash_index].rstrip() + '\n'] + lines[start_line + 1:]
                else:
                    new_lines = lines # Sécurité
            
            else: 
                if line_content.strip().startswith('//') or line_content.strip().startswith('/*'):
                     new_lines = lines[:start_line] + lines[end_line + 1:]
                else:
                    # Inline
                    sl_index = line_content.find('//')
                    if sl_index != -1:
                        new_lines = lines[:start_line] + [line_content[:sl_index].rstrip() + '\n'] + lines[start_line + 1:]
                    else:
                        # Pour simplifier ici, si on détecte pas
                         new_lines = lines[:start_line] + lines[end_line + 1:]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Erreur lors de la modification du fichier {file_path}: {e}")
        return False
# src/logic/comment_processor.py
import os
import hashlib


def find_dart_files(directory):
    """Trouve tous les fichiers .dart dans un répertoire."""
    dart_files = []
    for root_dir, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".dart"):
                dart_files.append(os.path.join(root_dir, file))
    return dart_files


def get_comment_hash(comment_content):
    """Génère un hash SHA256 pour un contenu de commentaire."""
    return hashlib.sha256(comment_content.strip().encode('utf-8')).hexdigest()


def _is_in_string(line, index):
    """Vérifie si un index est à l'intérieur d'une chaîne de caractères."""
    sub_line = line[:index]
    single_quotes = sub_line.count("'")
    double_quotes = sub_line.count('"')
    return single_quotes % 2 != 0 or double_quotes % 2 != 0


def find_comments_in_file(file_path, kept_comments_hashes):
    """
    Générateur qui trouve et yield les commentaires d'un fichier,
    en ignorant ceux dont le hash est déjà sauvegardé.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Erreur de lecture du fichier {file_path}: {e}")
        return

    in_multiline_comment = False
    comment_buffer = []
    comment_start_line = -1

    for i, line in enumerate(lines):
        if in_multiline_comment:
            comment_buffer.append(line)
            end_ml_index = line.find('*/')
            if end_ml_index != -1 and not _is_in_string(line, end_ml_index):
                in_multiline_comment = False
                full_comment = "".join(comment_buffer)
                comment_hash = get_comment_hash(full_comment)
                if comment_hash not in kept_comments_hashes:
                    yield {"file_path": file_path, "start_line": comment_start_line, "end_line": i,
                           "content": full_comment, "hash": comment_hash}
                comment_buffer = []
        else:
            sl_index = line.find('//')
            start_ml_index = line.find('/*')

            if start_ml_index != -1 and (sl_index == -1 or start_ml_index < sl_index):
                if not _is_in_string(line, start_ml_index):
                    in_multiline_comment = True
                    comment_start_line = i
                    comment_buffer.append(line)
                    end_ml_index = line.find('*/', start_ml_index + 2)
                    if end_ml_index != -1 and not _is_in_string(line, end_ml_index):
                        in_multiline_comment = False
                        full_comment = "".join(comment_buffer)
                        comment_hash = get_comment_hash(full_comment)
                        if comment_hash not in kept_comments_hashes:
                            yield {"file_path": file_path, "start_line": i, "end_line": i, "content": full_comment,
                                   "hash": comment_hash}
                        comment_buffer = []

            elif sl_index != -1:
                if not _is_in_string(line, sl_index):
                    comment_hash = get_comment_hash(line[sl_index:])
                    if comment_hash not in kept_comments_hashes:
                        yield {"file_path": file_path, "start_line": i, "end_line": i, "content": line,
                               "hash": comment_hash}


def remove_comment_from_file(comment_info):
    """Supprime un commentaire d'un fichier et réécrit le fichier."""
    file_path = comment_info["file_path"]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_line = comment_info["start_line"]
        end_line = comment_info["end_line"]

        if lines[start_line].strip().startswith('//') or '/*' in lines[start_line]:
            new_lines = lines[:start_line] + lines[end_line + 1:]
        else:
            line_content = lines[start_line]
            sl_index = line_content.find('//')
            new_lines = lines[:start_line] + [line_content[:sl_index].rstrip() + '\n'] + lines[start_line + 1:]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Erreur lors de la modification du fichier {file_path}: {e}")
        return False