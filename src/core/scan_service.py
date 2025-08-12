"""
Главный сервис для координации сканирования
"""
from pathlib import Path
from typing import Optional, Callable
from .interfaces import ScanResult, IProgressReporter
from .configuration import Configuration
from .import_parser import ImportParser
from .project_analyzer import ProjectAnalyzer
from .file_scanner import FileScanner
from .data_exporter import DataExporter


class ScanService:
    """Главный сервис для координации сканирования"""
    
    def __init__(self, config: Configuration = None):
        """
        Инициализация сервиса
        
        Args:
            config: Конфигурация (если None, создается по умолчанию)
        """
        self.config = config or Configuration()
        
        # Создание зависимостей
        self.import_parser = ImportParser(self.config)
        self.project_analyzer = ProjectAnalyzer(self.config)
        self.file_scanner = FileScanner(
            self.config, 
            self.import_parser, 
            self.project_analyzer
        )
        self.data_exporter = DataExporter()
        
        # Состояние
        self.last_scan_result: Optional[ScanResult] = None
        self.is_scanning = False
    
    def scan_directory(self, directory: Path, 
                      progress_callback: Optional[Callable] = None) -> ScanResult:
        """
        Сканирует директорию
        
        Args:
            directory: Директория для сканирования
            progress_callback: Функция обратного вызова для прогресса
            
        Returns:
            Результат сканирования
        """
        if self.is_scanning:
            raise RuntimeError("Сканирование уже выполняется")
        
        try:
            self.is_scanning = True
            
            # Проверка существования директории
            if not directory.exists():
                raise FileNotFoundError(f"Директория не найдена: {directory}")
            
            if not directory.is_dir():
                raise ValueError(f"Путь не является директорией: {directory}")
            
            # Выполнение сканирования
            result = self.file_scanner.scan_directory(directory, progress_callback)
            
            # Сохранение результата
            self.last_scan_result = result
            
            return result
            
        finally:
            self.is_scanning = False
    
    def get_last_result(self) -> Optional[ScanResult]:
        """
        Возвращает результат последнего сканирования
        
        Returns:
            Результат сканирования или None
        """
        return self.last_scan_result
    
    def export_results(self, result: ScanResult, 
                      output_dir: Path,
                      formats: list = None) -> dict:
        """
        Экспортирует результаты в различные форматы
        
        Args:
            result: Результат сканирования
            output_dir: Директория для сохранения
            formats: Список форматов для экспорта
            
        Returns:
            Словарь с путями к созданным файлам
        """
        if formats is None:
            formats = ['csv', 'json', 'txt']
        
        # Создание директории если не существует
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерация имени файла с временной меткой
        timestamp = result.scan_timestamp.strftime('%Y%m%d_%H%M%S')
        base_name = f"import_scan_{timestamp}"
        
        exported_files = {}
        
        try:
            # Экспорт в CSV
            if 'csv' in formats:
                csv_path = output_dir / f"{base_name}.csv"
                self.data_exporter.export_to_csv(result, csv_path)
                exported_files['csv'] = csv_path
            
            # Экспорт в JSON
            if 'json' in formats:
                json_path = output_dir / f"{base_name}.json"
                self.data_exporter.export_to_json(result, json_path)
                exported_files['json'] = json_path
            
            # Экспорт в Excel
            if 'excel' in formats:
                excel_path = output_dir / f"{base_name}.xlsx"
                self.data_exporter.export_to_excel(result, excel_path)
                exported_files['excel'] = excel_path
            
            # Экспорт краткого отчета
            if 'txt' in formats:
                txt_path = output_dir / f"{base_name}_report.txt"
                self.data_exporter.export_summary_report(result, txt_path)
                exported_files['txt'] = txt_path
            
            # Экспорт только импортов
            if 'imports_csv' in formats:
                imports_csv_path = output_dir / f"{base_name}_imports.csv"
                self.data_exporter.export_imports_only_csv(result, imports_csv_path)
                exported_files['imports_csv'] = imports_csv_path
                
        except Exception as e:
            raise RuntimeError(f"Ошибка при экспорте: {e}")
        
        return exported_files
    
    def get_scan_statistics(self, result: ScanResult) -> dict:
        """
        Возвращает статистику сканирования
        
        Args:
            result: Результат сканирования
            
        Returns:
            Словарь со статистикой
        """
        if not result:
            return {}
        
        # Статистика импортов
        imports_stats = self.import_parser.get_import_statistics(
            [lib for lib, data in result.imports_data.items() 
             for _ in range(data.count)]
        )
        
        # Статистика проектов
        projects_stats = self.project_analyzer.get_project_statistics(
            result.projects_data
        )
        
        return {
            'scan_info': {
                'duration': result.scan_duration,
                'files_scanned': result.total_files_scanned,
                'timestamp': result.scan_timestamp.isoformat()
            },
            'imports': imports_stats,
            'projects': projects_stats,
            'performance': {
                'files_per_second': result.total_files_scanned / result.scan_duration if result.scan_duration > 0 else 0,
                'imports_per_file': result.total_imports / result.total_files_scanned if result.total_files_scanned > 0 else 0
            }
        }
    
    def validate_directory(self, directory: Path) -> tuple[bool, str]:
        """
        Проверяет валидность директории для сканирования
        
        Args:
            directory: Директория для проверки
            
        Returns:
            Кортеж (валидна, сообщение об ошибке)
        """
        if not directory.exists():
            return False, f"Директория не существует: {directory}"
        
        if not directory.is_dir():
            return False, f"Путь не является директорией: {directory}"
        
        # Проверка на наличие Python файлов
        python_files = list(directory.rglob("*.py"))
        if not python_files:
            return False, "В директории не найдено Python файлов"
        
        return True, f"Найдено {len(python_files)} Python файлов"
    
    def get_configuration(self) -> Configuration:
        """
        Возвращает текущую конфигурацию
        
        Returns:
            Объект конфигурации
        """
        return self.config
    
    def update_configuration(self, **kwargs) -> None:
        """
        Обновляет конфигурацию
        
        Args:
            **kwargs: Параметры для обновления
        """
        for key, value in kwargs.items():
            self.config.update_config(key, value)
    
    def reset_configuration(self) -> None:
        """Сбрасывает конфигурацию к значениям по умолчанию"""
        self.config.reset_to_defaults()
