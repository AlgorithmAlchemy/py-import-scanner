# main.py

import os
import re
import threading
from threading import Event
from collections import Counter
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, Label, Button, Text, Scrollbar, Frame, Menu
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyperclip  # Для копирования в буфер обмена
from colorama import init
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import ast
from stats_window import open_stats_window, analyze_project_structure, parse_python_files

from utils import read_gitignore, is_ignored, find_projects

init(autoreset=True)
stop_event = Event()

# Очередь для передачи данных между потоками
imports_count = {}
task_queue = queue.Queue()

# Глобальная переменная для хранения данных о проектах
project_data = {}
project_data_ready = False

import os

# Получаем путь к директории исполняемого файла
script_dir = os.path.dirname(os.path.abspath(__file__))
# Определяем путь к проектам относительно директории исполняемого файла
default_project_path = os.path.join(script_dir)

# Выводим путь для проверки
print(f"Путь к папке projects: {default_project_path}")

# Проверка, существует ли эта директория
if not os.path.isdir(default_project_path):
    raise FileNotFoundError(f"Директория 'projects' не найдена по пути: {default_project_path}")


# =========================
# Функции для анализа файлов
# =========================

def get_gitignore_excluded_dirs(gitignore_path='.gitignore'):
    excluded_dirs = []
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            excluded_dirs = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        pass  # Если файл .gitignore не найден, просто не исключаем папки
    return excluded_dirs


def is_excluded_directory(directory, excluded_dirs):
    # Исключаем папки, содержащие в названии venv, env, или из .gitignore
    if any(excluded_dir in directory for excluded_dir in excluded_dirs):
        return True
    return False


def find_imports_in_file(file_path):
    imports = []
    excluded = {
        '__future__', 'warnings', 'io', 'typing', 'collections', 'contextlib', 'types', 'abc', 'forwarding',
        'ssl', 'distutils', 'operator', 'pathlib', 'dataclasses', 'inspect', 'socket', 'shutil', 'attr',
        'tempfile', 'zipfile', 'betterproto', 'the', 'struct', 'base64', 'optparse', 'textwrap', 'setuptools',
        'pkg_resources', 'multidict', 'enum', 'copy', 'importlib', 'traceback', 'six', 'binascii', 'stat',
        'errno', 'grpclib', 'posixpath', 'zlib', 'pytz', 'bisect', 'weakref', 'winreg', 'fnmatch', 'site',
        'email', 'html', 'mimetypes', 'locale', 'calendar', 'shlex', 'unicodedata', 'babel', 'pkgutil', 'ipaddress',
        'arq', 'rsa', 'handlers', 'opentele', 'states'
    }

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    lib = alias.name.split('.')[0]
                    if lib and lib not in excluded and lib.isidentifier():
                        imports.append(lib)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    lib = node.module.split('.')[0]
                    if lib and lib not in excluded and lib.isidentifier():
                        imports.append(lib)

    except Exception:
        pass  # игнорируем битые файлы, ошибки парсинга

    return imports



def scan_directory_for_imports_parallel(directory, progress_label, output_text,task_queue, stop_event):
    global imports_count, total_imports, project_data

    ignored_paths = read_gitignore(directory)
    all_imports = []
    file_paths = []

    for root, dirs, files in os.walk(directory):
        # Исключаем папки venv, .venv, env, .env прямо на месте
        dirs[:] = [d for d in dirs if d not in ('venv', '.venv', 'env', '.env') and not is_ignored(os.path.join(root, d), ignored_paths)]

        for file in files:
            file_path = os.path.join(root, file)

            # Пропускаем файлы в venv-подобных папках ИЛИ те, что в .gitignore
            if ('venv' in file_path or '.venv' in file_path or 'env' in file_path or '.env' in file_path):
                continue
            if file.endswith('.py') and not is_ignored(file_path, ignored_paths):
                file_paths.append(file_path)

    total_files = len(file_paths)
    progress_label.config(text=f"Найдено {total_files} файлов для обработки...")
    progress_label.update()

    imports_list = []

    def process_file(file_path):
        if stop_event.is_set():
            return []
        return find_imports_in_file(file_path)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_file, fp): fp for fp in file_paths}

        processed_files = 0
        for future in as_completed(futures):
            imports = future.result()
            imports_list.extend(imports)

            processed_files += 1
            if processed_files % 50 == 0 or processed_files == total_files:
                task_queue.put(f"Обработано {processed_files}/{total_files} файлов.")

    imports_count = dict(Counter(imports_list))
    total_imports = sum(imports_count.values())

    task_queue.put(('stats', imports_count, total_imports))

    progress_label.config(text="Анализ структуры проекта...")
    progress_label.update()
    # После анализа импортов

    analyze_project_structure(directory, task_queue)



    # Вставляем данные в вывод, если необходимо
    output_text.insert("end", f"Проектные данные: {project_data}")
    output_text.update()

    try:
        # Сканируем директории и отбираем папки для анализа
        projects = find_projects(directory)

        # Проводим анализ каждого проекта
        project_data = parse_python_files(directory)

        # Переименование поля
        for item in project_data:
            item['date'] = item.pop('created')

        project_data_ready = True

        formatted_data = "\n".join(
            [f"Проект: {project}\n"
             f"  Кол-во .py: {data['py_count']}\n"
             f"  Библиотеки: {', '.join(data['libs'])}\n"
             f"  Создан: {data['date']}\n"
             f"  Директории: {', '.join(data['dirs'])}\n"
             for project, data in project_info.items()]
        )

        output_text.insert("end", f"\nПроектные данные:\n{formatted_data}")
        output_text.update()

    except Exception as e:
        task_queue.put(f"Ошибка при анализе структуры проектов: {e}")

