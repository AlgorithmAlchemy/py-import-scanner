# stats_window.py

import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import ast
import datetime

from utils import read_gitignore, is_ignored, find_projects

IGNORED_DIRS = {'.git', '__pycache__', '.idea', '.vscode', '.venv', '.eggs'}


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




def parse_python_files(projects_dir, export=True, max_files=5000, max_depth=6):
    import os, ast, datetime
    import pandas as pd

    IGNORED_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'venv', '.venv', 'env', '.env', '.mypy_cache'}

    project_stats = {}
    scanned_files = 0

    for root, dirs, files in os.walk(projects_dir):
        # Удаление игнорируемых директорий
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        # Ограничение глубины
        rel_root = os.path.relpath(root, projects_dir)
        depth = rel_root.count(os.sep)
        if depth > max_depth:
            continue

        py_files = [f for f in files if f.endswith(".py")]
        if not py_files:
            continue

        project_name = rel_root.replace(os.sep, " / ") if rel_root != "." else "ROOT"

        if project_name not in project_stats:
            project_stats[project_name] = {
                "py_count": 0,
                "libs": set(),
                "created": None,
                "dirs": set()
            }

        for file in py_files:
            """if scanned_files >= max_files:
                print(f"⚠ Превышен лимит {max_files} файлов. Анализ остановлен.")
                break"""

            file_path = os.path.join(root, file)
            scanned_files += 1
            project_stats[project_name]["py_count"] += 1

            # Обработка даты
            try:
                creation_time = os.path.getctime(file_path)
                creation_date = datetime.datetime.fromtimestamp(creation_time)
                current_created = project_stats[project_name]["created"]
                if current_created is None or creation_date < current_created:
                    project_stats[project_name]["created"] = creation_date
            except Exception:
                pass

            # Добавление относительной директории
            rel_dir = os.path.relpath(root, projects_dir)
            if rel_dir != ".":
                project_stats[project_name]["dirs"].add(rel_dir)

            # Парсинг импортов
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                node = ast.parse(content, filename=file_path)
                for sub_node in ast.walk(node):
                    if isinstance(sub_node, ast.Import):
                        for alias in sub_node.names:
                            project_stats[project_name]["libs"].add(alias.name.split('.')[0])
                    elif isinstance(sub_node, ast.ImportFrom) and sub_node.module:
                        project_stats[project_name]["libs"].add(sub_node.module.split('.')[0])
            except Exception:
                continue

        print(f"[✓] {project_name} — {len(py_files)} файлов")

    # Финальная сборка
    result = []
    for proj, data in project_stats.items():
        date_str = data["created"].strftime("%Y-%m-%d %H:%M:%S") if data["created"] else None
        result.append({
            "name": proj,
            "stack": sorted(data["libs"]),
            "dirs": sorted(data["dirs"]),
            "date": date_str,
            "py_count": data["py_count"]
        })

    if not result:
        print("⚠ Не найдено проектов с .py файлами.")
        return []

    df = pd.DataFrame(result)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if export:
        df.to_csv("project_stats.csv", index=False, encoding="utf-8-sig")
        df.to_html("project_stats.html", index=False)

    print("==== Итог ====")
    print(df[["name", "date"]])
    return df.to_dict("records")





def open_stats_window(root, project_data: list[dict]):
    stats_win = tk.Toplevel(root)
    stats_win.title("📊 Статистика по проектам")
    stats_win.geometry("1000x700")

    if not project_data:
        tk.Label(stats_win, text="❌ Нет данных для отображения.", font=("Arial", 12)).pack(pady=20)
        return

    df = pd.DataFrame(project_data)

    if df.empty or 'date' not in df.columns:
        tk.Label(stats_win, text="❌ Недостаточно данных для статистики.", font=("Arial", 12)).pack(pady=20)
        return

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    if df.empty:
        tk.Label(stats_win, text="❌ Все даты повреждены или отсутствуют.", font=("Arial", 12)).pack(pady=20)
        return

    df['month'] = df['date'].dt.to_period('M')

    # === Верхняя сводка ===
    summary_frame = tk.Frame(stats_win)
    summary_frame.pack(pady=10)

    total_projects = len(df)
    total_files = df['py_count'].sum()
    earliest = df['date'].min().strftime("%Y-%m-%d")
    latest = df['date'].max().strftime("%Y-%m-%d")
    unique_months = df['month'].nunique()

    summary_text = (
        f"📦 Всего проектов: {total_projects}     🧠 Всего .py файлов: {total_files}\n"
        f"📆 Период: {earliest} → {latest}     📊 Уникальных месяцев: {unique_months}"
    )
    tk.Label(summary_frame, text=summary_text, font=("Arial", 11), justify="left").pack()

    # === График по месяцам ===
    chart_frame = tk.Frame(stats_win)
    chart_frame.pack(fill="both", expand=False, pady=5)

    fig, ax = plt.subplots(figsize=(8, 4))
    df_by_month = df.groupby('month').size().sort_index()
    df_by_month.plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')

    ax.set_title('📅 Количество проектов по месяцам', fontsize=14)
    ax.set_ylabel('Проекты', fontsize=12)
    ax.set_xlabel('Месяц', fontsize=12)
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # === Анализ технологий ===
    tech_frame = tk.LabelFrame(stats_win, text="📚 Используемые библиотеки", font=("Arial", 12))
    tech_frame.pack(fill="both", expand=True, padx=10, pady=10)

    if 'stack' in df.columns:
        all_stacks = sum(df['stack'].tolist(), [])
        stack_series = pd.Series(all_stacks).value_counts()
        if not stack_series.empty:
            stack_text = "\n".join(f"• {lib:<20} — {count}" for lib, count in stack_series.items())
        else:
            stack_text = "Нет данных о библиотеках."
    else:
        stack_text = "Нет данных по стеку технологий."

    tk.Message(tech_frame, text=stack_text, font=("Courier New", 10), width=900, anchor="w", justify="left").pack()

    # === Кнопка закрытия ===
    tk.Button(stats_win, text="Закрыть", command=stats_win.destroy).pack(pady=10)

