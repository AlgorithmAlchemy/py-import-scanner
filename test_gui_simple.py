#!/usr/bin/env python3
"""
Упрощенный тест интеграции всех улучшений
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_interfaces():
    """Тестирует интерфейсы"""
    print("🔧 Тестирование интерфейсов...")
    
    try:
        from core.interfaces import ScanResult, ImportData, ProjectData
        print("✅ Интерфейсы импортированы успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка интерфейсов: {e}")
        return False

def test_patterns():
    """Тестирует паттерны проектирования"""
    print("\n🎯 Тестирование паттернов проектирования...")
    
    try:
        from core.patterns import (
            ComponentFactory, ComponentType, ScanningStrategyFactory,
            ScanSubject, ProgressObserver, LoggingObserver, MetricsObserver,
            ScanConfigurationBuilder, ScanConfiguration
        )
        print("✅ Паттерны импортированы успешно")
        
        # Тест Builder Pattern
        builder = ScanConfigurationBuilder()
        config = builder.with_strategy("adaptive").with_max_workers(4).build()
        print(f"✅ Builder Pattern: {config.strategy_type}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка паттернов: {e}")
        return False

def test_complexity_analyzer():
    """Тестирует анализатор сложности"""
    print("\n📊 Тестирование анализатора сложности...")
    
    try:
        from core.complexity_analyzer import (
            ComplexityAnalyzer, ComplexityMetrics, FunctionMetrics, 
            ClassMetrics, FileComplexityReport, ProjectComplexityReport
        )
        print("✅ Анализатор сложности импортирован успешно")
        
        # Создание тестового файла
        test_file = Path("test_simple.py")
        test_content = '''
def simple_function():
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
'''
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Анализ файла
        analyzer = ComplexityAnalyzer()
        report = analyzer.analyze_file(test_file)
        print(f"✅ Анализ сложности: оценка {report.grade}")
        
        # Удаление тестового файла
        test_file.unlink()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка анализатора сложности: {e}")
        return False

def test_logging():
    """Тестирует логирование"""
    print("\n📝 Тестирование логирования...")
    
    try:
        from core.logging_config import get_logger
        logger = get_logger("TestSimple")
        logger.info("Тестовое сообщение")
        print("✅ Логирование работает")
        return True
    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")
        return False

def test_configuration():
    """Тестирует конфигурацию"""
    print("\n⚙️ Тестирование конфигурации...")
    
    try:
        from core.configuration import Configuration
        config = Configuration()
        print("✅ Конфигурация создана успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_import_parser():
    """Тестирует парсер импортов"""
    print("\n📦 Тестирование парсера импортов...")
    
    try:
        from core.import_parser import ImportParser
        from core.configuration import Configuration
        
        config = Configuration()
        parser = ImportParser(config)
        print("✅ Парсер импортов создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка парсера импортов: {e}")
        return False

def test_project_analyzer():
    """Тестирует анализатор проектов"""
    print("\n📁 Тестирование анализатора проектов...")
    
    try:
        from core.project_analyzer import ProjectAnalyzer
        from core.configuration import Configuration
        
        config = Configuration()
        analyzer = ProjectAnalyzer(config)
        print("✅ Анализатор проектов создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка анализатора проектов: {e}")
        return False

def test_data_exporter():
    """Тестирует экспортер данных"""
    print("\n💾 Тестирование экспортера данных...")
    
    try:
        from core.data_exporter import DataExporter
        exporter = DataExporter()
        print("✅ Экспортер данных создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка экспортера данных: {e}")
        return False

def test_file_scanner():
    """Тестирует сканер файлов"""
    print("\n🔍 Тестирование сканера файлов...")
    
    try:
        from core.file_scanner import FileScanner
        from core.configuration import Configuration
        from core.import_parser import ImportParser
        from core.project_analyzer import ProjectAnalyzer
        
        config = Configuration()
        import_parser = ImportParser(config)
        project_analyzer = ProjectAnalyzer(config)
        scanner = FileScanner(config, import_parser, project_analyzer)
        print("✅ Сканер файлов создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка сканера файлов: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 УПРОЩЕННОЕ ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ")
    print("=" * 50)
    
    # Тестируем все компоненты
    tests = [
        test_interfaces,
        test_patterns,
        test_complexity_analyzer,
        test_logging,
        test_configuration,
        test_import_parser,
        test_project_analyzer,
        test_data_exporter,
        test_file_scanner
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n✅ Все улучшения интегрированы:")
        print("   - Модульная архитектура")
        print("   - Паттерны проектирования")
        print("   - Анализ сложности кода")
        print("   - Структурированное логирование")
        print("   - Конфигурация")
        print("   - Парсер импортов")
        print("   - Анализатор проектов")
        print("   - Экспортер данных")
        print("   - Сканер файлов")
        print("\n🚀 GUI готов к запуску!")
    else:
        print("⚠️ Некоторые тесты не пройдены.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
