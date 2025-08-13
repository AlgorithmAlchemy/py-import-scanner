"""
Окно детального анализа отдельного проекта
"""
import os
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTabWidget, QTextEdit, QLabel, QPushButton, 
                               QTableWidget, QTableWidgetItem, QProgressBar,
                               QFrame, QSplitter, QScrollArea, QComboBox,
                               QFileDialog, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap
# Временно отключаем matplotlib для избежания конфликтов
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib
# matplotlib.use('Qt5Agg')

from ..core.project_analyzer_core import IntegratedProjectAnalyzer
from ..core.configuration import Configuration


def get_ui_texts(language="ru"):
    """Получение текстов интерфейса в соответствии с выбранным языком"""
    texts = {
        "ru": {
            "window_title": "📊 Детальный анализ проекта",
            "title_label": "📊 Детальный анализ проекта",
            "select_folder_btn": "📁 Выбрать папку",
            "analyze_btn": "🔍 Анализировать папку",
            "export_btn": "💾 Экспорт",
            "progress_label": "Выберите папку для анализа",
            "ready_status": "Готов к анализу",
            "folder_selected": "Выбрана папка: {}",
            "warning_title": "Предупреждение",
            "warning_select_folder": "Сначала выберите папку!",
            "error_title": "Ошибка",
            "error_analysis": "Ошибка при анализе:\n{}",
            "error_export": "Ошибка при сохранении отчета:\n{}",
            "success_export": "Отчет сохранен в {}",
            "analysis_completed": "✅ Анализ завершен!",
            "analysis_error": "❌ Ошибка анализа",
            "overview_tab": "📊 Обзор",
            "libraries_tab": "📦 Библиотеки",
            "quality_tab": "✨ Качество",
            "complexity_tab": "📊 Сложность",
            "architecture_tab": "🏗️ Архитектура",
            "dependencies_tab": "🔗 Зависимости",
            "overview_title": "📊 Общая статистика папки",
            "architecture_title": "🏗️ АНАЛИЗ АРХИТЕКТУРЫ ПАПКИ",
            "dependencies_title": "🔗 АНАЛИЗ ЗАВИСИМОСТЕЙ В ПАПКЕ",
            "architecture_placeholder": "Результаты анализа архитектуры папки появятся здесь...",
            "dependencies_placeholder": "Результаты анализа зависимостей в папке появятся здесь...",
            "chart_libraries": "Топ библиотек",
            "chart_quality": "Распределение качества кода",
            "chart_complexity": "Распределение сложности кода",
            "chart_quality_folder": "Распределение качества кода в папке",
            "no_architecture_data": "Данные архитектуры недоступны",
            "no_dependencies_data": "Данные зависимостей недоступны"
        },
        "en": {
            "window_title": "📊 Detailed Project Analysis",
            "title_label": "📊 Detailed Project Analysis",
            "select_folder_btn": "📁 Select Folder",
            "analyze_btn": "🔍 Analyze Folder",
            "export_btn": "💾 Export",
            "progress_label": "Select folder for analysis",
            "ready_status": "Ready for analysis",
            "folder_selected": "Selected folder: {}",
            "warning_title": "Warning",
            "warning_select_folder": "Please select a folder first!",
            "error_title": "Error",
            "error_analysis": "Error during analysis:\n{}",
            "error_export": "Error saving report:\n{}",
            "success_export": "Report saved to {}",
            "analysis_completed": "✅ Analysis completed!",
            "analysis_error": "❌ Analysis error",
            "overview_tab": "📊 Overview",
            "libraries_tab": "📦 Libraries",
            "quality_tab": "✨ Quality",
            "complexity_tab": "📊 Complexity",
            "architecture_tab": "🏗️ Architecture",
            "dependencies_tab": "🔗 Dependencies",
            "overview_title": "📊 General Folder Statistics",
            "architecture_title": "🏗️ FOLDER ARCHITECTURE ANALYSIS",
            "dependencies_title": "🔗 DEPENDENCIES ANALYSIS IN FOLDER",
            "architecture_placeholder": "Folder architecture analysis results will appear here...",
            "dependencies_placeholder": "Folder dependencies analysis results will appear here...",
            "chart_libraries": "Top Libraries",
            "chart_quality": "Code Quality Distribution",
            "chart_complexity": "Code Complexity Distribution",
            "chart_quality_folder": "Code Quality Distribution in Folder",
            "no_architecture_data": "Architecture data unavailable",
            "no_dependencies_data": "Dependencies data unavailable"
        }
    }
    
    return texts.get(language, texts["ru"])


