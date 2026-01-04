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
    # Simplification : on compte les guillemets. Ignore les guillemets échappés.
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

        # Cas simple d'un commentaire qui prend toute la ligne ou plusieurs lignes
        if lines[start_line].strip().startswith('//') or '/*' in lines[start_line]:
            new_lines = lines[:start_line] + lines[end_line + 1:]
        # Cas d'un commentaire en fin de ligne (//)
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