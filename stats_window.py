# stats_window.py

import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import ast
import datetime

from utils import read_gitignore, is_ignored

def analyze_project_structure(directory, task_queue):
    ignored_paths = read_gitignore(directory)

    structure = {
        'total_files': 0,
        'total_dirs': 0,
        'py_files': 0,
        'py_files_venv': 0,
        'other_files': 0,
        'folders': []
    }

    venv_like = ('venv', '.venv', 'env', '.env', '__pycache__', '.git', '.idea', '.vscode', '.mypy_cache')

    for root, dirs, files in os.walk(directory):
        # исключаем сразу ненужные папки
        dirs[:] = [d for d in dirs if d not in venv_like and not is_ignored(os.path.join(root, d), ignored_paths)]

        structure['total_dirs'] += len(dirs)
        structure['total_files'] += len(files)

        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.py'):
                if any(p in file_path for p in venv_like) or is_ignored(file_path, ignored_paths):
                    structure['py_files_venv'] += 1
                else:
                    structure['py_files'] += 1
            else:
                structure['other_files'] += 1

        relative_root = os.path.relpath(root, directory)
        structure['folders'].append(relative_root)

    task_queue.put(('project_stats', structure))



"""
def parse_python_files(projects_dir):
    project_stats = {}

    for root, dirs, files in os.walk(projects_dir):
        project_name = os.path.relpath(root, projects_dir).split(os.sep)[0]

        if project_name not in project_stats:
            project_stats[project_name] = {
                "py_count": 0,
                "libs": set(),
                "created": None,
                "dirs": set()
            }

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                # Обновляем счётчик Python файлов
                project_stats[project_name]["py_count"] += 1

                # Обновляем дату создания проекта
                creation_time = os.path.getctime(file_path)
                creation_date = datetime.datetime.fromtimestamp(creation_time)

                current_created = project_stats[project_name]["created"]
                if current_created is None or creation_date < current_created:
                    project_stats[project_name]["created"] = creation_date

                # Сбор директорий
                rel_dir = os.path.relpath(root, os.path.join(projects_dir, project_name))
                if rel_dir != ".":
                    project_stats[project_name]["dirs"].add(rel_dir)

                # Парсим файл для библиотек
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        node = ast.parse(f.read(), filename=file_path)

                    for sub_node in ast.walk(node):
                        if isinstance(sub_node, ast.Import):
                            for alias in sub_node.names:
                                project_stats[project_name]["libs"].add(alias.name.split('.')[0])
                        elif isinstance(sub_node, ast.ImportFrom):
                            if sub_node.module:
                                project_stats[project_name]["libs"].add(sub_node.module.split('.')[0])
                except Exception:
                    continue

    # Приведение к нужному формату
    for proj in project_stats:
        project_stats[proj]["libs"] = sorted(project_stats[proj]["libs"])
        project_stats[proj]["dirs"] = sorted(project_stats[proj]["dirs"])
        if project_stats[proj]["created"]:
            project_stats[proj]["created"] = project_stats[proj]["created"].strftime("%Y-%m-%d %H:%M:%S")

    return project_stats
"""


def open_stats_window(root, project_data: list[dict]):
    stats_win = tk.Toplevel(root)
    stats_win.title("Статистика проектов")
    stats_win.geometry("800x600")

    df = pd.DataFrame(project_data)
    if df.empty or 'date' not in df.columns:
        tk.Label(stats_win, text="Недостаточно данных для отображения статистики.").pack(pady=20)
        return

    df['date'] = pd.to_datetime(df['date'])

    stats_canvas = tk.Frame(stats_win)
    stats_canvas.pack(fill="both", expand=True)

    # === График по дате создания ===
    fig, ax = plt.subplots(figsize=(6, 4))
    df_by_month = df.groupby(df['date'].dt.to_period('M')).size().sort_index()
    df_by_month.plot(kind='bar', ax=ax, title='Проекты по месяцам', rot=45)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=stats_canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10)

    # === Анализ технологий ===
    if 'stack' in df.columns:
        all_stacks = sum(df['stack'].tolist(), [])
        stack_series = pd.Series(all_stacks).value_counts()
        stack_text = "\n".join(f"{lang}: {count}" for lang, count in stack_series.items())
    else:
        stack_text = "Нет данных по стеку технологий."

    tk.Label(stats_canvas, text="Анализ технологий:\n" + stack_text, justify="left", font=("Arial", 12)).pack(pady=5)

    # === Кнопка закрытия ===
    tk.Button(stats_canvas, text="Закрыть", command=stats_win.destroy).pack(pady=10)
