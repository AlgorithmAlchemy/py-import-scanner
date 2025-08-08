# gui/chart_windows.py

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import datetime
import numpy as np


class ChartWindow(QMainWindow):
    """Базовый класс для окон с графиками"""
    
    def __init__(self, imports_count, chart_type, parent=None):
        super().__init__(parent)
        self.imports_count = imports_count
        self.chart_type = chart_type
        self.canvas = None
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        if self.chart_type == "bar":
            self.setWindowTitle("📊 Гистограмма импортов")
            self.setGeometry(200, 200, 1000, 600)
        else:
            self.setWindowTitle("🥧 Круговая диаграмма импортов")
            self.setGeometry(200, 200, 800, 600)
            
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title_label = QLabel(f"Анализ импортов Python - {self.chart_type.upper()}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Создание графика
        self.create_chart()
        if self.canvas:
            main_layout.addWidget(self.canvas)
        
        # Панель кнопок
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Сохранить график")
        save_btn.clicked.connect(self.save_chart)
        save_btn.setMinimumHeight(40)
        
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setMinimumHeight(40)
        
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
    def setup_styles(self):
        """Настройка стилей"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QLabel {
                color: #2c3e50;
                font-size: 16px;
            }
        """)
        
    def create_chart(self):
        """Создание графика (переопределяется в подклассах)"""
        pass
        
    def save_chart(self):
        """Сохранение графика"""
        if not self.canvas:
            QMessageBox.warning(self, "Ошибка", "График не создан")
            return
            
        try:
            # Предлагаем имя файла
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"import_chart_{self.chart_type}_{timestamp}.png"
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Сохранить график", 
                default_name,
                "PNG файлы (*.png);;JPEG файлы (*.jpg);;Все файлы (*)"
            )
            
            if filename:
                # Сохраняем график
                self.canvas.figure.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Успех", f"График сохранен в:\n{filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении:\n{str(e)}")


class BarChartWindow(ChartWindow):
    """Окно с гистограммой"""
    
    def __init__(self, imports_count, parent=None):
        super().__init__(imports_count, "bar", parent)
        
    def create_chart(self):
        """Создание гистограммы"""
        if not self.imports_count:
            return
            
        # Создание фигуры
        fig = Figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
        
        # Подготовка данных
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        top_imports = sorted_imports[:20]  # Топ-20
        
        libraries = [item[0] for item in top_imports]
        counts = [item[1] for item in top_imports]
        
        # Создание графика
        bars = ax.barh(libraries, counts, color='#3498db', alpha=0.8)
        ax.set_title('Топ-20 самых популярных библиотек', fontsize=16, fontweight='bold')
        ax.set_xlabel('Количество импортов', fontsize=14)
        ax.set_ylabel('Библиотеки', fontsize=14)
        
        # Добавление значений на столбцы
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax.text(width + width * 0.01, bar.get_y() + bar.get_height()/2,
                   f'{count}', ha='left', va='center', fontweight='bold')
        
        # Настройка сетки
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        fig.tight_layout()
        
        # Создание canvas
        self.canvas = FigureCanvas(fig)


class PieChartWindow(ChartWindow):
    """Окно с круговой диаграммой"""
    
    def __init__(self, imports_count, parent=None):
        super().__init__(imports_count, "pie", parent)
        
    def create_chart(self):
        """Создание круговой диаграммы"""
        if not self.imports_count:
            return
            
        # Создание фигуры
        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111)
        
        # Подготовка данных
        sorted_imports = sorted(self.imports_count.items(), key=lambda x: x[1], reverse=True)
        top_imports = sorted_imports[:15]  # Топ-15
        others_count = sum(count for _, count in sorted_imports[15:])
        
        libraries = [item[0] for item in top_imports]
        counts = [item[1] for item in top_imports]
        
        # Добавляем "Прочее"
        if others_count > 0:
            libraries.append('Прочее')
            counts.append(others_count)
        
        # Цвета для диаграммы
        colors = plt.cm.Set3(np.linspace(0, 1, len(libraries)))
        
        # Создание круговой диаграммы
        wedges, texts, autotexts = ax.pie(counts, labels=libraries, autopct='%1.1f%%',
                                         startangle=90, colors=colors, explode=[0.05] * len(libraries))
        
        ax.set_title('Распределение импортов по библиотекам', fontsize=16, fontweight='bold')
        
        # Настройка текста
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        fig.tight_layout()
        
        # Создание canvas
        self.canvas = FigureCanvas(fig)