def debug_log(message: str):
    """Функция для отладочного логирования"""
    print(f"[DEBUG] StatsWindow: {message}")
    sys.stdout.flush()


class AnalysisWorker(QThread):
    """Поток для выполнения анализа"""
    progress_updated = Signal(str)
    analysis_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, project_path: Path, config: Configuration):
        debug_log("🔧 Инициализация AnalysisWorker...")
        super().__init__()
        self.project_path = project_path
        self.config = config
        debug_log(f"✅ AnalysisWorker инициализирован с project_path: {project_path}")
        
        try:
            debug_log("🔧 Создание IntegratedProjectAnalyzer...")
            self.analyzer = IntegratedProjectAnalyzer(config)
            debug_log("✅ IntegratedProjectAnalyzer создан")
        except Exception as e:
            debug_log(f"❌ ОШИБКА при создании IntegratedProjectAnalyzer: {e}")
            debug_log(f"Трассировка: {traceback.format_exc()}")
            raise
    
    def run(self):
        debug_log("🚀 AnalysisWorker.run() начат")
        try:
            debug_log("🔍 Вызов analyzer.analyze_project...")
            result = self.analyzer.analyze_project(
                self.project_path, 
                self.progress_updated.emit
            )
            debug_log("✅ Анализ завершен успешно")
            debug_log(f"📊 Результат содержит ключи: {list(result.keys()) if result else 'None'}")
            self.analysis_completed.emit(result)
        except Exception as e:
            debug_log(f"❌ ОШИБКА в AnalysisWorker.run(): {e}")
            debug_log(f"Трассировка: {traceback.format_exc()}")
            self.error_occurred.emit(str(e))


