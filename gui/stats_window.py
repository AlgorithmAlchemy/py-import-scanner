"""
Окно статистики с современным PySide6 интерфейсом
"""

import os
import ast
import datetime
import pandas as pd
import matplotlib.pyplot as plt
# Используем Agg backend для совместимости
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTabWidget, QTableWidget,
                               QTableWidgetItem, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from utils import read_gitignore, is_ignored

IGNORED_DIRS = {'.git', '__pycache__', '.idea', '.vscode', '.venv', '.eggs'}


# =========================
# СТАНДАРТНЫЕ ФУНКЦИИ ДЛЯ ИМПОРТА
# =========================

def analyze_project_structure(directory, task_queue):
    """Анализ структуры проекта - функция для импорта из main.py"""
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
    """Парсинг Python файлов - функция для импорта из main.py"""
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


# =========================
# КЛАССЫ ДЛЯ GUI
# =========================

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
    
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.imports_count = {}  # Будет заполнено из project_data
        self.stats_worker = None
        
        # Извлекаем данные об импортах из project_data
        self.extract_imports_data()
        
        self.init_ui()
        self.setup_styles()
        
    def extract_imports_data(self):
        """Извлечение данных об импортах из project_data"""
        if not self.project_data:
            self.imports_count = {}
            return
            
        # Собираем все импорты из всех проектов
        all_imports = []
        
        # Проверяем, является ли project_data pandas DataFrame
        if hasattr(self.project_data, 'to_dict'):
            # Это pandas DataFrame
            project_list = self.project_data.to_dict('records')
        else:
            # Это уже список словарей
            project_list = self.project_data
            
        for project in project_list:
            # Проверяем разные возможные ключи для импортов
            if 'stack' in project and project['stack']:
                all_imports.extend(project['stack'])
            elif 'imports' in project and project['imports']:
                all_imports.extend(project['imports'])
            elif 'libs' in project and project['libs']:
                all_imports.extend(project['libs'])
        
        # Подсчитываем количество каждого импорта
        from collections import Counter
        self.imports_count = dict(Counter(all_imports))
        
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
        
        # Вкладка с обзором
        self.create_overview_tab()
        
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
        
    def create_overview_tab(self):
        """Создание вкладки с обзором"""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Заголовок обзора
        overview_title = QLabel("📋 Обзор статистики")
        overview_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        overview_title.setAlignment(Qt.AlignCenter)
        overview_layout.addWidget(overview_title)
        
        # Основная статистика
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        stats_text.setFont(QFont("Consolas", 11))
        stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                color: #2c3e50;
            }
        """)
        
        # Формируем статистику
        stats_content = self.generate_overview_stats()
        stats_text.setPlainText(stats_content)
        
        overview_layout.addWidget(stats_text)
        
        self.tab_widget.addTab(overview_widget, "📋 Обзор")
        
    def generate_overview_stats(self):
        """Генерация текста обзора статистики"""
        if not self.imports_count:
            return "Нет данных для анализа"
            
        total_imports = sum(self.imports_count.values())
        unique_libraries = len(self.imports_count)
        
        # Топ-10 библиотек
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        top_10 = sorted_imports[:10]
        
        stats = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ОБЗОР СТАТИСТИКИ ИМПОРТОВ                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 ОБЩАЯ СТАТИСТИКА:
   • Общее количество импортов: {total_imports:,}
   • Уникальных библиотек: {unique_libraries:,}
   • Среднее использование на библиотеку: {total_imports/unique_libraries:.1f}

🏆 ТОП-10 САМЫХ ПОПУЛЯРНЫХ БИБЛИОТЕК:
"""
        
        for i, (lib, count) in enumerate(top_10, 1):
            percentage = (count / total_imports) * 100
            stats += f"   {i:2d}. {lib:<20} {count:>8,} импортов ({percentage:>5.1f}%)\n"
        
        stats += f"""
📈 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
   • Библиотеки с 1 импортом: {sum(1 for count in self.imports_count.values() if count == 1):,}
   • Библиотеки с 2-5 импортами: {sum(1 for count in self.imports_count.values() if 2 <= count <= 5):,}
   • Библиотеки с 6-10 импортами: {sum(1 for count in self.imports_count.values() if 6 <= count <= 10):,}
   • Библиотеки с 10+ импортами: {sum(1 for count in self.imports_count.values() if count > 10):,}

💡 РЕКОМЕНДАЦИИ:
   • Самые используемые библиотеки: {', '.join(lib for lib, _ in top_10[:3])}
   • Рассмотрите возможность оптимизации импортов
   • Проверьте неиспользуемые зависимости
"""
        
        return stats
        
    def create_charts_tab(self):
        """Создание вкладки с графиками"""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # Заголовок
        charts_title = QLabel("📈 Графики статистики")
        charts_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        charts_title.setAlignment(Qt.AlignCenter)
        charts_layout.addWidget(charts_title)
        
        # Информация о том, что графики открываются в отдельных окнах
        info_label = QLabel("💡 Графики открываются в отдельных окнах для лучшего просмотра")
        info_label.setFont(QFont("Segoe UI", 10))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666; padding: 10px;")
        charts_layout.addWidget(info_label)
        
        # Кнопки для открытия графиков
        buttons_layout = QHBoxLayout()
        
        bar_button = QPushButton("📊 Открыть гистограмму")
        bar_button.setFont(QFont("Segoe UI", 11))
        bar_button.clicked.connect(self.open_bar_chart)
        buttons_layout.addWidget(bar_button)
        
        pie_button = QPushButton("🥧 Открыть круговую диаграмму")
        pie_button.setFont(QFont("Segoe UI", 11))
        pie_button.clicked.connect(self.open_pie_chart)
        buttons_layout.addWidget(pie_button)
        
        charts_layout.addLayout(buttons_layout)
        
        # Добавляем растягивающийся виджет для заполнения пространства
        charts_layout.addStretch()
        
        self.tab_widget.addTab(charts_widget, "📈 Графики")
        
    def open_bar_chart(self):
        """Открыть гистограмму в отдельном окне"""
        try:
            from gui.chart_windows import BarChartWindow
            chart_window = BarChartWindow(self.imports_count, self)
            chart_window.show()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии гистограммы: {str(e)}")
    
    def open_pie_chart(self):
        """Открыть круговую диаграмму в отдельном окне"""
        try:
            from gui.chart_windows import PieChartWindow
            chart_window = PieChartWindow(self.imports_count, self)
            chart_window.show()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии круговой диаграммы: {str(e)}")
        
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
        if not self.project_data:
            self.details_text.setText("Нет данных о проектах для отображения")
            return
            
        # Проверяем, является ли project_data pandas DataFrame
        if hasattr(self.project_data, 'to_dict'):
            # Это pandas DataFrame
            project_list = self.project_data.to_dict('records')
        else:
            # Это уже список словарей
            project_list = self.project_data
            
        details = f"""
📊 ДЕТАЛЬНАЯ СТАТИСТИКА ПРОЕКТОВ
{'='*60}

📈 ОБЩАЯ ИНФОРМАЦИЯ:
• Всего проектов: {len(project_list)}
• Всего уникальных библиотек: {len(self.imports_count)}
• Общее количество импортов: {sum(self.imports_count.values())}

🏗️ АНАЛИЗ ПРОЕКТОВ:
{'='*60}
"""
        
        # Группируем проекты по типам
        project_types = {}
        for project in project_list:
            project_type = project.get('type', 'Неизвестно')
            if project_type not in project_types:
                project_types[project_type] = []
            project_types[project_type].append(project)
        
        details += f"\n📁 РАСПРЕДЕЛЕНИЕ ПО ТИПАМ ПРОЕКТОВ:\n"
        for project_type, projects in project_types.items():
            details += f"• {project_type}: {len(projects)} проектов\n"
        
        details += f"\n📋 СПИСОК ВСЕХ ПРОЕКТОВ:\n"
        details += f"{'='*60}\n"
        
        for i, project in enumerate(project_list, 1):
            name = project.get('name', 'Неизвестно')
            date = project.get('date', 'Неизвестно')
            py_count = project.get('py_count', 0)
            
            # Определяем количество импортов
            imports_list = []
            if 'stack' in project and project['stack']:
                imports_list = project['stack']
            elif 'imports' in project and project['imports']:
                imports_list = project['imports']
            elif 'libs' in project and project['libs']:
                imports_list = list(project['libs'])
            
            imports_count = len(imports_list)
            
            details += f"{i:3d}. {name}\n"
            details += f"     📅 Дата: {date}\n"
            details += f"     📄 Python файлов: {py_count}\n"
            details += f"     📦 Импортов: {imports_count}\n"
            
            if imports_list:
                # Показываем топ-5 импортов
                top_imports = imports_list[:5]
                details += f"     🔝 Топ импорты: {', '.join(top_imports)}\n"
            
            details += "\n"
            
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
def open_stats_window(parent, project_data):
    """Открытие окна статистики"""
    stats_window = StatsWindow(project_data, parent)
    stats_window.show()
    return stats_window
