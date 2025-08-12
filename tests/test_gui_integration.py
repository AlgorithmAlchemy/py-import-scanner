#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции всех улучшений в GUI
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.scan_service import ScanService
from core.configuration import Configuration
from core.complexity_analyzer import ComplexityAnalyzer
from core.patterns import ScanConfigurationBuilder
from core.logging_config import get_logger


def test_scan_service_integration():
    """Тестирует интеграцию ScanService со всеми улучшениями"""
    print("🔧 Тестирование интеграции ScanService...")
    
    try:
        # Создание сервиса
        config = Configuration()
        service = ScanService(config)
        
        print("✅ ScanService создан успешно")
        print(f"   - Фабрика компонентов: {type(service.component_factory).__name__}")
        print(f"   - Субъект наблюдателей: {type(service.scan_subject).__name__}")
        print(f"   - Анализатор сложности: {type(service.complexity_analyzer).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка создания ScanService: {e}")
        return False


def test_patterns_integration():
    """Тестирует интеграцию паттернов проектирования"""
    print("\n🎯 Тестирование паттернов проектирования...")
    
    try:
        # Factory Pattern
        config = Configuration()
        factory = service.component_factory
        
        import_parser = factory.create_component(factory.ComponentType.IMPORT_PARSER)
        print(f"✅ Factory Pattern: создан {type(import_parser).__name__}")
        
        # Strategy Pattern
        strategy_factory = service.ScanningStrategyFactory
        strategy = strategy_factory.create_strategy(
            "adaptive", service.file_scanner, service.import_parser, service.project_analyzer
        )
        print(f"✅ Strategy Pattern: создана {type(strategy).__name__}")
        
        # Observer Pattern
        subject = service.scan_subject
        print(f"✅ Observer Pattern: субъект {type(subject).__name__} готов")
        
        # Builder Pattern
        builder = ScanConfigurationBuilder()
        config = builder.with_strategy("parallel").with_max_workers(4).build()
        print(f"✅ Builder Pattern: конфигурация создана")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка паттернов: {e}")
        return False


def test_complexity_analyzer_integration():
    """Тестирует интеграцию анализатора сложности"""
    print("\n📊 Тестирование анализатора сложности...")
    
    try:
        analyzer = ComplexityAnalyzer()
        
        # Создание тестового файла
        test_file = Path("test_integration.py")
        test_content = '''
def simple_function():
    return "Hello, World!"

def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "very large"
            else:
                return "large"
        else:
            return "small"
    else:
        return "negative"

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Анализ файла
        report = analyzer.analyze_file(test_file)
        print(f"✅ Анализ сложности: оценка {report.grade}")
        print(f"   - Сложность: {report.metrics.cyclomatic_complexity}")
        print(f"   - Функций: {report.metrics.function_count}")
        print(f"   - Классов: {report.metrics.class_count}")
        
        # Удаление тестового файла
        test_file.unlink()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка анализатора сложности: {e}")
        return False


def test_logging_integration():
    """Тестирует интеграцию логирования"""
    print("\n📝 Тестирование логирования...")
    
    try:
        logger = get_logger("TestIntegration")
        logger.info("Тестовое сообщение", extra_data={"test": True})
        print("✅ Логирование работает")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")
        return False


def test_security_integration():
    """Тестирует интеграцию безопасности"""
    print("\n🔒 Тестирование безопасности...")
    
    try:
        security_manager = service.security_manager
        
        # Тест валидации файла
        test_file = Path("test_security.py")
        with open(test_file, 'w') as f:
            f.write("print('Hello')")
        
        is_valid, message = security_manager.validate_file(test_file)
        print(f"✅ Валидация файла: {is_valid} - {message}")
        
        # Удаление тестового файла
        test_file.unlink()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка безопасности: {e}")
        return False


def test_performance_integration():
    """Тестирует интеграцию производительности"""
    print("\n⚡ Тестирование производительности...")
    
    try:
        performance_manager = service.performance_manager
        
        # Тест профилирования
        performance_manager.start_profiling("test_operation")
        performance_manager.end_profiling("test_operation")
        
        # Тест кэша
        cache_key = performance_manager.generate_cache_key("test", "data")
        print(f"✅ Производительность: кэш ключ {cache_key[:20]}...")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка производительности: {e}")
        return False


def test_gui_ready():
    """Проверяет готовность к запуску GUI"""
    print("\n🖥️ Проверка готовности GUI...")
    
    try:
        # Проверяем наличие всех необходимых компонентов
        required_components = [
            'ScanService',
            'ComponentFactory', 
            'ScanSubject',
            'ComplexityAnalyzer',
            'SecurityManager',
            'PerformanceManager'
        ]
        
        for component in required_components:
            if hasattr(service, component.lower().replace('manager', '_manager')):
                print(f"✅ {component} готов")
            else:
                print(f"❌ {component} отсутствует")
                return False
        
        print("✅ Все компоненты готовы для GUI")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки GUI: {e}")
        return False


def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ВСЕХ УЛУЧШЕНИЙ")
    print("=" * 60)
    
    global service
    
    # Тестируем все компоненты
    tests = [
        test_scan_service_integration,
        test_patterns_integration,
        test_complexity_analyzer_integration,
        test_logging_integration,
        test_security_integration,
        test_performance_integration,
        test_gui_ready
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! GUI готов к запуску!")
        print("\n🚀 Рекомендации:")
        print("   - Запустите: python src/main_refactored.py")
        print("   - Все улучшения интегрированы")
        print("   - Паттерны проектирования работают")
        print("   - Анализ сложности доступен")
        print("   - Безопасность и производительность активны")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте зависимости.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
