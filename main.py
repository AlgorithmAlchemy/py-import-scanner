# main.py

import os
import datetime
import time
from threading import Event
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Используем Agg backend для совместимости
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                               QFileDialog, QMenu, QMessageBox, QProgressBar, QComboBox)
from PySide6.QtCore import Qt, QThread, Signal, QTranslator, QLocale
from PySide6.QtGui import QFont, QAction
import pyperclip  # Для копирования в буфер обмена
from colorama import init
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import ast
from gui.stats_window import StatsWindow
from gui.chart_windows import BarChartWindow, PieChartWindow
from utils import read_gitignore, is_ignored, find_projects

init(autoreset=True)
stop_event = Event()

# Очередь для передачи данных между потоками
imports_count = {}
task_queue = queue.Queue()

# Глобальная переменная для хранения данных о проектах
project_data = {}
project_data_ready = False

# Кэш для исключенных библиотек (оптимизация)
EXCLUDED_LIBS = frozenset({
    '__future__', 'warnings', 'io', 'typing', 'collections', 'contextlib', 'types', 'abc', 'forwarding',
    'ssl', 'distutils', 'operator', 'pathlib', 'dataclasses', 'inspect', 'socket', 'shutil', 'attr',
    'tempfile', 'zipfile', 'betterproto', 'the', 'struct', 'base64', 'optparse', 'textwrap', 'setuptools',
    'pkg_resources', 'multidict', 'enum', 'copy', 'importlib', 'traceback', 'six', 'binascii', 'stat',
    'errno', 'grpclib', 'posixpath', 'zlib', 'pytz', 'bisect', 'weakref', 'winreg', 'fnmatch', 'site',
    'email', 'html', 'mimetypes', 'locale', 'calendar', 'shlex', 'unicodedata', 'babel', 'pkgutil', 'ipaddress',
    'arq', 'rsa', 'handlers', 'opentele', 'states', 'os', 'sys', 're', 'json', 'datetime', 'time',
    'math', 'random', 'itertools', 'functools', 'logging', 'subprocess', 'threading', 'multiprocessing'
})

# Кэш для исключенных директорий
EXCLUDED_DIRS = frozenset({'venv', '.venv', 'env', '.env', '__pycache__', '.git', 'node_modules', 
                           'build', 'dist', '.pytest_cache', '.coverage', '.tox', '.mypy_cache'})

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


def find_imports_in_file_optimized(file_path):
    """Оптимизированная версия поиска импортов с ранним выходом"""
    imports = []
    
    try:
        # Быстрое чтение файла с автоматическим определением кодировки
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    content = f.read()
            except UnicodeDecodeError:
                return imports
        
        # Быстрая проверка на наличие импортов (оптимизация)
        if 'import ' not in content and 'from ' not in content:
            return imports
            
        # Парсинг AST с оптимизацией
        try:
            tree = ast.parse(content, filename=file_path)
        except (SyntaxError, ValueError):
            return imports

        # Быстрый обход AST с ранним выходом
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    lib = alias.name.split('.')[0]
                    if lib and lib not in EXCLUDED_LIBS and lib.isidentifier():
                        imports.append(lib)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    lib = node.module.split('.')[0]
                    if lib and lib not in EXCLUDED_LIBS and lib.isidentifier():
                        imports.append(lib)
                        
            # Ранний выход если нашли достаточно импортов
            if len(imports) > 50:  # Большинство файлов не имеют больше 50 импортов
                break

    except Exception:
        pass  # игнорируем битые файлы, ошибки парсинга

    return imports


