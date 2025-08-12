"""
Модуль паттернов проектирования - Factory, Strategy, Observer
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Protocol
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from .logging_config import get_logger


# ============================================================================
# FACTORY PATTERN - Фабрика для создания компонентов
# ============================================================================

class ComponentType(Enum):
    """Типы компонентов для фабрики"""
    IMPORT_PARSER = "import_parser"
    FILE_SCANNER = "file_scanner"
    PROJECT_ANALYZER = "project_analyzer"
    DATA_EXPORTER = "data_exporter"
    SECURITY_MANAGER = "security_manager"
    PERFORMANCE_MANAGER = "performance_manager"
    LOGGER = "logger"


class ComponentFactory:
    """Фабрика для создания компонентов системы"""
    
    def __init__(self, config: Any) -> None:
        self.config = config
        self.logger = get_logger("ComponentFactory")
        self._components: Dict[ComponentType, Any] = {}
        self._lock = threading.RLock()
    
    def create_component(self, component_type: ComponentType, **kwargs: Any) -> Any:
        """
        Создает компонент указанного типа
        
        Args:
            component_type: Тип компонента
            **kwargs: Дополнительные параметры
            
        Returns:
            Созданный компонент
        """
        with self._lock:
            if component_type in self._components:
                return self._components[component_type]
            
            component = self._create_component_instance(component_type, **kwargs)
            self._components[component_type] = component
            
            self.logger.info(f"Создан компонент: {component_type.value}")
            return component
    
    def _create_component_instance(self, component_type: ComponentType, **kwargs: Any) -> Any:
        """Создает экземпляр компонента"""
        if component_type == ComponentType.IMPORT_PARSER:
            from .import_parser import ImportParser
            return ImportParser(self.config)
        
        elif component_type == ComponentType.FILE_SCANNER:
            from .file_scanner import FileScanner
            import_parser = self.create_component(ComponentType.IMPORT_PARSER)
            project_analyzer = self.create_component(ComponentType.PROJECT_ANALYZER)
            return FileScanner(self.config, import_parser, project_analyzer)
        
        elif component_type == ComponentType.PROJECT_ANALYZER:
            from .project_analyzer import ProjectAnalyzer
            return ProjectAnalyzer(self.config)
        
        elif component_type == ComponentType.DATA_EXPORTER:
            from .data_exporter import DataExporter
            return DataExporter()
        
        elif component_type == ComponentType.SECURITY_MANAGER:
            from .security import SecurityManager, SecurityConfig
            security_config_dict = self.config.get_security_config()
            security_config = SecurityConfig(**security_config_dict)
            return SecurityManager(security_config)
        
        elif component_type == ComponentType.PERFORMANCE_MANAGER:
            from .performance import PerformanceManager, PerformanceConfig
            performance_config_dict = self.config.get_performance_config()
            performance_config = PerformanceConfig(**performance_config_dict)
            return PerformanceManager(performance_config)
        
        elif component_type == ComponentType.LOGGER:
            from .logging_config import get_logger
            return get_logger(kwargs.get('name', 'Component'))
        
        else:
            raise ValueError(f"Неизвестный тип компонента: {component_type}")
    
    def get_component(self, component_type: ComponentType) -> Optional[Any]:
        """Получает существующий компонент"""
        with self._lock:
            return self._components.get(component_type)
    
    def clear_cache(self) -> None:
        """Очищает кэш компонентов"""
        with self._lock:
            self._components.clear()
            self.logger.info("Кэш компонентов очищен")


# ============================================================================
# STRATEGY PATTERN - Стратегии для различных алгоритмов
# ============================================================================

class ScanningStrategy(Protocol):
    """Протокол для стратегий сканирования"""
    
    def scan_directory(self, directory: Path, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Сканирует директорию"""
        ...