# =========================
# Работа с интерфейсом
# =========================

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        excluded_dirs = get_gitignore_excluded_dirs()  # Получаем исключенные директории из .gitignore
        threading.Thread(target=scan_directory_for_imports_parallel,
                         args=(directory, progress_label, output_text, task_queue, stop_event),  # Передаем только 3 аргумента
                         daemon=True).start()


# =========================
# Функция для вывода прочих библиотек
# =========================

def show_others(imports_count, total_imports, output_text):
    # Сортируем библиотеки по количеству
    sorted_imports = sorted(imports_count.items(), key=lambda x: x[1], reverse=True)

    # Ограничиваем вывод до 200 библиотек
    top_imports = sorted_imports[:200]
    others_count = sum(count for lib, count in sorted_imports[200:])

    # Очищаем вывод
    output_text.delete(1.0, "end")

    # Выводим "Прочее" для остальных
    if others_count > 0:
        output_text.insert("insert", f"Прочее:\n")
        for lib, count in sorted_imports[200:]:
            percentage = (count / total_imports) * 100
            output_text.insert("insert", f"{lib}: {count} ({percentage:.2f}%)\n")
    else:
        output_text.insert("insert", "Прочее: Нет дополнительных библиотек.\n")


# =========================
# Функции для вывода
# =========================

def show_main_libs(imports_count, total_imports, output_text):
    output_text.delete(1.0, "end")
    output_text.insert("insert", "Топ 100 популярных библиотек:\n")

    sorted_imports = sorted(imports_count.items(), key=lambda x: x[1], reverse=True)
    top_imports = sorted_imports[:100]

    for lib, count in top_imports:
        percentage = (count / total_imports) * 100
        output_text.insert("insert", f"{lib}: {count} ({percentage:.2f}%)\n")


def print_import_statistics(imports_count, total_imports, output_text):
    output_text.delete(1.0, "end")
    output_text.insert("insert", f"Общее количество импортов: {total_imports}\n")

    # Сортируем библиотеки по количеству
    sorted_imports = sorted(imports_count.items(), key=lambda x: x[1], reverse=True)

    # Ограничиваем вывод до 100 библиотек
    top_imports = sorted_imports[:100]
    others_count = sum(count for lib, count in sorted_imports[100:])

    # Выводим топ 100 библиотек
    for lib, count in top_imports:
        percentage = (count / total_imports) * 100
        output_text.insert("insert", f"{lib}: {count} ({percentage:.2f}%)\n")

    # Выводим "Прочее" для остальных
    if others_count > 0:
        output_text.insert("insert", f"Прочее: {others_count} ({(others_count / total_imports) * 100:.2f}%)\n")


def plot_import_statistics(imports_count, total_imports, plot_type="both"):
    # Сортируем библиотеки по убыванию использования
    sorted_imports = sorted(imports_count.items(), key=lambda x: x[1], reverse=True)

    # Ограничиваем вывод до 30 библиотек
    top_imports = sorted_imports[:30]
    others_count = sum(count for lib, count in sorted_imports[30:])

    libraries_sorted = [lib for lib, _ in top_imports]
    counts_sorted = [count for _, count in top_imports]
    percentages_sorted = [(count / total_imports) * 100 for count in counts_sorted]

    # Добавляем "Прочее"
    if others_count > 0:
        libraries_sorted.append('Прочее')
        counts_sorted.append(others_count)
        percentages_sorted.append((others_count / total_imports) * 100)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

    if plot_type == "both" or plot_type == "bar":
        # Гистограмма
        ax1.barh(libraries_sorted, counts_sorted, color='skyblue')
        ax1.set_xlabel('Количество использований')
        ax1.set_ylabel('Библиотеки')
        ax1.set_title('Частота использования библиотек')

        # Логарифмическая шкала для графика
        ax1.set_xscale('log')

    if plot_type == "both" or plot_type == "pie":
        # Круговая диаграмма
        ax2.pie(counts_sorted, labels=libraries_sorted, autopct='%1.1f%%', startangle=90)
        ax2.axis('equal')
        ax2.set_title('Распределение по библиотекам')

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)