class StatsWindow(QMainWindow):
    """Окно расширенной статистики папки/директории"""
    
    def __init__(self, scan_service=None, language="ru"):
        debug_log("=== ИНИЦИАЛИЗАЦИЯ StatsWindow ===")
        debug_log(f"scan_service: {scan_service}")
        debug_log(f"language: {language}")
        
        try:
            super().__init__()
            debug_log("✅ super().__init__() выполнен")
            
            self.folder_path = None  # Пользователь сам выберет папку
            self.scan_service = scan_service
            self.language = language
            self.texts = get_ui_texts(language)
            self.analysis_result = None
            self.analysis_worker = None
            
            debug_log("✅ Переменные инициализированы")
            
            # Инициализация конфигурации
            debug_log("🔧 Инициализация конфигурации...")
            self.config = Configuration()
            debug_log("✅ Конфигурация создана")
            
            debug_log("🎨 Инициализация UI...")
            self.init_ui()
            debug_log("✅ UI инициализирован")
            
            debug_log("🎨 Настройка стилей...")
            self.setup_styles()
            debug_log("✅ Стили настроены")
            
            # НЕ запускаем анализ автоматически - пользователь сам выберет папку
            debug_log("ℹ️ Анализ не запускается автоматически - пользователь выберет папку")
            
            debug_log("✅ StatsWindow инициализирован успешно")
            
        except Exception as e:
            debug_log(f"❌ ОШИБКА при инициализации StatsWindow: {e}")
            debug_log(f"Трассировка: {traceback.format_exc()}")
            raise
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        debug_log("🎨 Начало инициализации UI...")
        
        self.setWindowTitle(self.texts["window_title"])
        self.setMinimumSize(1200, 800)
        debug_log("✅ Заголовок и размер окна установлены")
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel(self.texts["title_label"])
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
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
        self.select_folder_btn = QPushButton(self.texts["select_folder_btn"])
        self.select_folder_btn.setFont(QFont("Segoe UI", 11))
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.select_folder_btn.setStyleSheet("""
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
        """)
        
        self.analyze_btn = QPushButton(self.texts["analyze_btn"])
        self.analyze_btn.setFont(QFont("Segoe UI", 11))
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.export_btn = QPushButton("💾 Экспорт")
        self.export_btn.setFont(QFont("Segoe UI", 11))
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        control_layout.addWidget(self.select_folder_btn)
        control_layout.addWidget(self.analyze_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # Прогресс бар
        self.progress_label = QLabel(self.texts["progress_label"])
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
        
        # Вкладки с результатами
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
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Создаем вкладки
        self.create_overview_tab()
        self.create_libraries_tab()
        self.create_quality_tab()
        self.create_complexity_tab()
        self.create_architecture_tab()
        self.create_dependencies_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Статус бар
        self.statusBar().showMessage("Готов к анализу")
        
        debug_log("✅ UI полностью инициализирован")
    
    def create_overview_tab(self):
        """Создание вкладки обзора"""
        overview_widget = QWidget()
        layout = QVBoxLayout(overview_widget)
        
        # Общая статистика
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        stats_layout = QGridLayout(stats_frame)
        
        # Заголовок
        stats_title = QLabel("📊 Общая статистика папки")
        stats_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        stats_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        stats_layout.addWidget(stats_title, 0, 0, 1, 2)
        
        # Статистические метрики
        self.stats_labels = {}
        metrics = [
            ("total_files", "📁 Всего файлов"),
            ("total_lines", "📝 Всего строк"),
            ("total_imports", "📦 Всего импортов"),
            ("unique_libraries", "🔧 Уникальных библиотек"),
            ("average_complexity", "📊 Средняя сложность"),
            ("quality_score", "✨ Среднее качество"),
            ("scan_duration", "⏱️ Время анализа")
        ]
        
        for i, (key, label) in enumerate(metrics):
            row = (i // 2) + 1
            col = (i % 2) * 2
            
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Segoe UI", 10, QFont.Bold))
            label_widget.setStyleSheet("color: #2c3e50;")
            
            value_widget = QLabel("—")
            value_widget.setFont(QFont("Segoe UI", 12))
            value_widget.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            stats_layout.addWidget(label_widget, row, col)
            stats_layout.addWidget(value_widget, row, col + 1)
            
            self.stats_labels[key] = value_widget
        
        layout.addWidget(stats_frame)
        
        # Графики
        charts_frame = QFrame()
        charts_frame.setFrameStyle(QFrame.StyledPanel)
        charts_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        charts_layout = QHBoxLayout(charts_frame)
        
        # График топ библиотек
        self.libraries_chart = self.create_chart("Топ библиотек")
        charts_layout.addWidget(self.libraries_chart)
        
        # График распределения качества
        self.quality_chart = self.create_chart("Распределение качества кода")
        charts_layout.addWidget(self.quality_chart)
        
        layout.addWidget(charts_frame)
        
        self.tab_widget.addTab(overview_widget, "📊 Обзор")
    
    def create_libraries_tab(self):
        """Создание вкладки библиотек"""
        libraries_widget = QWidget()
        layout = QVBoxLayout(libraries_widget)
        
        # Таблица библиотек
        self.libraries_table = QTableWidget()
        self.libraries_table.setColumnCount(5)
        self.libraries_table.setHorizontalHeaderLabels([
            "Библиотека", "Количество", "Процент", "Файлы", "Первый файл"
        ])
        self.libraries_table.setStyleSheet("""
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
        
        layout.addWidget(self.libraries_table)
        
        self.tab_widget.addTab(libraries_widget, "📦 Библиотеки")
    
    def create_quality_tab(self):
        """Создание вкладки качества"""
        quality_widget = QWidget()
        layout = QVBoxLayout(quality_widget)
        
        # График качества
        self.quality_distribution_chart = self.create_chart("Распределение качества кода в папке")
        layout.addWidget(self.quality_distribution_chart)
        
        # Таблица файлов с проблемами
        self.quality_table = QTableWidget()
        self.quality_table.setColumnCount(4)
        self.quality_table.setHorizontalHeaderLabels([
            "Файл", "Качество", "Проблемы", "Сложность"
        ])
        self.quality_table.setStyleSheet("""
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
        
        layout.addWidget(self.quality_table)
        
        self.tab_widget.addTab(quality_widget, "✨ Качество")
    
    def create_complexity_tab(self):
        """Создание вкладки сложности"""
        complexity_widget = QWidget()
        layout = QVBoxLayout(complexity_widget)
        
        # График сложности
        self.complexity_chart = self.create_chart("Распределение сложности кода")
        layout.addWidget(self.complexity_chart)
        
        # Таблица сложных файлов
        self.complexity_table = QTableWidget()
        self.complexity_table.setColumnCount(3)
        self.complexity_table.setHorizontalHeaderLabels([
            "Файл", "Сложность", "Строк"
        ])
        self.complexity_table.setStyleSheet("""
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
        
        layout.addWidget(self.complexity_table)
        
        self.tab_widget.addTab(complexity_widget, "📊 Сложность")
    
    def create_architecture_tab(self):
        """Создание вкладки архитектуры"""
        architecture_widget = QWidget()
        layout = QVBoxLayout(architecture_widget)
        
        # Текстовое представление архитектуры
        self.architecture_text = QTextEdit()
        self.architecture_text.setFont(QFont("Consolas", 10))
        self.architecture_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                color: #2c3e50;
            }
        """)
        self.architecture_text.setPlaceholderText("Результаты анализа архитектуры папки появятся здесь...")
        
        layout.addWidget(self.architecture_text)
        
        self.tab_widget.addTab(architecture_widget, "🏗️ Архитектура")
    
    def create_dependencies_tab(self):
        """Создание вкладки зависимостей"""
        dependencies_widget = QWidget()
        layout = QVBoxLayout(dependencies_widget)
        
        # Текстовое представление зависимостей
        self.dependencies_text = QTextEdit()
        self.dependencies_text.setFont(QFont("Consolas", 10))
        self.dependencies_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                color: #2c3e50;
            }
        """)
        self.dependencies_text.setPlaceholderText("Результаты анализа зависимостей в папке появятся здесь...")
        
        layout.addWidget(self.dependencies_text)
        
        self.tab_widget.addTab(dependencies_widget, "🔗 Зависимости")
    
    def create_chart(self, title: str):
        """Создание заглушки для графика"""
        # Временно создаем простой виджет вместо графика
        from PySide6.QtWidgets import QLabel
        label = QLabel(f"📊 {title}\n(График временно недоступен)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 20px;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        return label
    
    def setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
        """)
    
    def select_folder(self):
        """Выбор папки для анализа"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку для анализа",
            os.getcwd()
        )
        
        if directory:
            self.folder_path = Path(directory)
            self.analyze_btn.setEnabled(True)
            self.progress_label.setText(self.texts["folder_selected"].format(directory))
            self.statusBar().showMessage(f"Папка: {directory}")
    
    def start_analysis(self):
        """Запуск анализа папки"""
        debug_log("🚀 Запуск анализа папки...")
        debug_log(f"folder_path: {self.folder_path}")
        
        if not self.folder_path:
            debug_log("❌ folder_path не установлен")
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите папку!")
            return
        
        debug_log("✅ folder_path установлен, начинаем анализ")
        
        # Отключаем кнопки
        self.analyze_btn.setEnabled(False)
        self.select_folder_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        debug_log("✅ Кнопки отключены")
        
        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        debug_log("✅ Прогресс бар показан")
        
        # Запускаем анализ в отдельном потоке
        debug_log("🔧 Создание AnalysisWorker...")
        try:
            self.analysis_worker = AnalysisWorker(self.folder_path, self.config)
            debug_log("✅ AnalysisWorker создан")
            
            self.analysis_worker.progress_updated.connect(self.update_progress)
            self.analysis_worker.analysis_completed.connect(self.analysis_completed)
            self.analysis_worker.error_occurred.connect(self.analysis_error)
            debug_log("✅ Сигналы подключены")
            
            debug_log("🚀 Запуск потока анализа...")
            self.analysis_worker.start()
            debug_log("✅ Поток анализа запущен")
            
        except Exception as e:
            debug_log(f"❌ ОШИБКА при создании AnalysisWorker: {e}")
            debug_log(f"Трассировка: {traceback.format_exc()}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при запуске анализа:\n{e}")
            # Включаем кнопки обратно
            self.analyze_btn.setEnabled(True)
            self.select_folder_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def update_progress(self, message: str):
        """Обновление прогресса"""
        self.progress_label.setText(message)
        self.statusBar().showMessage(message)
    
    def analysis_completed(self, result: Dict[str, Any]):
        """Завершение анализа"""
        self.analysis_result = result
        
        # Скрываем прогресс
        self.progress_bar.setVisible(False)
        
        # Включаем кнопки
        self.analyze_btn.setEnabled(True)
        self.select_folder_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Обновляем данные
        self.update_statistics()
        self.update_libraries_table()
        self.update_quality_tab()
        self.update_complexity_tab()
        self.update_architecture_tab()
        self.update_dependencies_tab()
        
        self.progress_label.setText(self.texts["analysis_completed"])
        self.statusBar().showMessage("Анализ завершен успешно")
    
    def analysis_error(self, error_message: str):
        """Обработка ошибки анализа"""
        QMessageBox.critical(self, "Ошибка", f"Ошибка при анализе:\n{error_message}")
        
        # Включаем кнопки
        self.analyze_btn.setEnabled(True)
        self.select_folder_btn.setEnabled(True)
        
        # Скрываем прогресс
        self.progress_bar.setVisible(False)
        
        self.progress_label.setText(self.texts["analysis_error"])
        self.statusBar().showMessage("Ошибка анализа")
    
    def update_statistics(self):
        """Обновление статистики"""
        if not self.analysis_result:
            return
        
        stats = self.analysis_result['project_stats']
        
        # Обновляем метрики
        self.stats_labels['total_files'].setText(str(stats['total_files']))
        self.stats_labels['total_lines'].setText(str(stats['total_lines']))
        self.stats_labels['total_imports'].setText(str(stats['total_imports']))
        self.stats_labels['unique_libraries'].setText(str(stats['unique_libraries']))
        self.stats_labels['average_complexity'].setText(f"{stats['average_complexity']:.2f}")
        self.stats_labels['quality_score'].setText(f"{stats['quality_score']:.2f}")
        self.stats_labels['scan_duration'].setText(f"{stats['scan_duration']:.2f}с")
        
        # Обновляем графики
        self.update_libraries_chart()
        self.update_quality_chart()
    
    def update_libraries_table(self):
        """Обновление таблицы библиотек"""
        if not self.analysis_result:
            return
        
        libraries = self.analysis_result['top_libraries']
        
        self.libraries_table.setRowCount(len(libraries))
        
        for i, lib in enumerate(libraries):
            self.libraries_table.setItem(i, 0, QTableWidgetItem(lib['name']))
            self.libraries_table.setItem(i, 1, QTableWidgetItem(str(lib['count'])))
            self.libraries_table.setItem(i, 2, QTableWidgetItem(f"{lib['percentage']:.1f}%"))
            self.libraries_table.setItem(i, 3, QTableWidgetItem(str(len(lib['files']))))
            self.libraries_table.setItem(i, 4, QTableWidgetItem(lib['first_occurrence']))
        
        self.libraries_table.resizeColumnsToContents()
    
    def update_libraries_chart(self):
        """Обновление графика библиотек"""
        if not self.analysis_result:
            return
        
        # Временно отключаем обновление графиков
        pass
    
    def update_quality_chart(self):
        """Обновление графика качества"""
        if not self.analysis_result:
            return
        
        # Временно отключаем обновление графиков
        pass
    
    def update_quality_tab(self):
        """Обновление вкладки качества"""
        if not self.analysis_result:
            return
        
        files_analysis = self.analysis_result['files_analysis']
        
        # Сортируем по качеству
        sorted_files = sorted(files_analysis, key=lambda x: x['quality_score'])
        
        self.quality_table.setRowCount(len(sorted_files))
        
        for i, file_analysis in enumerate(sorted_files):
            self.quality_table.setItem(i, 0, QTableWidgetItem(file_analysis['path']))
            self.quality_table.setItem(i, 1, QTableWidgetItem(f"{file_analysis['quality_score']:.1f}"))
            self.quality_table.setItem(i, 2, QTableWidgetItem(str(len(file_analysis['issues']))))
            self.quality_table.setItem(i, 3, QTableWidgetItem(f"{file_analysis['complexity']:.1f}"))
        
        self.quality_table.resizeColumnsToContents()
    
    def update_complexity_tab(self):
        """Обновление вкладки сложности"""
        if not self.analysis_result:
            return
        
        files_analysis = self.analysis_result['files_analysis']
        
        # Сортируем по сложности
        sorted_files = sorted(files_analysis, key=lambda x: x['complexity'], reverse=True)
        
        self.complexity_table.setRowCount(len(sorted_files))
        
        for i, file_analysis in enumerate(sorted_files):
            self.complexity_table.setItem(i, 0, QTableWidgetItem(file_analysis['path']))
            self.complexity_table.setItem(i, 1, QTableWidgetItem(f"{file_analysis['complexity']:.1f}"))
            self.complexity_table.setItem(i, 2, QTableWidgetItem(str(file_analysis['lines'])))
        
        self.complexity_table.resizeColumnsToContents()
    
    def update_architecture_tab(self):
        """Обновление вкладки архитектуры"""
        if not self.analysis_result:
            return
        
        architecture_data = self.analysis_result.get('architecture_data', {})
        
        # Форматируем данные архитектуры
        text = "🏗️ АНАЛИЗ АРХИТЕКТУРЫ ПАПКИ\n"
        text += "=" * 50 + "\n\n"
        
        if architecture_data:
            for key, value in architecture_data.items():
                text += f"{key}: {value}\n"
        else:
            text += "Данные архитектуры недоступны"
        
        self.architecture_text.setText(text)
    
    def update_dependencies_tab(self):
        """Обновление вкладки зависимостей"""
        if not self.analysis_result:
            return
        
        dependency_graph = self.analysis_result.get('dependency_graph', {})
        
        # Форматируем данные зависимостей
        text = "🔗 АНАЛИЗ ЗАВИСИМОСТЕЙ В ПАПКЕ\n"
        text += "=" * 50 + "\n\n"
        
        if dependency_graph:
            for module, dependencies in dependency_graph.items():
                text += f"📦 {module}:\n"
                for dep in dependencies:
                    text += f"  └── {dep}\n"
                text += "\n"
        else:
            text += "Данные зависимостей недоступны"
        
        self.dependencies_text.setText(text)
    
    def export_report(self):
        """Экспорт отчета"""
        if not self.analysis_result:
            QMessageBox.warning(self, "Предупреждение", "Сначала выполните анализ!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет",
            f"project_analysis_{int(time.time())}.json",
            "JSON файлы (*.json);;Текстовые файлы (*.txt)"
        )
        
        if file_path:
            try:
                output_path = Path(file_path)
                format_type = 'json' if file_path.endswith('.json') else 'txt'
                
                # Создаем анализатор для экспорта
                analyzer = IntegratedProjectAnalyzer(self.config)
                analyzer.analysis_result = self.analysis_result
                analyzer.export_report(output_path, format_type)
                
                QMessageBox.information(self, "Успех", f"Отчет сохранен в {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении отчета:\n{e}")
