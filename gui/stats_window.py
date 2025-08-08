"""
Окно статистики с современным PySide6 интерфейсом
"""

import os
import ast
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTabWidget, QTableWidget,
                               QTableWidgetItem, QFrame, QScrollArea, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
import seaborn as sns

from utils import read_gitignore, is_ignored, find_projects

IGNORED_DIRS = {'.git', '__pycache__', '.idea', '.vscode', '.venv', '.eggs'}


class StatsWorker(QThread):
    """Поток для анализа статистики"""
    progress_updated = Signal(str)
    analysis_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        
    def run(self):
        try:
            # Анализ структуры проекта
            structure = self.analyze_project_structure(self.directory)
            
            # Парсинг Python файлов
            project_stats = self.parse_python_files(self.directory)
            
            results = {
                'structure': structure,
                'project_stats': project_stats
            }
            
            self.analysis_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def analyze_project_structure(self, directory):
        """Анализ структуры проекта"""
        self.progress_updated.emit("Анализирую структуру проекта...")
        
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
            
        return structure
    
    def parse_python_files(self, projects_dir, export=True, max_files=5000, max_depth=6):
        """Парсинг Python файлов"""
        self.progress_updated.emit("Парсинг Python файлов...")
        
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
                file_path = os.path.join(root, file)
                scanned_files += 1
                project_stats[project_name]["py_count"] += 1
                
                # Обработка даты
                try:
                    creation_time = os.path.getctime(file_path)
                    creation_date = datetime.datetime.fromtimestamp(creation_time)
                    
                    if project_stats[project_name]["created"] is None:
                        project_stats[project_name]["created"] = creation_date
                    elif creation_date < project_stats[project_name]["created"]:
                        project_stats[project_name]["created"] = creation_date
                except:
                    pass
                    
                # Анализ импортов
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        tree = ast.parse(f.read(), filename=file_path)
                        
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                lib = alias.name.split('.')[0]
                                if lib and lib.isidentifier():
                                    project_stats[project_name]["libs"].add(lib)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                lib = node.module.split('.')[0]
                                if lib and lib.isidentifier():
                                    project_stats[project_name]["libs"].add(lib)
                except:
                    pass
                    
                # Добавление директории
                project_stats[project_name]["dirs"].add(os.path.dirname(file_path))
                
        return project_stats


