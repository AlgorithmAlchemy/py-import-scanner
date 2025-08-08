# stats_window.py

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
import ast
import datetime
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTabWidget, QTableWidget,
                               QTableWidgetItem, QFrame, QScrollArea, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

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


class StatsWindow(QMainWindow):
    def __init__(self, imports_count, parent=None):
        super().__init__(parent)
        self.imports_count = imports_count
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        self.setWindowTitle("📊 Статистика по проектам")
        self.setGeometry(200, 200, 1000, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя сводка
        summary_frame = QFrame()
        summary_layout = QVBoxLayout(summary_frame)
        
        self.summary_label = QLabel("📦 Анализ проектов")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setFont(QFont("Arial", 14, QFont.Bold))
        summary_layout.addWidget(self.summary_label)
        
        main_layout.addWidget(summary_frame)
        
        # Табы для разных видов статистики
        self.tab_widget = QTabWidget()
        
        # Таб с графиками
        self.charts_tab = self.create_charts_tab()
        self.tab_widget.addTab(self.charts_tab, "📊 Графики")
        
        # Таб с таблицей
        self.table_tab = self.create_table_tab()
        self.tab_widget.addTab(self.table_tab, "📋 Таблица")
        
        # Таб с деталями
        self.details_tab = self.create_details_tab()
        self.tab_widget.addTab(self.details_tab, "📝 Детали")
        
        main_layout.addWidget(self.tab_widget)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("💾 Экспорт в CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        
        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
    def setup_styles(self):
        """Настройка современного стиля"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a90e2;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #444444;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444444;
            }
        """)
        
    def create_charts_tab(self):
        """Создание таба с графиками"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # График импортов
        self.imports_chart = self.create_imports_chart()
        layout.addWidget(self.imports_chart)
        
        return widget
        
    def create_table_tab(self):
        """Создание таба с таблицей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.table = QTableWidget()
        self.populate_table()
        layout.addWidget(self.table)
        
        return widget
        
    def create_details_tab(self):
        """Создание таба с деталями"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.populate_details()
        layout.addWidget(self.details_text)
        
        return widget
        
    def create_imports_chart(self):
        """Создание графика импортов"""
        if not self.imports_count:
            label = QLabel("Нет данных для отображения")
            label.setAlignment(Qt.AlignCenter)
            return label
            
        # Создаем график
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Сортируем данные
        sorted_imports = sorted(self.imports_count.items(), 
                               key=lambda x: x[1], reverse=True)[:20]
        
        libraries = [lib for lib, _ in sorted_imports]
        counts = [count for _, count in sorted_imports]
        
        # Создаем горизонтальную гистограмму
        bars = ax.barh(libraries, counts, color='skyblue', edgecolor='black')
        
        # Настройки графика
        ax.set_xlabel('Количество использований')
        ax.set_title('Топ-20 используемых библиотек')
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        
        # Добавляем значения на столбцы
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                   str(count), va='center')
        
        plt.tight_layout()
        
        # Создаем canvas для Qt
        canvas = FigureCanvas(fig)
        return canvas
        
    def populate_table(self):
        """Заполнение таблицы данными"""
        if not self.imports_count:
            return
            
        # Настройка таблицы
        sorted_imports = sorted(self.imports_count.items(), 
                               key=lambda x: x[1], reverse=True)
        
        self.table.setRowCount(len(sorted_imports))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Библиотека', 'Количество', '%'])
        
        total = sum(self.imports_count.values())
        
        for i, (lib, count) in enumerate(sorted_imports):
            percentage = (count / total) * 100
            
            self.table.setItem(i, 0, QTableWidgetItem(lib))
            self.table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{percentage:.2f}%"))
            
        self.table.resizeColumnsToContents()
        
    def populate_details(self):
        """Заполнение детальной информации"""
        if not self.imports_count:
            self.details_text.setText("Нет данных для отображения")
            return
            
        total = sum(self.imports_count.values())
        unique_libs = len(self.imports_count)
        
        details = f"""
📊 ДЕТАЛЬНАЯ СТАТИСТИКА ИМПОРТОВ

📈 Общая информация:
• Всего импортов: {total:,}
• Уникальных библиотек: {unique_libs}
• Среднее использование: {total/unique_libs:.1f}

🏆 Топ-10 библиотек:
"""
        
        sorted_imports = sorted(self.imports_count.items(), 
                               key=lambda x: x[1], reverse=True)[:10]
        
        for i, (lib, count) in enumerate(sorted_imports, 1):
            percentage = (count / total) * 100
            details += f"{i:2d}. {lib:<20} {count:>6} ({percentage:>5.1f}%)\n"
            
        self.details_text.setText(details)
        
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        if not self.imports_count:
            return
            
        import pandas as pd
        
        # Создаем DataFrame
        data = []
        total = sum(self.imports_count.values())
        
        for lib, count in self.imports_count.items():
            percentage = (count / total) * 100
            data.append({
                'Библиотека': lib,
                'Количество': count,
                'Процент': round(percentage, 2)
            })
            
        df = pd.DataFrame(data)
        df = df.sort_values('Количество', ascending=False)
        
        # Сохраняем файл
        filename = f"imports_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Экспорт", f"Данные сохранены в файл: {filename}")


def open_stats_window(parent, imports_count):
    """Функция для открытия окна статистики"""
    stats_window = StatsWindow(imports_count, parent)
    stats_window.show()
    return stats_window