# =========================
# Копирование в буфер обмена
# =========================

def on_copy(event=None):
    selected_text = output_text.get("sel.first", "sel.last")
    pyperclip.copy(selected_text)  # Копируем выделенный текст в буфер обмена


def update_gui():
    try:
        message = task_queue.get_nowait()

        if isinstance(message, str):
            progress_label.config(text=message)

        elif isinstance(message, tuple) and message[0] == 'stats':
            imports_count, total_imports = message[1], message[2]
            print_import_statistics(imports_count, total_imports, output_text)
            plot_import_statistics(imports_count, total_imports)

        elif isinstance(message, tuple) and message[0] == 'project_stats':
            structure = message[1]
            output_text.insert("insert", "\n--- Статистика проекта ---\n")
            output_text.insert("insert", f"Всего файлов: {structure['total_files']}\n")
            output_text.insert("insert", f"Всего директорий: {structure['total_dirs']}\n")
            output_text.insert("insert", f"Python файлов: {structure['py_files']} (моего кода)\n")
            output_text.insert("insert", f"Python файлов в виртуальных/служебных папках: {structure['py_files_venv']}\n")
            output_text.insert("insert", f"Прочих файлов: {structure['other_files']}\n")
            output_text.insert("insert", f"\nСписок директорий:\n")
            for folder in structure['folders']:
                output_text.insert("insert", f" - {folder}\n")

    except queue.Empty:
        pass

    window.after(100, update_gui)

# =========================
# GUI
# =========================

def on_closing():
    stop_event.set()  # Сигнал остановки для потоков
    window.destroy()  # Закрытие окна


window = Tk()
window.title("Статистика импортов в проектах")
window.geometry("1200x800")
window.protocol("WM_DELETE_WINDOW", on_closing)

frame = Frame(window)
frame.pack(pady=20)

btn_browse = Button(frame, text="Выбрать директорию", command=browse_directory)
btn_browse.pack()

output_text = Text(window, wrap="word", width=80, height=15)
output_text.pack(padx=20, pady=20)

scrollbar = Scrollbar(window, command=output_text.yview)
scrollbar.pack(side="right", fill="y")
output_text.config(yscrollcommand=scrollbar.set)

output_text.tag_configure("green", foreground="green")
output_text.tag_configure("cyan", foreground="cyan")
output_text.tag_configure("red", foreground="red")

# Первый ряд: графики
chart_frame = Frame(window)
chart_frame.pack(pady=5)

btn_bar_chart = Button(chart_frame, text="Гистограмма", command=lambda: plot_import_statistics(imports_count, total_imports, "bar"))
btn_bar_chart.pack(side="left", padx=10)

btn_pie_chart = Button(chart_frame, text="Круговая диаграмма", command=lambda: plot_import_statistics(imports_count, total_imports, "pie"))
btn_pie_chart.pack(side="left", padx=10)

# Второй ряд: основные и прочие библиотеки
lib_frame = Frame(window)
lib_frame.pack(pady=5)

btn_main_libs = Button(lib_frame, text="Показать основные библиотеки", command=lambda: show_main_libs(imports_count, total_imports, output_text))
btn_main_libs.pack(side="left", padx=10)

btn_others = Button(lib_frame, text="Показать прочие библиотеки", command=lambda: show_others(imports_count, total_imports, output_text))
btn_others.pack(side="left", padx=10)


# Новая кнопка: временной анализ проектов
# btn_stats_by_date = Button(lib_frame, text="Анализ проектов по дате", command=lambda: open_stats_window(window, project_data) )
btn_stats_by_date = Button(lib_frame, text="Анализ проектов по дате", command=lambda: open_stats_window(window, project_data) )

btn_stats_by_date.pack(side="left", padx=10)


# Добавляем контекстное меню для копирования
context_menu = Menu(window, tearoff=0)
context_menu.add_command(label="Копировать", command=on_copy)


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


output_text.bind("<Button-3>", show_context_menu)  # Правый клик мыши
output_text.bind("<Control-c>", on_copy)  # Ctrl+C для копирования

progress_label = Label(window, text="Готов к работе.", font=("Arial", 12))
progress_label.pack(pady=10)

# Запуск функции обновления GUI
def periodic_check():
    update_gui()
    window.after(100, periodic_check)  # каждые 100 мс проверяем очередь

# Запуск Tkinter
periodic_check()
window.mainloop()

