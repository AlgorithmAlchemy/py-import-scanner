"""
Пример использования паттернов проектирования в Python Import Parser
"""
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scan_service import ScanService
from core.patterns import (
    ComponentFactory, ComponentType, ScanningStrategyFactory,
    ScanSubject, ProgressObserver, LoggingObserver, MetricsObserver,
    ScanConfigurationBuilder
)
from core.logging_config import get_logger


def example_factory_pattern():
    """Пример использования Factory паттерна"""
    print("\n=== Factory Pattern Example ===")
    
    from core.configuration import Configuration
    
    # Создание конфигурации
    config = Configuration()
    
    # Создание фабрики компонентов
    factory = ComponentFactory(config)
    
    # Создание компонентов через фабрику
    import_parser = factory.create_component(ComponentType.IMPORT_PARSER)
    file_scanner = factory.create_component(ComponentType.FILE_SCANNER)
    security_manager = factory.create_component(ComponentType.SECURITY_MANAGER)
    
    print(f"Создан ImportParser: {type(import_parser).__name__}")
    print(f"Создан FileScanner: {type(file_scanner).__name__}")
    print(f"Создан SecurityManager: {type(security_manager).__name__}")
    
    # Получение существующего компонента
    existing_parser = factory.get_component(ComponentType.IMPORT_PARSER)
    print(f"Получен существующий парсер: {existing_parser is import_parser}")


def example_strategy_pattern():
    """Пример использования Strategy паттерна"""
    print("\n=== Strategy Pattern Example ===")
    
    from core.configuration import Configuration
    from core.import_parser import ImportParser
    from core.project_analyzer import ProjectAnalyzer
    from core.file_scanner import FileScanner
    
    # Создание компонентов
    config = Configuration()
    import_parser = ImportParser(config)
    project_analyzer = ProjectAnalyzer(config)
    file_scanner = FileScanner(config, import_parser, project_analyzer)
    
    # Создание различных стратегий
    sequential_strategy = ScanningStrategyFactory.create_strategy(
        "sequential", file_scanner, import_parser, project_analyzer
    )
    parallel_strategy = ScanningStrategyFactory.create_strategy(
        "parallel", file_scanner, import_parser, project_analyzer
    )
    adaptive_strategy = ScanningStrategyFactory.create_strategy(
        "adaptive", file_scanner, import_parser, project_analyzer
    )
    
    print(f"Создана последовательная стратегия: {type(sequential_strategy).__name__}")
    print(f"Создана параллельная стратегия: {type(parallel_strategy).__name__}")
    print(f"Создана адаптивная стратегия: {type(adaptive_strategy).__name__}")
    
    # Тестирование стратегий на небольшой директории
    test_dir = Path(__file__).parent.parent / "src"
    if test_dir.exists():
        print(f"\nТестирование стратегий на директории: {test_dir}")
        
        try:
            # Адаптивная стратегия автоматически выберет лучший подход
            result = adaptive_strategy.scan_directory(test_dir)
            print(f"Результат адаптивной стратегии: {len(result.get('imports', []))} импортов")
        except Exception as e:
            print(f"Ошибка при тестировании: {e}")


def example_observer_pattern():
    """Пример использования Observer паттерна"""
    print("\n=== Observer Pattern Example ===")
    
    # Создание субъекта
    subject = ScanSubject()
    
    # Создание наблюдателей
    progress_observer = ProgressObserver(lambda msg: print(f"Progress: {msg}"))
    logging_observer = LoggingObserver()
    metrics_observer = MetricsObserver()
    
    # Присоединение наблюдателей
    subject.attach(progress_observer)
    subject.attach(logging_observer)
    subject.attach(metrics_observer)
    
    print("Наблюдатели присоединены к субъекту")
    
    # Симуляция событий сканирования
    print("\nСимуляция событий сканирования:")
    
    subject.notify_all("scan_started", {
        "directory": "/test/path",
        "strategy": "adaptive"
    })
    
    subject.notify_all("file_processed", {
        "file": "test.py",
        "imports_count": 5
    })
    
    subject.notify_all("file_processed", {
        "file": "main.py",
        "imports_count": 10
    })
    
    subject.notify_all("scan_completed", {
        "total_files": 2,
        "total_imports": 15,
        "duration": 1.5
    })
    
    # Получение метрик
    metrics = metrics_observer.get_metrics()
    print(f"\nСобранные метрики: {metrics}")