class SequentialScanningStrategy:
    """Стратегия последовательного сканирования"""
    
    def __init__(self, file_scanner: Any, import_parser: Any, project_analyzer: Any) -> None:
        self.file_scanner = file_scanner
        self.import_parser = import_parser
        self.project_analyzer = project_analyzer
        self.logger = get_logger("SequentialScanningStrategy")
    
    def scan_directory(self, directory: Path, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Последовательное сканирование директории"""
        self.logger.info("Запуск последовательного сканирования")
        
        # Поиск файлов
        if progress_callback:
            progress_callback("Поиск Python файлов...")
        
        file_paths = self._find_python_files(directory)
        
        # Последовательное сканирование
        all_imports = []
        for i, file_path in enumerate(file_paths):
            imports = self.file_scanner.scan_file(file_path)
            all_imports.extend(imports)
            
            if progress_callback and i % 10 == 0:
                progress_callback(f"Обработано {i + 1}/{len(file_paths)} файлов...")
        
        # Анализ проектов
        projects_data = self.project_analyzer.analyze_project_structure(directory)
        
        return {
            'imports': all_imports,
            'projects': projects_data,
            'total_files': len(file_paths)
        }
    
    def _find_python_files(self, directory: Path) -> List[Path]:
        """Находит Python файлы в директории"""
        file_paths = []
        for root, dirs, files in directory.rglob("*.py"):
            file_paths.append(root / files)
        return file_paths


class ParallelScanningStrategy:
    """Стратегия параллельного сканирования"""
    
    def __init__(self, file_scanner: Any, import_parser: Any, project_analyzer: Any) -> None:
        self.file_scanner = file_scanner
        self.import_parser = import_parser
        self.project_analyzer = project_analyzer
        self.logger = get_logger("ParallelScanningStrategy")
    
    def scan_directory(self, directory: Path, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Параллельное сканирование директории"""
        self.logger.info("Запуск параллельного сканирования")
        
        # Используем существующую логику параллельного сканирования
        result = self.file_scanner.scan_directory(directory, progress_callback)
        
        return {
            'imports': result.imports_data,
            'projects': result.projects_data,
            'total_files': result.total_files_scanned
        }


class AdaptiveScanningStrategy:
    """Адаптивная стратегия сканирования"""
    
    def __init__(self, file_scanner: Any, import_parser: Any, project_analyzer: Any) -> None:
        self.file_scanner = file_scanner
        self.import_parser = import_parser
        self.project_analyzer = project_analyzer
        self.logger = get_logger("AdaptiveScanningStrategy")
    
    def scan_directory(self, directory: Path, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Адаптивное сканирование директории"""
        self.logger.info("Запуск адаптивного сканирования")
        
        # Определяем количество файлов
        file_count = len(list(directory.rglob("*.py")))
        
        # Выбираем стратегию на основе количества файлов
        if file_count < 100:
            strategy = SequentialScanningStrategy(self.file_scanner, self.import_parser, self.project_analyzer)
            self.logger.info("Выбрана последовательная стратегия")
        else:
            strategy = ParallelScanningStrategy(self.file_scanner, self.import_parser, self.project_analyzer)
            self.logger.info("Выбрана параллельная стратегия")
        
        return strategy.scan_directory(directory, progress_callback)


class ScanningStrategyFactory:
    """Фабрика стратегий сканирования"""
    
    @staticmethod
    def create_strategy(strategy_type: str, file_scanner: Any, import_parser: Any, project_analyzer: Any) -> ScanningStrategy:
        """Создает стратегию сканирования"""
        if strategy_type == "sequential":
            return SequentialScanningStrategy(file_scanner, import_parser, project_analyzer)
        elif strategy_type == "parallel":
            return ParallelScanningStrategy(file_scanner, import_parser, project_analyzer)
        elif strategy_type == "adaptive":
            return AdaptiveScanningStrategy(file_scanner, import_parser, project_analyzer)
        else:
            raise ValueError(f"Неизвестный тип стратегии: {strategy_type}")


# ============================================================================
# OBSERVER PATTERN - Наблюдатели для событий
# ============================================================================

@dataclass
class ScanEvent:
    """Событие сканирования"""
    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class ScanObserver(ABC):
    """Абстрактный наблюдатель событий сканирования"""
    
    @abstractmethod
    def update(self, event: ScanEvent) -> None:
        """Обновляется при получении события"""
        pass


class ProgressObserver(ScanObserver):
    """Наблюдатель для отображения прогресса"""
    
    def __init__(self, progress_callback: Optional[Callable] = None) -> None:
        self.progress_callback = progress_callback
        self.logger = get_logger("ProgressObserver")
    
    def update(self, event: ScanEvent) -> None:
        """Обновляет прогресс"""
        if self.progress_callback:
            if event.event_type == "file_processed":
                self.progress_callback(f"Обработан файл: {event.data.get('file', 'Unknown')}")
            elif event.event_type == "scan_completed":
                self.progress_callback(f"Сканирование завершено: {event.data.get('total_files', 0)} файлов")
            elif event.event_type == "error":
                self.progress_callback(f"Ошибка: {event.data.get('error', 'Unknown error')}")


class LoggingObserver(ScanObserver):
    """Наблюдатель для логирования событий"""
    
    def __init__(self) -> None:
        self.logger = get_logger("LoggingObserver")
    
    def update(self, event: ScanEvent) -> None:
        """Логирует событие"""
        if event.event_type == "file_processed":
            self.logger.debug("Файл обработан", extra_data=event.data)
        elif event.event_type == "scan_completed":
            self.logger.info("Сканирование завершено", extra_data=event.data)
        elif event.event_type == "error":
            self.logger.error("Ошибка сканирования", extra_data=event.data)


class MetricsObserver(ScanObserver):
    """Наблюдатель для сбора метрик"""
    
    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {
            'files_processed': 0,
            'total_imports': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        self.logger = get_logger("MetricsObserver")
    
    def update(self, event: ScanEvent) -> None:
        """Обновляет метрики"""
        if event.event_type == "scan_started":
            self.metrics['start_time'] = event.timestamp
        elif event.event_type == "file_processed":
            self.metrics['files_processed'] += 1
            self.metrics['total_imports'] += event.data.get('imports_count', 0)
        elif event.event_type == "scan_completed":
            self.metrics['end_time'] = event.timestamp
        elif event.event_type == "error":
            self.metrics['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает собранные метрики"""
        metrics = self.metrics.copy()
        if metrics['start_time'] and metrics['end_time']:
            metrics['duration'] = metrics['end_time'] - metrics['start_time']
        return metrics


class ScanSubject:
    """Субъект для управления наблюдателями"""
    
    def __init__(self) -> None:
        self.observers: List[ScanObserver] = []
        self.logger = get_logger("ScanSubject")
    
    def attach(self, observer: ScanObserver) -> None:
        """Добавляет наблюдателя"""
        self.observers.append(observer)
        self.logger.debug(f"Добавлен наблюдатель: {type(observer).__name__}")
    
    def detach(self, observer: ScanObserver) -> None:
        """Удаляет наблюдателя"""
        if observer in self.observers:
            self.observers.remove(observer)
            self.logger.debug(f"Удален наблюдатель: {type(observer).__name__}")
    
    def notify(self, event: ScanEvent) -> None:
        """Уведомляет всех наблюдателей"""
        for observer in self.observers:
            try:
                observer.update(event)
            except Exception as e:
                self.logger.error(f"Ошибка в наблюдателе {type(observer).__name__}: {e}")
    
    def notify_all(self, event_type: str, data: Dict[str, Any]) -> None:
        """Уведомляет всех наблюдателей с созданием события"""
        event = ScanEvent(event_type, data)
        self.notify(event)


# ============================================================================
# COMPOSITE PATTERN - Композитный паттерн для сканирования
# ============================================================================

class ScanComponent(ABC):
    """Абстрактный компонент сканирования"""
    
    @abstractmethod
    def scan(self, path: Path) -> Dict[str, Any]:
        """Выполняет сканирование"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя компонента"""
        pass


class FileScanComponent(ScanComponent):
    """Компонент для сканирования файла"""
    
    def __init__(self, file_scanner: Any) -> None:
        self.file_scanner = file_scanner
    
    def scan(self, path: Path) -> Dict[str, Any]:
        """Сканирует файл"""
        imports = self.file_scanner.scan_file(path)
        return {
            'type': 'file',
            'path': str(path),
            'imports': imports,
            'imports_count': len(imports)
        }
    
    def get_name(self) -> str:
        return "FileScanner"


class DirectoryScanComponent(ScanComponent):
    """Компонент для сканирования директории"""
    
    def __init__(self, components: List[ScanComponent]) -> None:
        self.components = components
    
    def scan(self, path: Path) -> Dict[str, Any]:
        """Сканирует директорию"""
        results = []
        for component in self.components:
            try:
                result = component.scan(path)
                results.append(result)
            except Exception as e:
                results.append({
                    'type': 'error',
                    'component': component.get_name(),
                    'error': str(e)
                })
        
        return {
            'type': 'directory',
            'path': str(path),
            'components': results
        }
    
    def get_name(self) -> str:
        return "DirectoryScanner"
    
    def add_component(self, component: ScanComponent) -> None:
        """Добавляет компонент"""
        self.components.append(component)
    
    def remove_component(self, component: ScanComponent) -> None:
        """Удаляет компонент"""
        if component in self.components:
            self.components.remove(component)


# ============================================================================
# BUILDER PATTERN - Строитель для конфигурации сканирования
# ============================================================================

@dataclass
class ScanConfiguration:
    """Конфигурация сканирования"""
    strategy_type: str = "adaptive"
    enable_parallel: bool = True
    max_workers: int = 4
    progress_callback: Optional[Callable] = None
    enable_logging: bool = True
    enable_metrics: bool = True
    scan_components: List[str] = field(default_factory=lambda: ["file", "project"])


class ScanConfigurationBuilder:
    """Строитель конфигурации сканирования"""
    
    def __init__(self) -> None:
        self.config = ScanConfiguration()
    
    def with_strategy(self, strategy_type: str) -> 'ScanConfigurationBuilder':
        """Устанавливает тип стратегии"""
        self.config.strategy_type = strategy_type
        return self
    
    def with_parallel(self, enable: bool) -> 'ScanConfigurationBuilder':
        """Включает/выключает параллельное сканирование"""
        self.config.enable_parallel = enable
        return self
    
    def with_max_workers(self, max_workers: int) -> 'ScanConfigurationBuilder':
        """Устанавливает максимальное количество потоков"""
        self.config.max_workers = max_workers
        return self
    
    def with_progress_callback(self, callback: Callable) -> 'ScanConfigurationBuilder':
        """Устанавливает callback для прогресса"""
        self.config.progress_callback = callback
        return self
    
    def with_logging(self, enable: bool) -> 'ScanConfigurationBuilder':
        """Включает/выключает логирование"""
        self.config.enable_logging = enable
        return self
    
    def with_metrics(self, enable: bool) -> 'ScanConfigurationBuilder':
        """Включает/выключает сбор метрик"""
        self.config.enable_metrics = enable
        return self
    
    def with_components(self, components: List[str]) -> 'ScanConfigurationBuilder':
        """Устанавливает компоненты сканирования"""
        self.config.scan_components = components
        return self
    
    def build(self) -> ScanConfiguration:
        """Строит конфигурацию"""
        return self.config
