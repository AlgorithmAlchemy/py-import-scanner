"""
Главное окно приложения с современным PySide6 интерфейсом
"""

import os
import re
import threading
from threading import Event
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                               QProgressBar, QFileDialog, QMenu, QMessageBox,
                               QFrame, QSplitter, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QIcon
import pyperclip
from colorama import init
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import ast

from utils import read_gitignore, is_ignored, find_projects

init(autoreset=True)

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
            imports_count = {}
            task_queue = queue.Queue()
            
            # Сканирование файлов
            self.scan_directory_for_imports_parallel(
                self.directory, 
                self.progress_updated.emit,
                task_queue, 
                self.stop_event
            )
            
            # Получение результатов
            while not task_queue.empty():
                try:
                    task_type, data = task_queue.get_nowait()
                    if task_type == 'imports':
                        imports_count.update(data)
                except queue.Empty:
                    break
                    
            self.scan_completed.emit(imports_count)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def scan_directory_for_imports_parallel(self, directory, progress_callback, task_queue, stop_event):
        """Сканирование директории с параллельной обработкой"""
        if stop_event.is_set():
            return
            
        excluded_dirs = get_gitignore_excluded_dirs()
        py_files = []
        
        # Поиск всех Python файлов
        for root, dirs, files in os.walk(directory):
            if stop_event.is_set():
                return
                
            # Исключаем ненужные папки
            dirs[:] = [d for d in dirs if not is_excluded_directory(d, excluded_dirs)]
            
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
                    
            progress_callback(f"Найдено {len(py_files)} Python файлов...")
        
        # Параллельная обработка файлов
        imports_count = {}
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_file = {
                executor.submit(find_imports_in_file, file_path): file_path 
                for file_path in py_files
            }
            
            completed = 0
            for future in as_completed(future_to_file):
                if stop_event.is_set():
                    return
                    
                completed += 1
                progress_callback(f"Обработано {completed}/{len(py_files)} файлов...")
                
                try:
                    imports = future.result()
                    for imp in imports:
                        imports_count[imp] = imports_count.get(imp, 0) + 1
                except Exception as e:
                    continue
        
        task_queue.put(('imports', imports_count))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.scan_worker = None
        self.imports_count = {}
        self.project_data = {}
        self.project_data_ready = False
        
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("Python Import Parser - Анализ импортов")
        self.setMinimumSize(1000, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Python Import Parser")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Подзаголовок
        subtitle_label = QLabel("Анализ и статистика импортов в Python проектах")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
        
        # Панель управления
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        control_layout = QHBoxLayout(control_frame)
        
        # Кнопки
        self.browse_btn = QPushButton("📁 Выбрать папку")
        self.browse_btn.setFont(QFont("Segoe UI", 11))
        self.browse_btn.clicked.connect(self.browse_directory)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        self.scan_btn = QPushButton("🔍 Сканировать")
        self.scan_btn.setFont(QFont("Segoe UI", 11))
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.stop_btn = QPushButton("⏹ Остановить")
        self.stop_btn.setFont(QFont("Segoe UI", 11))
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.stats_btn = QPushButton("📊 Статистика")
        self.stats_btn.setFont(QFont("Segoe UI", 11))
        self.stats_btn.clicked.connect(self.show_stats)
        self.stats_btn.setEnabled(False)
        self.stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        control_layout.addWidget(self.browse_btn)
        control_layout.addWidget(self.scan_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.stats_btn)
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # Прогресс бар
        self.progress_label = QLabel("Готов к работе")
        self.progress_label.setFont(QFont("Segoe UI", 10))
        self.progress_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        main_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Разделитель
        splitter = QSplitter(Qt.Vertical)
        
        # Область вывода
        output_frame = QFrame()
        output_frame.setFrameStyle(QFrame.StyledPanel)
        output_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
            }
        """)
        
        output_layout = QVBoxLayout(output_frame)
        
        output_label = QLabel("Результаты анализа:")
        output_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        output_label.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        output_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                color: #2c3e50;
            }
        """)
        self.output_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_text.customContextMenuRequested.connect(self.show_context_menu)
        output_layout.addWidget(self.output_text)
        
        splitter.addWidget(output_frame)
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
        
    def setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
        """)
        
    def browse_directory(self):
        """Выбор директории для сканирования"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку с Python проектами",
            os.getcwd()
        )
        
        if directory:
            self.selected_directory = directory
            self.scan_btn.setEnabled(True)
            self.progress_label.setText(f"Выбрана папка: {directory}")
            self.statusBar().showMessage(f"Выбрана папка: {directory}")
            
    def start_scan(self):
        """Запуск сканирования"""
        if not hasattr(self, 'selected_directory'):
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите папку для сканирования!")
            return
            
        self.stop_event.clear()
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        
        self.output_text.clear()
        self.output_text.append("🔍 Начинаю сканирование...\n")
        
        # Запуск потока сканирования
        self.scan_worker = ScanWorker(self.selected_directory, self.stop_event)
        self.scan_worker.progress_updated.connect(self.update_progress)
        self.scan_worker.scan_completed.connect(self.scan_completed)
        self.scan_worker.error_occurred.connect(self.scan_error)
        self.scan_worker.start()
        
    def stop_scan(self):
        """Остановка сканирования"""
        self.stop_event.set()
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.terminate()
            self.scan_worker.wait()
            
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Сканирование остановлено")
        self.statusBar().showMessage("Сканирование остановлено")
        
    def update_progress(self, message):
        """Обновление прогресса"""
        self.progress_label.setText(message)
        self.output_text.append(f"📝 {message}")
        self.output_text.ensureCursorVisible()
        
    def scan_completed(self, imports_count):
        """Завершение сканирования"""
        self.imports_count = imports_count
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.stats_btn.setEnabled(True)
        
        self.progress_label.setText("Сканирование завершено!")
        self.statusBar().showMessage("Сканирование завершено")
        
        # Отображение результатов
        self.display_results(imports_count)
        
    def scan_error(self, error_message):
        """Обработка ошибки сканирования"""
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сканировании:\n{error_message}")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def display_results(self, imports_count):
        """Отображение результатов анализа"""
        if not imports_count:
            self.output_text.append("❌ Импорты не найдены")
            return
            
        total_imports = sum(imports_count.values())
        self.output_text.append(f"\n✅ Найдено {len(imports_count)} уникальных библиотек")
        self.output_text.append(f"📊 Общее количество импортов: {total_imports}\n")
        
        # Сортировка по количеству
        sorted_imports = sorted(imports_count.items(), key=lambda x: x[1], reverse=True)
        
        self.output_text.append("🏆 Топ-10 самых популярных библиотек:")
        for i, (lib, count) in enumerate(sorted_imports[:10], 1):
            percentage = (count / total_imports) * 100
            self.output_text.append(f"{i:2d}. {lib:20s} - {count:4d} ({percentage:5.1f}%)")
            
        if len(sorted_imports) > 10:
            self.output_text.append(f"\n... и еще {len(sorted_imports) - 10} библиотек")
            
    def show_stats(self):
        """Показать окно статистики"""
        if not self.imports_count:
            QMessageBox.information(self, "Информация", "Сначала выполните сканирование!")
            return
            
        # Здесь будет вызов окна статистики
        QMessageBox.information(self, "Статистика", "Окно статистики будет реализовано в следующем обновлении!")
        
    def show_context_menu(self, position):
        """Показать контекстное меню"""
        menu = QMenu(self)
        
        copy_action = QAction("📋 Копировать", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        menu.addAction(copy_action)
        
        clear_action = QAction("🗑 Очистить", self)
        clear_action.triggered.connect(self.output_text.clear)
        menu.addAction(clear_action)
        
        menu.exec_(self.output_text.mapToGlobal(position))
        
    def copy_to_clipboard(self):
        """Копирование в буфер обмена"""
        text = self.output_text.toPlainText()
        if text:
            pyperclip.copy(text)
            self.statusBar().showMessage("Текст скопирован в буфер обмена", 2000)


# Вспомогательные функции (перенесены из main.py)
def get_gitignore_excluded_dirs(gitignore_path='.gitignore'):
    excluded_dirs = []
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            excluded_dirs = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        pass
    return excluded_dirs

def is_excluded_directory(directory, excluded_dirs):
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
        'arq', 'rsa', 'handlers', 'opentele', 'states', 'os', 'utils', 'database', 'time', 'models', 'loader', 'keyboards',
        'sys', 're', 'data', 'commands', 'functions', 'config', 'roop', 'keras', 'configparser', ''
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
        pass

    return imports
