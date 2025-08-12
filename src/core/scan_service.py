"""
Главный сервис для координации сканирования с паттернами проектирования
"""
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any, Tuple
from .interfaces import ScanResult, IProgressReporter
from .configuration import Configuration
from .import_parser import ImportParser
from .project_analyzer import ProjectAnalyzer
from .file_scanner import FileScanner
from .data_exporter import DataExporter
from .logging_config import setup_logging, get_logger, LogConfig
from .security import SecurityManager, SecurityConfig
from .performance import PerformanceManager, PerformanceConfig
from .patterns import (
    ComponentFactory, ComponentType, ScanningStrategyFactory,
    ScanSubject, ProgressObserver, LoggingObserver, MetricsObserver,
    ScanConfigurationBuilder, ScanConfiguration
)
from .complexity_analyzer import ComplexityAnalyzer, ProjectComplexityReport


class ScanService:
    """Главный сервис для координации сканирования с паттернами"""
    
    def __init__(self, config: Optional[Configuration] = None) -> None:
        """
        Инициализация сервиса с паттернами
        
        Args:
            config: Конфигурация (если None, создается по умолчанию)
        """
        self.config: Configuration = config or Configuration()
        
        # Настройка логирования
        log_config_dict: Dict[str, Any] = self.config.get_logging_config()
        log_config: LogConfig = LogConfig(**log_config_dict)
        setup_logging(log_config)
        self.logger = get_logger("ScanService")
        
        # Инициализация фабрики компонентов
        self.component_factory: ComponentFactory = ComponentFactory(self.config)
        
        # Создание компонентов через фабрику
        self.import_parser: ImportParser = self.component_factory.create_component(
            ComponentType.IMPORT_PARSER
        )
        self.project_analyzer: ProjectAnalyzer = self.component_factory.create_component(
            ComponentType.PROJECT_ANALYZER
        )
        self.file_scanner: FileScanner = self.component_factory.create_component(
            ComponentType.FILE_SCANNER
        )
        self.data_exporter: DataExporter = self.component_factory.create_component(
            ComponentType.DATA_EXPORTER
        )
        
        # Инициализация безопасности и производительности
        self.security_manager: SecurityManager = self.component_factory.create_component(
            ComponentType.SECURITY_MANAGER
        )
        self.performance_manager: PerformanceManager = self.component_factory.create_component(
            ComponentType.PERFORMANCE_MANAGER
        )
        
        # Инициализация анализатора сложности
        self.complexity_analyzer = ComplexityAnalyzer()
        
        # Инициализация субъекта для Observer паттерна
        self.scan_subject: ScanSubject = ScanSubject()
        
        # Состояние
        self.last_scan_result: Optional[ScanResult] = None
        self.is_scanning: bool = False
        self.current_strategy: Optional[Any] = None
        
        self.logger.info("ScanService инициализирован с паттернами", 
                        extra_data={"config_file": str(self.config.config_file)})
    
    def scan_directory(self, directory: Path, 
                      progress_callback: Optional[Callable[[str, Optional[float]], None]] = None,
                      strategy_type: str = "adaptive") -> ScanResult:
        """
        Сканирует директорию с использованием паттернов
        
        Args:
            directory: Директория для сканирования
            progress_callback: Функция обратного вызова для прогресса
            strategy_type: Тип стратегии сканирования
            
        Returns:
            Результат сканирования
        """
        self.logger.info("Начало сканирования директории с паттернами", 
                        extra_data={"directory": str(directory), "strategy": strategy_type})
        
        if self.is_scanning:
            self.logger.warning("Попытка запуска сканирования во время выполнения")
            raise RuntimeError("Сканирование уже выполняется")
        
        try:
            self.is_scanning = True
            
            # Настройка наблюдателей
            self._setup_observers(progress_callback)
            
            # Уведомление о начале сканирования
            self.scan_subject.notify_all("scan_started", {
                "directory": str(directory),
                "strategy": strategy_type
            })
            
            # Валидация безопасности
            is_valid: bool
            message: str
            is_valid, message = self.security_manager.validate_scan_request(directory)
            if not is_valid:
                self.logger.error("Ошибка валидации безопасности", 
                                extra_data={"directory": str(directory), "error": message})
                self.scan_subject.notify_all("error", {"error": message})
                raise ValueError(f"Ошибка валидации безопасности: {message}")
            
            # Запуск профилирования
            self.performance_manager.start_profiling("scan_directory")
            
            # Создание стратегии через фабрику
            self.current_strategy = ScanningStrategyFactory.create_strategy(
                strategy_type, self.file_scanner, self.import_parser, self.project_analyzer
            )
            
            # Выполнение сканирования с использованием стратегии
            self.logger.info("Запуск сканирования с выбранной стратегией")
            scan_result = self.current_strategy.scan_directory(directory, progress_callback)
            
            # Преобразование результата в ScanResult
            result = self._create_scan_result(scan_result, directory)
            
            # Сохранение результата
            self.last_scan_result = result
            
            # Завершение профилирования
            scan_duration: float = self.performance_manager.end_profiling("scan_directory")
            
            # Сохранение данных производительности
            self.performance_manager.save_performance_data()
            
            # Уведомление о завершении сканирования
            self.scan_subject.notify_all("scan_completed", {
                "total_files": result.total_files_scanned,
                "total_imports": result.total_imports,
                "duration": result.scan_duration,
                "strategy": strategy_type
            })
            
            self.logger.info("Сканирование завершено успешно с паттернами", 
                           extra_data={
                               "total_files": result.total_files_scanned,
                               "total_imports": result.total_imports,
                               "duration": result.scan_duration,
                               "scan_duration_profiled": scan_duration,
                               "projects_found": len(result.projects_data),
                               "strategy": strategy_type
                           })
            
            return result
            
        except Exception as e:
            self.logger.error("Ошибка при сканировании", 
                            extra_data={"error": str(e), "directory": str(directory)})
            self.scan_subject.notify_all("error", {"error": str(e)})
            raise
        finally:
            self.is_scanning = False
            self.logger.info("Сканирование завершено")
    
    def scan_with_configuration(self, directory: Path, 
                               config_builder: ScanConfigurationBuilder) -> ScanResult:
        """
        Сканирует директорию с использованием конфигурации Builder паттерна
        
        Args:
            directory: Директория для сканирования
            config_builder: Строитель конфигурации
            
        Returns:
            Результат сканирования
        """
        config: ScanConfiguration = config_builder.build()
        
        self.logger.info("Сканирование с кастомной конфигурацией", 
                        extra_data={"config": config.__dict__})
        
        # Настройка наблюдателей на основе конфигурации
        if config.enable_logging:
            self.scan_subject.attach(LoggingObserver())
        
        if config.enable_metrics:
            metrics_observer = MetricsObserver()
            self.scan_subject.attach(metrics_observer)
        
        if config.progress_callback:
            self.scan_subject.attach(ProgressObserver(config.progress_callback))
        
        # Выполнение сканирования
        result = self.scan_directory(directory, config.progress_callback, config.strategy_type)
        
        # Возврат метрик если они были включены
        if config.enable_metrics:
            metrics = metrics_observer.get_metrics()
            self.logger.info("Метрики сканирования", extra_data=metrics)
        
        return result
    
    def _setup_observers(self, progress_callback: Optional[Callable] = None) -> None:
        """Настраивает наблюдателей"""
        # Очищаем существующих наблюдателей
        self.scan_subject.observers.clear()
        
        # Добавляем наблюдателя логирования
        self.scan_subject.attach(LoggingObserver())
        
        # Добавляем наблюдателя метрик
        self.scan_subject.attach(MetricsObserver())
        
        # Добавляем наблюдателя прогресса если есть callback
        if progress_callback:
            self.scan_subject.attach(ProgressObserver(progress_callback))
    
    def _create_scan_result(self, scan_data: Dict[str, Any], directory: Path) -> ScanResult:
        """Создает ScanResult из данных стратегии"""
        from datetime import datetime
        
        # Преобразование данных в зависимости от стратегии
        if 'imports' in scan_data and isinstance(scan_data['imports'], list):
            # Для последовательной стратегии
            imports_data = self._process_imports_list(scan_data['imports'])
            projects_data = scan_data.get('projects', [])
            total_files = scan_data.get('total_files', 0)
        else:
            # Для параллельной стратегии
            imports_data = scan_data.get('imports', {})
            projects_data = scan_data.get('projects', [])
            total_files = scan_data.get('total_files', 0)
        
        return ScanResult(
            imports_data=imports_data,
            projects_data=projects_data,
            total_files_scanned=total_files,
            total_imports=sum(data.count for data in imports_data.values()),
            scan_duration=0.0,  # Будет обновлено позже
            scan_timestamp=datetime.now()
        )
    
    def _process_imports_list(self, imports_list: List[str]) -> Dict[str, Any]:
        """Обрабатывает список импортов в формат ImportData"""
        from collections import Counter
        from .interfaces import ImportData
        
        if not imports_list:
            return {}
        
        # Подсчет импортов
        counter = Counter(imports_list)
        total_imports = len(imports_list)
        
        # Создание ImportData
        imports_data = {}
        for library, count in counter.items():
            percentage = (count / total_imports * 100) if total_imports > 0 else 0
            imports_data[library] = ImportData(
                library=library,
                count=count,
                percentage=percentage,
                files=[]  # Можно добавить список файлов
            )
        
        return imports_data
    
    def get_last_result(self) -> Optional[ScanResult]:
        """
        Возвращает результат последнего сканирования
        
        Returns:
            Результат сканирования или None
        """
        return self.last_scan_result
    
    def export_results(self, result: ScanResult, 
                      output_dir: Path,
                      formats: Optional[List[str]] = None) -> Dict[str, Path]:
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
        timestamp: str = result.scan_timestamp.strftime('%Y%m%d_%H%M%S')
        base_name: str = f"import_scan_{timestamp}"
        
        exported_files: Dict[str, Path] = {}
        
        try:
            # Экспорт в CSV
            if 'csv' in formats:
                csv_path: Path = output_dir / f"{base_name}.csv"
                self.data_exporter.export_to_csv(result, csv_path)
                exported_files['csv'] = csv_path
            
            # Экспорт в JSON
            if 'json' in formats:
                json_path: Path = output_dir / f"{base_name}.json"
                self.data_exporter.export_to_json(result, json_path)
                exported_files['json'] = json_path
            
            # Экспорт в Excel
            if 'excel' in formats:
                excel_path: Path = output_dir / f"{base_name}.xlsx"
                self.data_exporter.export_to_excel(result, excel_path)
                exported_files['excel'] = excel_path
            
            # Экспорт краткого отчета
            if 'txt' in formats:
                txt_path: Path = output_dir / f"{base_name}_report.txt"
                self.data_exporter.export_summary_report(result, txt_path)
                exported_files['txt'] = txt_path
            
            # Экспорт только импортов
            if 'imports_csv' in formats:
                imports_csv_path: Path = output_dir / f"{base_name}_imports.csv"
                self.data_exporter.export_imports_only_csv(result, imports_csv_path)
                exported_files['imports_csv'] = imports_csv_path
                
        except Exception as e:
            raise RuntimeError(f"Ошибка при экспорте: {e}")
        
        return exported_files
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Возвращает отчет о производительности
        
        Returns:
            Словарь с данными о производительности
        """
        return self.performance_manager.get_performance_report()
    
    def get_scan_statistics(self, result: ScanResult) -> Dict[str, Any]:
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
        imports_stats: Dict[str, Any] = self.import_parser.get_import_statistics(
            [lib for lib, data in result.imports_data.items() 
             for _ in range(data.count)]
        )
        
        # Статистика проектов
        projects_stats: Dict[str, Any] = self.project_analyzer.get_project_statistics(
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
    
    def validate_directory(self, directory: Path) -> Tuple[bool, str]:
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
        python_files: List[Path] = list(directory.rglob("*.py"))
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
    
    def update_configuration(self, **kwargs: Any) -> None:
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
    
    def get_component_factory(self) -> ComponentFactory:
        """
        Возвращает фабрику компонентов
        
        Returns:
            Фабрика компонентов
        """
        return self.component_factory
    
    def get_scan_subject(self) -> ScanSubject:
        """
        Возвращает субъект для управления наблюдателями
        
        Returns:
            Субъект наблюдателей
        """
        return self.scan_subject
    
    def analyze_complexity(self, directory: Path) -> ProjectComplexityReport:
        """
        Анализирует сложность кода в проекте
        
        Args:
            directory: Директория проекта для анализа
            
        Returns:
            Отчет о сложности проекта
        """
        self.logger.info("Начало анализа сложности кода", 
                        extra_data={"directory": str(directory)})
        
        try:
            # Валидация директории
            is_valid: bool
            message: str
            is_valid, message = self.validate_directory(directory)
            if not is_valid:
                raise ValueError(f"Ошибка валидации директории: {message}")
            
            # Анализ сложности
            report = self.complexity_analyzer.analyze_project(directory)
            
            self.logger.info("Анализ сложности завершен", 
                            extra_data={
                                "total_files": report.total_files,
                                "average_complexity": report.average_complexity
                            })
            
            return report
            
        except Exception as e:
            self.logger.error("Ошибка при анализе сложности", 
                            extra_data={"directory": str(directory), "error": str(e)})
            raise
    
    def analyze_file_complexity(self, file_path: Path) -> 'FileComplexityReport':
        """
        Анализирует сложность отдельного файла
        
        Args:
            file_path: Путь к файлу для анализа
            
        Returns:
            Отчет о сложности файла
        """
        self.logger.info("Анализ сложности файла", 
                        extra_data={"file_path": str(file_path)})
        
        try:
            report = self.complexity_analyzer.analyze_file(file_path)
            
            self.logger.info("Анализ сложности файла завершен", 
                            extra_data={
                                "file_path": str(file_path),
                                "grade": report.grade,
                                "complexity": report.metrics.cyclomatic_complexity
                            })
            
            return report
            
        except Exception as e:
            self.logger.error("Ошибка при анализе сложности файла", 
                            extra_data={"file_path": str(file_path), "error": str(e)})
            raise
