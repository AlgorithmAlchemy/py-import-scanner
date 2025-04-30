import os


def read_gitignore(directory):
    gitignore_path = os.path.join(directory, '.gitignore')
    ignored_paths = set()

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignored_paths.add(line)
    return ignored_paths


def is_ignored(file_path, ignored_paths):
    relative_path = os.path.relpath(file_path)
    for ignored_path in ignored_paths:
        if relative_path.startswith(ignored_path):
            return True
    return False