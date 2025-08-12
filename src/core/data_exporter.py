"""
Модуль экспорта данных
"""
import json
import csv
import datetime
from typing import Dict, List
from pathlib import Path
import pandas as pd

from .interfaces import IDataExporter, ScanResult


class DataExporter(IDataExporter):
    """Экспортер данных в различные форматы"""
    
    def export_to_csv(self, data: ScanResult, file_path: Path) -> None:
        """
        Экспортирует данные в CSV
        
        Args:
            data: Результат сканирования
            file_path: Путь к файлу для сохранения
        """
        # Подготовка данных для CSV
        csv_data = []
        
        # Данные об импортах
        for library, import_data in data.imports_data.items():
            csv_data.append({
                'Тип': 'Импорт',
                'Название': library,
                'Количество': import_data.count,
                'Процент': round(import_data.percentage, 2),
                'Файлы': len(import_data.files)
            })
        
        # Данные о проектах
        for project in data.projects_data:
            csv_data.append({
                'Тип': 'Проект',
                'Название': project.name,
                'Python файлов': project.py_files_count,
                'Импортов': project.total_imports,
                'Уникальных библиотек': project.unique_libraries,
                'Дата создания': project.created_date.isoformat() if project.created_date else ''
            })
        
        # Запись в CSV
        if csv_data:
            fieldnames = csv_data[0].keys()
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
    
    def export_to_json(self, data: ScanResult, file_path: Path) -> None:
        """
        Экспортирует данные в JSON
        
        Args:
            data: Результат сканирования
            file_path: Путь к файлу для сохранения
        """
        # Подготовка данных для JSON
        json_data = {
            'scan_info': {
                'timestamp': data.scan_timestamp.isoformat(),
                'duration': data.scan_duration,
                'total_files': data.total_files_scanned,
                'total_imports': data.total_imports
            },
            'imports': {
                library: {
                    'count': import_data.count,
                    'percentage': import_data.percentage,
                    'files': import_data.files
                }
                for library, import_data in data.imports_data.items()
            },
            'projects': [
                {
                    'name': project.name,
                    'path': str(project.path),
                    'py_files_count': project.py_files_count,
                    'total_imports': project.total_imports,
                    'unique_libraries': project.unique_libraries,
                    'created_date': project.created_date.isoformat() if project.created_date else None,
                    'directories': list(project.directories),
                    'libraries': list(project.libraries)
                }
                for project in data.projects_data
            ]
        }
        
        # Запись в JSON
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
    
    def export_to_excel(self, data: ScanResult, file_path: Path) -> None:
        """
        Экспортирует данные в Excel
        
        Args:
            data: Результат сканирования
            file_path: Путь к файлу для сохранения
        """
        # Создание Excel файла с несколькими листами
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Лист с импортами
            imports_df = pd.DataFrame([
                {
                    'Библиотека': library,
                    'Количество': import_data.count,
                    'Процент': round(import_data.percentage, 2),
                    'Файлы': len(import_data.files)
                }
                for library, import_data in data.imports_data.items()
            ])
            
            if not imports_df.empty:
                imports_df.to_excel(writer, sheet_name='Импорты', index=False)
            
            # Лист с проектами
            projects_df = pd.DataFrame([
                {
                    'Название': project.name,
                    'Python файлов': project.py_files_count,
                    'Импортов': project.total_imports,
                    'Уникальных библиотек': project.unique_libraries,
                    'Дата создания': project.created_date.isoformat() if project.created_date else '',
                    'Директории': ', '.join(project.directories),
                    'Библиотеки': ', '.join(project.libraries)
                }
                for project in data.projects_data
            ])
            
            if not projects_df.empty:
                projects_df.to_excel(writer, sheet_name='Проекты', index=False)
            
            # Лист со статистикой
            stats_df = pd.DataFrame([
                {
                    'Метрика': 'Общее количество файлов',
                    'Значение': data.total_files_scanned
                },
                {
                    'Метрика': 'Общее количество импортов',
                    'Значение': data.total_imports
                },
                {
                    'Метрика': 'Уникальных библиотек',
                    'Значение': len(data.imports_data)
                },
                {
                    'Метрика': 'Количество проектов',
                    'Значение': len(data.projects_data)
                },
                {
                    'Метрика': 'Время сканирования (сек)',
                    'Значение': round(data.scan_duration, 2)
                },
                {
                    'Метрика': 'Дата сканирования',
                    'Значение': data.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
            ])
            
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
    
    def export_summary_report(self, data: ScanResult, file_path: Path) -> None:
        """
        Экспортирует краткий отчет
        
        Args:
            data: Результат сканирования
            file_path: Путь к файлу для сохранения
        """
        # Создание краткого отчета
        report_lines = [
            "ОТЧЕТ О СКАНИРОВАНИИ ИМПОРТОВ PYTHON",
            "=" * 50,
            f"Дата сканирования: {data.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Время сканирования: {data.scan_duration:.2f} секунд",
            f"Обработано файлов: {data.total_files_scanned}",
            f"Найдено импортов: {data.total_imports}",
            f"Уникальных библиотек: {len(data.imports_data)}",
            f"Количество проектов: {len(data.projects_data)}",
            "",
            "ТОП-10 САМЫХ ПОПУЛЯРНЫХ БИБЛИОТЕК:",
            "-" * 40
        ]
        
        # Сортировка импортов по популярности
        sorted_imports = sorted(
            data.imports_data.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        for i, (library, import_data) in enumerate(sorted_imports[:10], 1):
            report_lines.append(
                f"{i:2d}. {library:<20} {import_data.count:>5} "
                f"({import_data.percentage:>5.1f}%)"
            )
        
        report_lines.extend([
            "",
            "ПРОЕКТЫ:",
            "-" * 20
        ])
        
        for project in data.projects_data:
            report_lines.append(
                f"• {project.name}: {project.py_files_count} файлов, "
                f"{project.total_imports} импортов"
            )
        
        # Запись отчета
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
    
    def export_imports_only_csv(self, data: ScanResult, file_path: Path) -> None:
        """
        Экспортирует только данные об импортах в CSV
        
        Args:
            data: Результат сканирования
            file_path: Путь к файлу для сохранения
        """
        if not data.imports_data:
            return
        
        # Сортировка по количеству импортов
        sorted_imports = sorted(
            data.imports_data.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Место', 'Библиотека', 'Количество', 'Процент']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, (library, import_data) in enumerate(sorted_imports, 1):
                writer.writerow({
                    'Место': i,
                    'Библиотека': library,
                    'Количество': import_data.count,
                    'Процент': round(import_data.percentage, 2)
                })