class StatsWindow(QMainWindow):
    """Окно статистики"""
    
    def __init__(self, imports_count, parent=None):
        super().__init__(parent)
        self.imports_count = imports_count
        self.stats_worker = None
        
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("Статистика проекта - Python Import Parser")
        self.setMinimumSize(1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("📊 Статистика проекта")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #2980b9;
                color: white;
            }
        """)
        
        # Вкладка с графиками
        self.create_charts_tab()
        
        # Вкладка с таблицей
        self.create_table_tab()
        
        # Вкладка с детальной статистикой
        self.create_details_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📄 Экспорт в CSV")
        self.export_btn.setFont(QFont("Segoe UI", 11))
        self.export_btn.clicked.connect(self.export_to_csv)
        self.export_btn.setStyleSheet("""
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
        """)
        
        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.setFont(QFont("Segoe UI", 11))
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
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
        """)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
    def setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
        """)
        
    def create_charts_tab(self):
        """Создание вкладки с графиками"""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # Создание графиков
        self.create_imports_chart()
        self.create_pie_chart()
        
        charts_layout.addWidget(self.imports_canvas)
        charts_layout.addWidget(self.pie_canvas)
        
        self.tab_widget.addTab(charts_widget, "📈 Графики")
        
    def create_table_tab(self):
        """Создание вкладки с таблицей"""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Таблица с данными
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        self.populate_table()
        table_layout.addWidget(self.table)
        
        self.tab_widget.addTab(table_widget, "📋 Таблица")
        
    def create_details_tab(self):
        """Создание вкладки с детальной статистикой"""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Текстовое поле с детальной информацией
        self.details_text = QTextEdit()
        self.details_text.setFont(QFont("Consolas", 10))
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                color: #2c3e50;
            }
        """)
        
        self.populate_details()
        details_layout.addWidget(self.details_text)
        
        self.tab_widget.addTab(details_widget, "📝 Детали")
        
    def create_imports_chart(self):
        """Создание графика импортов"""
        if not self.imports_count:
            return
            
        # Создание фигуры
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Подготовка данных
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        top_imports = sorted_imports[:15]  # Топ-15
        
        libraries = [item[0] for item in top_imports]
        counts = [item[1] for item in top_imports]
        
        # Создание графика
        bars = ax.bar(libraries, counts, color='#3498db', alpha=0.8)
        ax.set_title('Топ-15 самых популярных библиотек', fontsize=14, fontweight='bold')
        ax.set_xlabel('Библиотеки', fontsize=12)
        ax.set_ylabel('Количество импортов', fontsize=12)
        
        # Поворот подписей
        ax.tick_params(axis='x', rotation=45)
        
        # Добавление значений на столбцы
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{count}', ha='center', va='bottom', fontweight='bold')
        
        fig.tight_layout()
        
        # Создание canvas
        self.imports_canvas = FigureCanvas(fig)
        
    def create_pie_chart(self):
        """Создание круговой диаграммы"""
        if not self.imports_count:
            return
            
        # Создание фигуры
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        # Подготовка данных
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        top_imports = sorted_imports[:10]  # Топ-10
        
        # Группировка остальных
        other_count = sum(count for _, count in sorted_imports[10:])
        if other_count > 0:
            top_imports.append(('Остальные', other_count))
        
        libraries = [item[0] for item in top_imports]
        counts = [item[1] for item in top_imports]
        
        # Цвета
        colors = plt.cm.Set3(np.linspace(0, 1, len(libraries)))
        
        # Создание круговой диаграммы
        wedges, texts, autotexts = ax.pie(counts, labels=libraries, autopct='%1.1f%%',
                                         colors=colors, startangle=90)
        ax.set_title('Распределение импортов', fontsize=14, fontweight='bold')
        
        # Настройка текста
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        fig.tight_layout()
        
        # Создание canvas
        self.pie_canvas = FigureCanvas(fig)
        
    def populate_table(self):
        """Заполнение таблицы данными"""
        if not self.imports_count:
            return
            
        # Подготовка данных
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        total_imports = sum(self.imports_count.values())
        
        # Настройка таблицы
        self.table.setRowCount(len(sorted_imports))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Место', 'Библиотека', 'Количество', 'Процент'])
        
        # Заполнение данных
        for i, (lib, count) in enumerate(sorted_imports):
            percentage = (count / total_imports) * 100
            
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(lib))
            self.table.setItem(i, 2, QTableWidgetItem(str(count)))
            self.table.setItem(i, 3, QTableWidgetItem(f"{percentage:.1f}%"))
            
        # Автоматическая подгонка размеров
        self.table.resizeColumnsToContents()
        
    def populate_details(self):
        """Заполнение детальной информации"""
        if not self.imports_count:
            return
            
        total_imports = sum(self.imports_count.values())
        unique_libs = len(self.imports_count)
        
        details = f"""
📊 ДЕТАЛЬНАЯ СТАТИСТИКА ИМПОРТОВ
{'='*50}

📈 ОБЩАЯ ИНФОРМАЦИЯ:
• Всего уникальных библиотек: {unique_libs}
• Общее количество импортов: {total_imports}
• Среднее количество импортов на библиотеку: {total_imports/unique_libs:.1f}

🏆 ТОП-20 САМЫХ ПОПУЛЯРНЫХ БИБЛИОТЕК:
{'='*50}
"""
        
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        
        for i, (lib, count) in enumerate(sorted_imports[:20], 1):
            percentage = (count / total_imports) * 100
            details += f"{i:2d}. {lib:25s} - {count:4d} импортов ({percentage:5.1f}%)\n"
            
        details += f"""
📋 ПОЛНЫЙ СПИСОК БИБЛИОТЕК:
{'='*50}
"""
        
        for i, (lib, count) in enumerate(sorted_imports, 1):
            percentage = (count / total_imports) * 100
            details += f"{i:3d}. {lib:25s} - {count:4d} ({percentage:5.1f}%)\n"
            
        self.details_text.setText(details)
        
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        if not self.imports_count:
            return
            
        try:
            # Создание DataFrame
            data = []
            total_imports = sum(self.imports_count.values())
            
            for lib, count in self.imports_count.items():
                percentage = (count / total_imports) * 100
                data.append({
                    'Библиотека': lib,
                    'Количество_импортов': count,
                    'Процент': round(percentage, 2)
                })
                
            df = pd.DataFrame(data)
            df = df.sort_values('Количество_импортов', ascending=False)
            
            # Сохранение файла
            filename = f"import_statistics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Успех", f"Данные экспортированы в файл: {filename}")
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")


# Функция для открытия окна статистики (совместимость с существующим кодом)
def open_stats_window(parent, imports_count):
    """Открытие окна статистики"""
    stats_window = StatsWindow(imports_count, parent)
    stats_window.show()
    return stats_window
