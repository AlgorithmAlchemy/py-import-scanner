"""
Тесты для паттернов проектирования
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

# Добавляем src в путь для импортов
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.patterns import (
    ComponentFactory, ComponentType, ScanningStrategyFactory,
    ScanSubject, ProgressObserver, LoggingObserver, MetricsObserver,
    ScanConfigurationBuilder, ScanConfiguration,
    SequentialScanningStrategy, ParallelScanningStrategy, AdaptiveScanningStrategy,
    FileScanComponent, DirectoryScanComponent
)
from core.configuration import Configuration


class TestFactoryPattern(unittest.TestCase):
    """Тесты для Factory паттерна"""
    
    def setUp(self):
        """Настройка тестов"""
        self.config = Configuration()
        self.factory = ComponentFactory(self.config)
    
    def test_create_import_parser(self):
        """Тест создания ImportParser через фабрику"""
        parser = self.factory.create_component(ComponentType.IMPORT_PARSER)
        self.assertIsNotNone(parser)
        self.assertEqual(parser.__class__.__name__, "ImportParser")
    
    def test_create_file_scanner(self):
        """Тест создания FileScanner через фабрику"""
        scanner = self.factory.create_component(ComponentType.FILE_SCANNER)
        self.assertIsNotNone(scanner)
        self.assertEqual(scanner.__class__.__name__, "FileScanner")
    
    def test_create_security_manager(self):
        """Тест создания SecurityManager через фабрику"""
        manager = self.factory.create_component(ComponentType.SECURITY_MANAGER)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.__class__.__name__, "SecurityManager")
    
    def test_get_existing_component(self):
        """Тест получения существующего компонента"""
        parser1 = self.factory.create_component(ComponentType.IMPORT_PARSER)
        parser2 = self.factory.get_component(ComponentType.IMPORT_PARSER)
        self.assertIs(parser1, parser2)
    
    def test_clear_cache(self):
        """Тест очистки кэша компонентов"""
        self.factory.create_component(ComponentType.IMPORT_PARSER)
        self.assertIsNotNone(self.factory.get_component(ComponentType.IMPORT_PARSER))
        
        self.factory.clear_cache()
        self.assertIsNone(self.factory.get_component(ComponentType.IMPORT_PARSER))
    
    def test_invalid_component_type(self):
        """Тест обработки неверного типа компонента"""
        with self.assertRaises(ValueError):
            self.factory.create_component("invalid_type")


class TestStrategyPattern(unittest.TestCase):
    """Тесты для Strategy паттерна"""
    
    def setUp(self):
        """Настройка тестов"""
        self.config = Configuration()
        self.mock_file_scanner = Mock()
        self.mock_import_parser = Mock()
        self.mock_project_analyzer = Mock()
    
    def test_create_sequential_strategy(self):
        """Тест создания последовательной стратегии"""
        strategy = ScanningStrategyFactory.create_strategy(
            "sequential", self.mock_file_scanner, 
            self.mock_import_parser, self.mock_project_analyzer
        )
        self.assertIsInstance(strategy, SequentialScanningStrategy)
    
    def test_create_parallel_strategy(self):
        """Тест создания параллельной стратегии"""
        strategy = ScanningStrategyFactory.create_strategy(
            "parallel", self.mock_file_scanner, 
            self.mock_import_parser, self.mock_project_analyzer
        )
        self.assertIsInstance(strategy, ParallelScanningStrategy)
    
    def test_create_adaptive_strategy(self):
        """Тест создания адаптивной стратегии"""
        strategy = ScanningStrategyFactory.create_strategy(
            "adaptive", self.mock_file_scanner, 
            self.mock_import_parser, self.mock_project_analyzer
        )
        self.assertIsInstance(strategy, AdaptiveScanningStrategy)
    
    def test_invalid_strategy_type(self):
        """Тест обработки неверного типа стратегии"""
        with self.assertRaises(ValueError):
            ScanningStrategyFactory.create_strategy(
                "invalid", self.mock_file_scanner, 
                self.mock_import_parser, self.mock_project_analyzer
            )
    
    def test_sequential_strategy_scan(self):
        """Тест работы последовательной стратегии"""
        strategy = SequentialScanningStrategy(
            self.mock_file_scanner, self.mock_import_parser, self.mock_project_analyzer
        )
        
        # Мокаем методы
        self.mock_file_scanner.scan_file.return_value = ["os", "sys"]
        self.mock_project_analyzer.analyze_project_structure.return_value = []
        
        # Создаем временную директорию с тестовыми файлами
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создаем тестовый Python файл
            test_file = temp_path / "test.py"
            test_file.write_text("import os\nimport sys")
            
            result = strategy.scan_directory(temp_path)
            
            self.assertIn('imports', result)
            self.assertIn('projects', result)
            self.assertIn('total_files', result)
    
    def test_adaptive_strategy_selection(self):
        """Тест выбора стратегии в адаптивной стратегии"""
        strategy = AdaptiveScanningStrategy(
            self.mock_file_scanner, self.mock_import_parser, self.mock_project_analyzer
        )
        
        # Мокаем методы
        self.mock_file_scanner.scan_directory.return_value = Mock(
            imports_data={}, projects_data=[], total_files_scanned=0
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создаем много файлов для тестирования параллельной стратегии
            for i in range(150):
                test_file = temp_path / f"test_{i}.py"
                test_file.write_text("import os")
            
            result = strategy.scan_directory(temp_path)
            self.assertIsNotNone(result)


class TestObserverPattern(unittest.TestCase):
    """Тесты для Observer паттерна"""
    
    def setUp(self):
        """Настройка тестов"""
        self.subject = ScanSubject()
        self.progress_observer = ProgressObserver(lambda msg: None)
        self.logging_observer = LoggingObserver()
        self.metrics_observer = MetricsObserver()
    
    def test_attach_observer(self):
        """Тест присоединения наблюдателя"""
        initial_count = len(self.subject.observers)
        self.subject.attach(self.progress_observer)
        self.assertEqual(len(self.subject.observers), initial_count + 1)
    
    def test_detach_observer(self):
        """Тест отключения наблюдателя"""
        self.subject.attach(self.progress_observer)
        initial_count = len(self.subject.observers)
        
        self.subject.detach(self.progress_observer)
        self.assertEqual(len(self.subject.observers), initial_count - 1)
    
    def test_notify_observers(self):
        """Тест уведомления наблюдателей"""
        mock_observer = Mock()
        self.subject.attach(mock_observer)
        
        self.subject.notify_all("test_event", {"data": "test"})
        mock_observer.update.assert_called_once()
    
    def test_progress_observer(self):
        """Тест наблюдателя прогресса"""
        progress_messages = []
        
        def progress_callback(msg):
            progress_messages.append(msg)
        
        observer = ProgressObserver(progress_callback)
        
        # Симулируем события
        from core.patterns import ScanEvent
        event = ScanEvent("file_processed", {"file": "test.py"})
        observer.update(event)
        
        self.assertIn("test.py", progress_messages[0])
    
    def test_metrics_observer(self):
        """Тест наблюдателя метрик"""
        observer = MetricsObserver()
        
        # Симулируем события
        from core.patterns import ScanEvent
        import time
        
        start_event = ScanEvent("scan_started", {})
        observer.update(start_event)
        
        file_event = ScanEvent("file_processed", {"imports_count": 5})
        observer.update(file_event)
        
        complete_event = ScanEvent("scan_completed", {})
        observer.update(complete_event)
        
        metrics = observer.get_metrics()
        self.assertEqual(metrics['files_processed'], 1)
        self.assertEqual(metrics['total_imports'], 5)
        self.assertIsNotNone(metrics['start_time'])
        self.assertIsNotNone(metrics['end_time'])


class TestBuilderPattern(unittest.TestCase):
    """Тесты для Builder паттерна"""
    
    def test_basic_builder(self):
        """Тест базового использования Builder"""
        config = (ScanConfigurationBuilder()
                 .with_strategy("parallel")
                 .with_parallel(True)
                 .with_max_workers(8)
                 .build())
        
        self.assertEqual(config.strategy_type, "parallel")
        self.assertTrue(config.enable_parallel)
        self.assertEqual(config.max_workers, 8)
    
    def test_fluent_interface(self):
        """Тест fluent interface Builder"""
        config = (ScanConfigurationBuilder()
                 .with_strategy("sequential")
                 .with_parallel(False)
                 .with_max_workers(4)
                 .with_logging(True)
                 .with_metrics(True)
                 .with_components(["file", "project"])
                 .build())
        
        self.assertEqual(config.strategy_type, "sequential")
        self.assertFalse(config.enable_parallel)
        self.assertEqual(config.max_workers, 4)
        self.assertTrue(config.enable_logging)
        self.assertTrue(config.enable_metrics)
        self.assertEqual(config.scan_components, ["file", "project"])
    
    def test_default_values(self):
        """Тест значений по умолчанию"""
        config = ScanConfigurationBuilder().build()
        
        self.assertEqual(config.strategy_type, "adaptive")
        self.assertTrue(config.enable_parallel)
        self.assertEqual(config.max_workers, 4)
        self.assertTrue(config.enable_logging)
        self.assertTrue(config.enable_metrics)


class TestCompositePattern(unittest.TestCase):
    """Тесты для Composite паттерна"""
    
    def setUp(self):
        """Настройка тестов"""
        self.mock_file_scanner = Mock()
        self.mock_file_scanner.scan_file.return_value = ["os", "sys"]
    
    def test_file_scan_component(self):
        """Тест компонента сканирования файла"""
        component = FileScanComponent(self.mock_file_scanner)
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
            temp_file.write(b"import os\nimport sys")
            temp_file_path = Path(temp_file.name)
        
        try:
            result = component.scan(temp_file_path)
            
            self.assertEqual(result['type'], 'file')
            self.assertEqual(result['path'], str(temp_file_path))
            self.assertEqual(result['imports'], ["os", "sys"])
            self.assertEqual(result['imports_count'], 2)
        finally:
            temp_file_path.unlink()
    
    def test_directory_scan_component(self):
        """Тест компонента сканирования директории"""
        file_component = FileScanComponent(self.mock_file_scanner)
        directory_component = DirectoryScanComponent([file_component])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создаем тестовый файл
            test_file = temp_path / "test.py"
            test_file.write_text("import os")
            
            result = directory_component.scan(temp_path)
            
            self.assertEqual(result['type'], 'directory')
            self.assertEqual(result['path'], str(temp_path))
            self.assertIn('components', result)
    
    def test_add_remove_component(self):
        """Тест добавления и удаления компонентов"""
        file_component = FileScanComponent(self.mock_file_scanner)
        directory_component = DirectoryScanComponent([])
        
        # Добавление компонента
        directory_component.add_component(file_component)
        self.assertEqual(len(directory_component.components), 1)
        
        # Удаление компонента
        directory_component.remove_component(file_component)
        self.assertEqual(len(directory_component.components), 0)


class TestPatternsIntegration(unittest.TestCase):
    """Интеграционные тесты паттернов"""
    
    def test_factory_with_strategy(self):
        """Тест интеграции Factory и Strategy паттернов"""
        config = Configuration()
        factory = ComponentFactory(config)
        
        # Создание компонентов через фабрику
        file_scanner = factory.create_component(ComponentType.FILE_SCANNER)
        import_parser = factory.create_component(ComponentType.IMPORT_PARSER)
        project_analyzer = factory.create_component(ComponentType.PROJECT_ANALYZER)
        
        # Создание стратегии
        strategy = ScanningStrategyFactory.create_strategy(
            "sequential", file_scanner, import_parser, project_analyzer
        )
        
        self.assertIsInstance(strategy, SequentialScanningStrategy)
    
    def test_observer_with_subject(self):
        """Тест интеграции Observer паттерна"""
        subject = ScanSubject()
        
        # Создание наблюдателей
        progress_messages = []
        progress_observer = ProgressObserver(lambda msg: progress_messages.append(msg))
        metrics_observer = MetricsObserver()
        
        # Присоединение наблюдателей
        subject.attach(progress_observer)
        subject.attach(metrics_observer)
        
        # Уведомление о событиях
        subject.notify_all("scan_started", {"directory": "/test"})
        subject.notify_all("file_processed", {"file": "test.py", "imports_count": 3})
        subject.notify_all("scan_completed", {"total_files": 1})
        
        # Проверка результатов
        self.assertGreater(len(progress_messages), 0)
        metrics = metrics_observer.get_metrics()
        self.assertEqual(metrics['files_processed'], 1)
        self.assertEqual(metrics['total_imports'], 3)


if __name__ == '__main__':
    unittest.main()