def example_builder_pattern():
    """Пример использования Builder паттерна"""
    print("\n=== Builder Pattern Example ===")
    
    # Создание конфигурации через Builder
    config_builder = ScanConfigurationBuilder()
    
    config = (config_builder
              .with_strategy("parallel")
              .with_parallel(True)
              .with_max_workers(8)
              .with_progress_callback(lambda msg: print(f"Builder Progress: {msg}"))
              .with_logging(True)
              .with_metrics(True)
              .with_components(["file", "project", "security"])
              .build())
    
    print("Конфигурация создана через Builder:")
    print(f"  Стратегия: {config.strategy_type}")
    print(f"  Параллельное сканирование: {config.enable_parallel}")
    print(f"  Максимум потоков: {config.max_workers}")
    print(f"  Логирование: {config.enable_logging}")
    print(f"  Метрики: {config.enable_metrics}")
    print(f"  Компоненты: {config.scan_components}")


def example_scan_service_with_patterns():
    """Пример использования ScanService с паттернами"""
    print("\n=== ScanService with Patterns Example ===")
    
    # Создание сервиса
    scan_service = ScanService()
    
    # Получение фабрики компонентов
    factory = scan_service.get_component_factory()
    print(f"Фабрика компонентов: {type(factory).__name__}")
    
    # Получение субъекта наблюдателей
    subject = scan_service.get_scan_subject()
    print(f"Субъект наблюдателей: {type(subject).__name__}")
    
    # Добавление кастомного наблюдателя
    custom_observer = ProgressObserver(lambda msg: print(f"Custom: {msg}"))
    subject.attach(custom_observer)
    
    # Тестирование сканирования с разными стратегиями
    test_dir = Path(__file__).parent.parent / "src"
    if test_dir.exists():
        print(f"\nТестирование сканирования с паттернами на: {test_dir}")
        
        try:
            # Сканирование с адаптивной стратегией
            result = scan_service.scan_directory(
                test_dir, 
                progress_callback=lambda msg: print(f"Scan: {msg}"),
                strategy_type="adaptive"
            )
            
            print(f"Результат сканирования:")
            print(f"  Файлов обработано: {result.total_files_scanned}")
            print(f"  Импортов найдено: {result.total_imports}")
            print(f"  Проектов обнаружено: {len(result.projects_data)}")
            
        except Exception as e:
            print(f"Ошибка при сканировании: {e}")
    
    # Пример использования Builder для конфигурации
    print("\nТестирование Builder конфигурации:")
    
    config_builder = (ScanConfigurationBuilder()
                     .with_strategy("sequential")
                     .with_parallel(False)
                     .with_progress_callback(lambda msg: print(f"Builder Scan: {msg}")))
    
    try:
        result = scan_service.scan_with_configuration(test_dir, config_builder)
        print(f"Результат с Builder конфигурацией: {result.total_files_scanned} файлов")
    except Exception as e:
        print(f"Ошибка при сканировании с Builder: {e}")


def example_composite_pattern():
    """Пример использования Composite паттерна"""
    print("\n=== Composite Pattern Example ===")
    
    from core.patterns import FileScanComponent, DirectoryScanComponent
    from core.configuration import Configuration
    from core.file_scanner import FileScanner
    from core.import_parser import ImportParser
    from core.project_analyzer import ProjectAnalyzer
    
    # Создание компонентов
    config = Configuration()
    import_parser = ImportParser(config)
    project_analyzer = ProjectAnalyzer(config)
    file_scanner = FileScanner(config, import_parser, project_analyzer)
    
    # Создание компонента сканирования файла
    file_component = FileScanComponent(file_scanner)
    
    # Создание композитного компонента для директории
    directory_component = DirectoryScanComponent([file_component])
    
    print(f"Создан компонент файла: {file_component.get_name()}")
    print(f"Создан компонент директории: {directory_component.get_name()}")
    
    # Тестирование на реальном файле
    test_file = Path(__file__)
    if test_file.exists():
        try:
            result = file_component.scan(test_file)
            print(f"Результат сканирования файла: {result}")
        except Exception as e:
            print(f"Ошибка при сканировании файла: {e}")


def main():
    """Главная функция с примерами всех паттернов"""
    print("🚀 Примеры использования паттернов проектирования")
    print("=" * 60)
    
    try:
        # Примеры паттернов
        example_factory_pattern()
        example_strategy_pattern()
        example_observer_pattern()
        example_builder_pattern()
        example_scan_service_with_patterns()
        example_composite_pattern()
        
        print("\n✅ Все примеры паттернов выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
