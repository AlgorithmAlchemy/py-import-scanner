"""
Упрощенный пример использования паттернов проектирования
"""
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Импортируем только базовые паттерны без внешних зависимостей
from core.patterns import (
    ComponentFactory, ComponentType, ScanningStrategyFactory,
    ScanSubject, ProgressObserver, LoggingObserver, MetricsObserver,
    ScanConfigurationBuilder, ScanConfiguration
)


def example_factory_pattern():
    """Пример использования Factory паттерна"""
    print("\n=== Factory Pattern Example ===")
    
    try:
        from core.configuration import Configuration
        
        # Создание конфигурации
        config = Configuration()
        
        # Создание фабрики компонентов
        factory = ComponentFactory(config)
        
        # Создание компонентов через фабрику
        import_parser = factory.create_component(ComponentType.IMPORT_PARSER)
        file_scanner = factory.create_component(ComponentType.FILE_SCANNER)
        security_manager = factory.create_component(ComponentType.SECURITY_MANAGER)
        
        print(f"✅ Создан ImportParser: {type(import_parser).__name__}")
        print(f"✅ Создан FileScanner: {type(file_scanner).__name__}")
        print(f"✅ Создан SecurityManager: {type(security_manager).__name__}")
        
        # Получение существующего компонента
        existing_parser = factory.get_component(ComponentType.IMPORT_PARSER)
        print(f"✅ Получен существующий парсер: {existing_parser is import_parser}")
        
    except Exception as e:
        print(f"❌ Ошибка в Factory Pattern: {e}")


def example_strategy_pattern():
    """Пример использования Strategy паттерна"""
    print("\n=== Strategy Pattern Example ===")
    
    try:
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
        
        print(f"✅ Создана последовательная стратегия: {type(sequential_strategy).__name__}")
        print(f"✅ Создана параллельная стратегия: {type(parallel_strategy).__name__}")
        print(f"✅ Создана адаптивная стратегия: {type(adaptive_strategy).__name__}")
        
    except Exception as e:
        print(f"❌ Ошибка в Strategy Pattern: {e}")


def example_observer_pattern():
    """Пример использования Observer паттерна"""
    print("\n=== Observer Pattern Example ===")
    
    try:
        # Создание субъекта
        subject = ScanSubject()
        
        # Создание наблюдателей
        progress_messages = []
        def progress_callback(msg):
            progress_messages.append(msg)
            print(f"Progress: {msg}")
        
        progress_observer = ProgressObserver(progress_callback)
        logging_observer = LoggingObserver()
        metrics_observer = MetricsObserver()
        
        # Присоединение наблюдателей
        subject.attach(progress_observer)
        subject.attach(logging_observer)
        subject.attach(metrics_observer)
        
        print("✅ Наблюдатели присоединены к субъекту")
        
        # Симуляция событий сканирования
        print("\n📡 Симуляция событий сканирования:")
        
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
        print(f"\n📊 Собранные метрики: {metrics}")
        
    except Exception as e:
        print(f"❌ Ошибка в Observer Pattern: {e}")


def example_builder_pattern():
    """Пример использования Builder паттерна"""
    print("\n=== Builder Pattern Example ===")
    
    try:
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
        
        print("✅ Конфигурация создана через Builder:")
        print(f"  📋 Стратегия: {config.strategy_type}")
        print(f"  🔄 Параллельное сканирование: {config.enable_parallel}")
        print(f"  🧵 Максимум потоков: {config.max_workers}")
        print(f"  📝 Логирование: {config.enable_logging}")
        print(f"  📊 Метрики: {config.enable_metrics}")
        print(f"  🧩 Компоненты: {config.scan_components}")
        
    except Exception as e:
        print(f"❌ Ошибка в Builder Pattern: {e}")


def example_composite_pattern():
    """Пример использования Composite паттерна"""
    print("\n=== Composite Pattern Example ===")
    
    try:
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
        
        print(f"✅ Создан компонент файла: {file_component.get_name()}")
        print(f"✅ Создан компонент директории: {directory_component.get_name()}")
        
        # Тестирование на реальном файле
        test_file = Path(__file__)
        if test_file.exists():
            try:
                result = file_component.scan(test_file)
                print(f"✅ Результат сканирования файла: {result['type']} - {result['imports_count']} импортов")
            except Exception as e:
                print(f"⚠️ Ошибка при сканировании файла: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка в Composite Pattern: {e}")


def example_patterns_integration():
    """Пример интеграции паттернов"""
    print("\n=== Patterns Integration Example ===")
    
    try:
        # Создание субъекта наблюдателей
        subject = ScanSubject()
        
        # Создание наблюдателей
        progress_messages = []
        def custom_progress_callback(message):
            progress_messages.append(message)
            print(f"Custom Progress: {message}")
        
        custom_observer = ProgressObserver(custom_progress_callback)
        metrics_observer = MetricsObserver()
        
        # Присоединение наблюдателей
        subject.attach(custom_observer)
        subject.attach(metrics_observer)
        
        print("✅ Наблюдатели настроены")
        
        # Создание конфигурации через Builder
        config_builder = (ScanConfigurationBuilder()
                         .with_strategy("adaptive")
                         .with_parallel(True)
                         .with_max_workers(4)
                         .with_metrics(True))
        
        config = config_builder.build()
        print(f"✅ Конфигурация создана: {config.strategy_type}")
        
        # Симуляция событий
        subject.notify_all("scan_started", {"directory": "/test"})
        subject.notify_all("file_processed", {"file": "test.py", "imports_count": 3})
        subject.notify_all("scan_completed", {"total_files": 1})
        
        # Проверка результатов
        print(f"✅ Получено сообщений прогресса: {len(progress_messages)}")
        metrics = metrics_observer.get_metrics()
        print(f"✅ Метрики: {metrics['files_processed']} файлов, {metrics['total_imports']} импортов")
        
    except Exception as e:
        print(f"❌ Ошибка в интеграции паттернов: {e}")


def main():
    """Главная функция с примерами всех паттернов"""
    print("🚀 Упрощенные примеры использования паттернов проектирования")
    print("=" * 70)
    
    # Примеры паттернов
    example_factory_pattern()
    example_strategy_pattern()
    example_observer_pattern()
    example_builder_pattern()
    example_composite_pattern()
    example_patterns_integration()
    
    print("\n" + "=" * 70)
    print("✅ Все примеры паттернов выполнены!")
    print("\n📚 Паттерны успешно внедрены в проект:")
    print("  🏭 Factory Pattern - централизованное создание компонентов")
    print("  🎯 Strategy Pattern - различные алгоритмы сканирования")
    print("  👁️ Observer Pattern - реакция на события")
    print("  🧩 Composite Pattern - единообразная работа с файлами/директориями")
    print("  🔨 Builder Pattern - пошаговое создание конфигураций")
    
    print("\n🎉 Проект готов к использованию с современной архитектурой!")


if __name__ == "__main__":
    main()