def scan_directory_for_imports_parallel(directory, progress_callback, task_queue, stop_event):
    """Максимально оптимизированная версия сканирования"""
    global imports_count, total_imports, project_data
    
    start_time = time.time()
    progress_callback("Поиск Python файлов...")
    
    ignored_paths = read_gitignore(directory)
    file_paths = []

    # Сверхбыстрый поиск файлов с предварительной фильтрацией
    for root, dirs, files in os.walk(directory):
        if stop_event.is_set():
            return {}, 0, []
            
        # Мгновенная фильтрация директорий
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS 
                   and not is_ignored(os.path.join(root, d), ignored_paths)]

        # Быстрая фильтрация Python файлов
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not is_ignored(file_path, ignored_paths):
                    file_paths.append(file_path)

    total_files = len(file_paths)
    progress_callback(f"Найдено {total_files} файлов для обработки...")

    if total_files == 0:
        return {}, 0, []

    # Оптимизация: группируем файлы в батчи для лучшей производительности
    batch_size = 100
    imports_list = []
    
    def process_batch(file_batch):
        """Обработка батча файлов"""
        batch_imports = []
        for file_path in file_batch:
            if stop_event.is_set():
                break
            batch_imports.extend(find_imports_in_file_optimized(file_path))
        return batch_imports

    # Создаем батчи файлов
    file_batches = [file_paths[i:i + batch_size] for i in range(0, len(file_paths), batch_size)]
    
    # Максимальное количество потоков для ускорения
    max_workers = min(100, len(file_batches), os.cpu_count() * 4)
    
    progress_callback(f"Запуск {max_workers} потоков для обработки...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_batch, batch): i for i, batch in enumerate(file_batches)}

        processed_batches = 0
        for future in as_completed(futures):
            if stop_event.is_set():
                break
                
            batch_imports = future.result()
            imports_list.extend(batch_imports)

            processed_batches += 1
            processed_files = processed_batches * batch_size
            if processed_files % 500 == 0 or processed_batches == len(file_batches):
                elapsed = time.time() - start_time
                rate = processed_files / elapsed if elapsed > 0 else 0
                progress_callback(f"Обработано {min(processed_files, total_files)}/{total_files} файлов "
                               f"({rate:.1f} файл/сек)...")

    # Подсчет результатов
    imports_count = dict(Counter(imports_list))
    total_imports = sum(imports_count.values())

    total_time = time.time() - start_time
    progress_callback(f"Сканирование завершено за {total_time:.2f} сек ({total_files/total_time:.1f} файл/сек)")

    # Быстрый анализ структуры проекта
    progress_callback("Анализ структуры проекта...")
    try:
        from gui.stats_window import analyze_project_structure, parse_python_files
        analyze_project_structure(directory, task_queue)

        # Сканируем директории и отбираем папки для анализа
        projects = find_projects(directory)

        # Проводим анализ каждого проекта
        project_data = parse_python_files(directory)

        # Переименование поля (если оно существует)
        for item in project_data:
            if 'created' in item:
                item['date'] = item.pop('created')

        project_data_ready = True

    except Exception as e:
        print(f"Ошибка при анализе структуры проектов: {e}")
        project_data = []
    
    return imports_count, total_imports, project_data


# Обратная совместимость
def find_imports_in_file(file_path):
    return find_imports_in_file_optimized(file_path)


# =========================
# Класс для работы с интерфейсом
# =========================

class ScanWorker(QThread):
    """Поток для сканирования файлов"""
    progress_updated = Signal(str)
    scan_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, directory, stop_event):
        super().__init__()
        self.directory = directory
        self.stop_event = stop_event
        
    def run(self):
        try:
            # Создаем локальную очередь для потокобезопасности
            local_task_queue = queue.Queue()
            
            # Запускаем сканирование с оптимизированной функцией
            imports_count, total_imports, project_data = scan_directory_for_imports_parallel(
                self.directory, 
                self.progress_updated.emit, 
                local_task_queue, 
                self.stop_event
            )
            
            if not self.stop_event.is_set():
                result = {
                    'imports_count': imports_count,
                    'total_imports': total_imports,
                    'project_data': project_data
                }
                self.scan_completed.emit(result)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scan_worker = None
        self.stop_event = Event()
        self.current_language = "ru"  # Язык по умолчанию
        
        # Инициализация переводчика
        self.translator = QTranslator()
        self.current_language = "ru"
        
        self.init_ui()
        self.setup_styles()
        self.setup_context_menu()
        
    def change_language(self, index):
        """Изменение языка интерфейса"""
        print(f"\n\n*** СМЕНА ЯЗЫКА: индекс={index} ***\n\n")
        lang_code = self.lang_combo.itemData(index)
        print(f"Выбранный код языка: {lang_code}")
        print(f"Текущий язык: {self.current_language}")
        
        if lang_code == self.current_language:
            print("Язык не изменился, выход из метода")
            return
            
        self.current_language = lang_code
        print(f"Установлен новый язык: {self.current_language}")
        self.retranslateUi()
        print(f"Обновление текстов UI выполнено")
        
    def retranslateUi(self):
        """Обновление текстов интерфейса в соответствии с выбранным языком"""
        texts = self.get_ui_texts()
        
        # Обновление заголовка окна
        self.setWindowTitle(texts["window_title"])
        
        # Обновление кнопок
        self.browse_button.setText(texts["browse_btn"])
        self.scan_button.setText(texts["scan_btn"])
        self.stop_button.setText(texts["stop_btn"])
        self.stats_button.setText(texts["stats_btn"])
        
        # Обновление статусной строки
        if self.status_label.text() == "Готов к работе" or self.status_label.text() == "Ready to work":
            self.status_label.setText(texts["ready_status"])
            
    def get_ui_texts(self):
        """Получение текстов интерфейса в соответствии с выбранным языком"""
        texts = {
            "ru": {
                "window_title": "Python Import Parser - Анализ импортов",
                "browse_btn": "📁 Выбрать папку",
                "scan_btn": "🔍 Сканировать",
                "stop_btn": "⏹ Остановить",
                "stats_btn": "📊 Статистика",
                "ready_status": "Готов к работе",
                "folder_selected": "Выбрана папка: {}",
                "warning_title": "Предупреждение",
                "warning_select_folder": "Сначала выберите папку для сканирования!",
                "scan_started": "🔍 Начинаю сканирование...",
                "scan_stopped": "Сканирование остановлено",
                "scan_completed": "Сканирование завершено",
                "error_title": "Ошибка",
                "error_message": "Произошла ошибка при сканировании:\n{}",
                "no_imports": "❌ Импорты не найдены",
                "found_libraries": "✅ Найдено {} уникальных библиотек",
                "total_imports": "📊 Общее количество импортов: {}",
                "top_libraries": "🏆 Топ-10 самых популярных библиотек:",
                "more_libraries": "... и еще {} библиотек",
                "info_title": "Информация",
                "scan_first": "Сначала выполните сканирование!",
                "stats_next_update": "Окно статистики будет реализовано в следующем обновлении!",
                "copy_action": "📋 Копировать",
                "clear_action": "🗑 Очистить",
                "copied_to_clipboard": "Текст скопирован в буфер обмена",
                "bar_chart": "📊 Гистограмма",
                "pie_chart": "🥧 Круговая диаграмма",
                "results_placeholder": "Результаты сканирования появятся здесь...",
                "title": "🚀 Анализатор импортов Python",
                "subtitle": "Ультра-быстрое сканирование проектов"
            },
            "en": {
                "window_title": "Python Import Parser - Import Analysis",
                "browse_btn": "📁 Select Folder",
                "scan_btn": "🔍 Scan",
                "stop_btn": "⏹ Stop",
                "stats_btn": "📊 Statistics",
                "ready_status": "Ready to work",
                "folder_selected": "Selected folder: {}",
                "warning_title": "Warning",
                "warning_select_folder": "Please select a folder to scan first!",
                "scan_started": "🔍 Starting scan...",
                "scan_stopped": "Scan stopped",
                "scan_completed": "Scan completed",
                "error_title": "Error",
                "error_message": "An error occurred during scanning:\n{}",
                "no_imports": "❌ No imports found",
                "found_libraries": "✅ Found {} unique libraries",
                "total_imports": "📊 Total number of imports: {}",
                "top_libraries": "🏆 Top-10 most popular libraries:",
                "more_libraries": "... and {} more libraries",
                "info_title": "Information",
                "scan_first": "Please run a scan first!",
                "stats_next_update": "Statistics window will be implemented in the next update!",
                "copy_action": "📋 Copy",
                "clear_action": "🗑 Clear",
                "copied_to_clipboard": "Text copied to clipboard",
                "bar_chart": "📊 Histogram",
                "pie_chart": "🥧 Pie Chart",
                "results_placeholder": "Scan results will appear here...",
                "title": "🚀 Python Import Analyzer",
                "subtitle": "Ultra-fast project scanning"
            }
        }
        
        return texts.get(self.current_language, texts["ru"])

    def init_ui(self):
        self.setWindowTitle("Анализатор импортов Python - Ультра-быстрая версия")
        self.setGeometry(100, 100, 800, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title_label = QLabel("🚀 Анализатор импортов Python")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        main_layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Ультра-быстрое сканирование проектов")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # Кнопка выбора директории
        self.browse_button = QPushButton("📁 Выбрать директорию")
        self.browse_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.browse_button.clicked.connect(self.browse_directory)
        button_layout.addWidget(self.browse_button)

        # Кнопка сканирования
        self.scan_button = QPushButton("🔍 Сканировать")
        self.scan_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.scan_button.clicked.connect(lambda: self.start_scan(default_project_path))
        button_layout.addWidget(self.scan_button)

        # Кнопка остановки
        self.stop_button = QPushButton("⏹ Остановить")
        self.stop_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Выпадающий список для выбора языка
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setCurrentIndex(0)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        button_layout.addWidget(self.lang_combo)

        main_layout.addLayout(button_layout)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFont(QFont("Arial", 10))
        main_layout.addWidget(self.progress_bar)

        # Область результатов
        self.results_text = QTextEdit()
        self.results_text.setFont(QFont("Consolas", 10))
        self.results_text.setPlaceholderText("Результаты сканирования появятся здесь...")
        main_layout.addWidget(self.results_text)

        # Кнопки для графиков
        chart_layout = QHBoxLayout()
        chart_layout.setSpacing(10)

        self.bar_chart_button = QPushButton("📊 Гистограмма")
        self.bar_chart_button.setFont(QFont("Arial", 11))
        self.bar_chart_button.clicked.connect(lambda: self.plot_import_statistics("bar"))
        chart_layout.addWidget(self.bar_chart_button)

        self.pie_chart_button = QPushButton("🥧 Круговая диаграмма")
        self.pie_chart_button.setFont(QFont("Arial", 11))
        self.pie_chart_button.clicked.connect(lambda: self.plot_import_statistics("pie"))
        chart_layout.addWidget(self.pie_chart_button)

        self.stats_button = QPushButton("📈 Статистика проектов")
        self.stats_button.setFont(QFont("Arial", 11))
        self.stats_button.clicked.connect(self.show_stats)
        chart_layout.addWidget(self.stats_button)

        main_layout.addLayout(chart_layout)

        # Статус
        self.status_label = QLabel("Готов к сканированию")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        main_layout.addWidget(self.status_label)

    def change_language(self, index):
        lang_code = self.lang_combo.itemData(index)
        print(f"Изменение языка на: {lang_code}, индекс: {index}")
        
        # Загружаем переводчик для выбранного языка
        if lang_code == "en":
            # Для английского языка загружаем переводчик
            print("Загрузка английского языка")
            self.current_language = "en"
        else:
            # Для русского языка используем исходные строки
            print("Загрузка русского языка")
            self.current_language = "ru"
        
        # Обновляем тексты интерфейса
        self.retranslateUi()
        print("Тексты интерфейса обновлены")
    
    def retranslateUi(self):
        texts = self.get_ui_texts()
        
        # Обновляем тексты в интерфейсе
        self.setWindowTitle(texts["window_title"])
        self.browse_button.setText(texts["browse_btn"])
        self.scan_button.setText(texts["scan_btn"])
        self.stop_button.setText(texts["stop_btn"])
        self.stats_button.setText(texts["stats_btn"])
        self.status_label.setText(texts["ready_status"])
        
        # Обновляем заголовки
        for widget in self.centralWidget().findChildren(QLabel):
            if widget.font().pointSize() == 24:  # Заголовок
                widget.setText(texts["title"])
            elif widget.font().pointSize() == 12 and widget != self.status_label:  # Подзаголовок
                widget.setText(texts["subtitle"])
        
        # Обновляем тексты для кнопок графиков
        self.bar_chart_button.setText(texts["bar_chart"])
        self.pie_chart_button.setText(texts["pie_chart"])
        
        # Обновляем плейсхолдер для текстового поля
        self.results_text.setPlaceholderText(texts["results_placeholder"])
        
    def setup_styles(self):
        # Современный стиль для всего приложения
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
                transform: translateY(-2px);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #004085, stop:1 #002752);
            }
            
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
            
            QTextEdit {
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', monospace;
                selection-background-color: #007bff;
            }
            
            QTextEdit:focus {
                border-color: #007bff;
            }
            
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                text-align: center;
                background: white;
                color: #495057;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #28a745, stop:1 #20c997);
                border-radius: 6px;
            }
            
            QLabel {
                color: #495057;
            }
            
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                min-height: 16px;
                max-width: 120px;
                selection-background-color: #0056b3;
            }
            
            QComboBox:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
            
            QComboBox:on {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #004085, stop:1 #002752);
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left-width: 0px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #f8f9fa;
                border: 2px solid #007bff;
                border-radius: 8px;
                selection-background-color: #007bff;
                selection-color: white;
            }
        """)

    def browse_directory(self):
        try:
            texts = self.get_ui_texts()
            directory = QFileDialog.getExistingDirectory(
                self, 
                texts["browse_btn"].replace("📁 ", ""),
                default_project_path
            )
            if directory:
                self.start_scan(directory)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, texts["error_title"], f"{texts['error_message'].format(str(e))}")

    def start_scan(self, directory):
        try:
            texts = self.get_ui_texts()
            
            self.stop_event.clear()
            self.scan_button.setEnabled(False)
            self.browse_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
            self.results_text.clear()
            self.status_label.setText(texts["scan_started"])
            
            # Запускаем сканирование в отдельном потоке
            self.scan_worker = ScanWorker(directory, self.stop_event)
            self.scan_worker.progress_updated.connect(self.update_progress)
            self.scan_worker.scan_completed.connect(self.scan_completed)
            self.scan_worker.error_occurred.connect(self.scan_error)
            self.scan_worker.start()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при запуске сканирования: {str(e)}")

    def stop_scan(self):
        self.stop_event.set()
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.quit()
            self.scan_worker.wait()
        
        texts = self.get_ui_texts()
        self.scan_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(texts["scan_stopped"])

    def update_progress(self, message):
        self.status_label.setText(message)
        self.results_text.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")

    def scan_completed(self, data):
        global imports_count, total_imports, project_data
        
        imports_count = data['imports_count']
        total_imports = data['total_imports']
        project_data = data['project_data']
        
        texts = self.get_ui_texts()
        self.scan_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(texts["scan_completed"])
        
        self.display_results()

    def scan_error(self, error_message):
        import traceback
        traceback.print_exc()
        texts = self.get_ui_texts()
        QMessageBox.critical(self, texts["error_title"], f"{texts['error_message'].format(error_message)}")
        
        self.scan_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(texts["error_title"])

    def display_results(self):
        texts = self.get_ui_texts()
        if not imports_count:
            self.results_text.append(texts["no_imports"])
            return

        # Сортируем по количеству импортов
        sorted_imports = sorted(imports_count.items(), key=lambda x: x[1], reverse=True)

        self.results_text.append(f"\n{'='*60}")
        self.results_text.append(f"{texts['window_title'].upper()}")
        self.results_text.append(f"{'='*60}")
        self.results_text.append(texts["total_imports"].format(total_imports))
        self.results_text.append(texts["found_libraries"].format(len(imports_count)))
        self.results_text.append(f"{datetime.datetime.now().strftime('%H:%M:%S')}")
        self.results_text.append(f"\n{texts['top_libraries']}")
        self.results_text.append(f"{'='*60}")

        for i, (lib, count) in enumerate(sorted_imports[:20], 1):
            percentage = (count / total_imports) * 100
            self.results_text.append(f"{i:2d}. {lib:<25} {count:>5} ({percentage:5.1f}%)")

        if len(sorted_imports) > 20:
            self.results_text.append(f"\n{texts['more_libraries'].format(len(sorted_imports) - 20)}")


    def plot_import_statistics(self, plot_type="bar"):
        texts = self.get_ui_texts()
        if not imports_count:
            QMessageBox.warning(self, texts["warning_title"], texts["scan_first"])
            return

        try:
            if plot_type == "bar":
                chart_window = BarChartWindow(imports_count, self)
            else:
                chart_window = PieChartWindow(imports_count, self)
            
            chart_window.show()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, texts["error_title"], f"{texts['error_message'].format(str(e))}")

    def show_stats(self):
        global project_data_ready
        texts = self.get_ui_texts()
        
        if not project_data or len(project_data) == 0:
            QMessageBox.warning(self, texts["warning_title"], texts["scan_first"])
            return

        try:
            # Устанавливаем флаг готовности данных
            project_data_ready = True
            
            stats_window = StatsWindow(project_data, self)
            stats_window.show()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, texts["error_title"], f"{texts['error_message'].format(str(e))}")

    def setup_context_menu(self):
        self.results_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_text.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        texts = self.get_ui_texts()
        context_menu = QMenu(self)
        
        copy_action = QAction(texts["copy_action"], self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        context_menu.addAction(copy_action)
        
        context_menu.exec_(self.results_text.mapToGlobal(position))

    def copy_to_clipboard(self):
        try:
            texts = self.get_ui_texts()
            text = self.results_text.toPlainText()
            if text:
                pyperclip.copy(text)
                self.status_label.setText(texts["copied_to_clipboard"])
        except Exception as e:
            QMessageBox.warning(self, texts["error_title"], f"{texts['error_message'].format(str(e))}")


def main():
    print("Запуск приложения...")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

