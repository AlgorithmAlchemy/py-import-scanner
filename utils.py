import os

# =========================
# Функции для анализа файлов
# =========================

def find_projects(root_dir):
    projects = []
    visited = set()

    for root, dirs, files in os.walk(root_dir):
        # Пропустить уже отмеченные как проекты папки
        if any(root.startswith(p) for p in visited):
            continue

        # Если есть хотя бы один .py файл — это проект
        if any(f.endswith('.py') for f in files):
            projects.append(root)
            visited.add(root)

    return projects


def read_gitignore(directory):
    gitignore_path = os.path.join(directory, '.gitignore')
    ignored_paths = set()

    if os.path.exists(gitignore_path):
        try:
            # Пробуем UTF-8
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignored_paths.add(line)
        except UnicodeDecodeError:
            try:
                # Пробуем cp1251 (Windows-1251)
                with open(gitignore_path, 'r', encoding='cp1251') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            ignored_paths.add(line)
            except UnicodeDecodeError:
                # Если не получается, игнорируем файл
                print(f"Предупреждение: не удалось прочитать .gitignore в {directory}")
                return ignored_paths
    return ignored_paths


def is_ignored(file_path, ignored_paths):
    relative_path = os.path.relpath(file_path)
    for ignored_path in ignored_paths:
        if relative_path.startswith(ignored_path):
            return True
    return False