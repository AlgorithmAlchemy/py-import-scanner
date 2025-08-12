"""
Пример использования модуля безопасности
"""
import sys
import tempfile
from pathlib import Path

# Добавляем путь к src для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.security import SecurityConfig, SecurityManager
from core.configuration import Configuration


def demonstrate_security_features():
    """Демонстрация функций безопасности"""
    print("🔒 Демонстрация модуля безопасности Python Import Parser")
    print("=" * 60)
    
    # Создание конфигурации безопасности
    print("\n1. Создание конфигурации безопасности")
    security_config = SecurityConfig(
        max_file_size=1024,  # 1KB для демонстрации
        max_files_per_scan=10,
        max_total_size=2048,
        check_for_malicious_patterns=True,
        validate_imports=True,
        sanitize_content=True
    )
    
    print(f"   - Максимальный размер файла: {security_config.max_file_size} байт")
    print(f"   - Максимальное количество файлов: {security_config.max_files_per_scan}")
    print(f"   - Проверка злонамеренных паттернов: {security_config.check_for_malicious_patterns}")
    
    # Создание менеджера безопасности
    print("\n2. Инициализация менеджера безопасности")
    security_manager = SecurityManager(security_config)
    
    # Демонстрация валидации путей
    print("\n3. Валидация путей файлов")
    test_paths = [
        "normal_file.py",
        "path/with/../traversal.py",
        "/absolute/path/file.py",
        "file_with_blocked_pattern/__pycache__/file.py",
        "file_with_wrong_extension.txt"
    ]
    
    for path in test_paths:
        is_valid, message = security_manager.validator.validate_file_path(Path(path))
        status = "✅" if is_valid else "❌"
        print(f"   {status} {path}: {message}")
    
    # Демонстрация валидации содержимого
    print("\n4. Валидация содержимого файлов")
    test_contents = [
        "import os\nimport sys\n",  # Нормальное содержимое
        "eval('print(\"hello\")')",  # Злонамеренный паттерн
        "import os\n" * 1001,  # Слишком много импортов
        "line_with_very_long_content_" * 1000,  # Слишком длинная строка
    ]
    
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        temp_file = Path(f.name)
    
    try:
        for i, content in enumerate(test_contents, 1):
            is_valid, message, sanitized = security_manager.validate_and_sanitize_content(content, temp_file)
            status = "✅" if is_valid else "❌"
            print(f"   {status} Тест {i}: {message}")
            if not is_valid:
                print(f"      Ошибка: {message}")
    finally:
        if temp_file.exists():
            temp_file.unlink()
    
    # Демонстрация валидации импортов
    print("\n5. Валидация импортов")
    test_imports = [
        ["os", "sys", "json"],  # Нормальные импорты
        ["pickle", "subprocess"],  # Подозрительные импорты
        ["123invalid", "class"],  # Недопустимые имена
        ["very_long_import_name_" * 10],  # Слишком длинное имя
    ]
    
    for i, imports in enumerate(test_imports, 1):
        is_valid, message = security_manager.validate_imports(imports, temp_file)
        status = "✅" if is_valid else "❌"
        print(f"   {status} Тест {i}: {message}")
        if not is_valid:
            print(f"      Ошибка: {message}")
    
    # Демонстрация санитизации
    print("\n6. Санитизация содержимого")
    dirty_content = "import os\x00\n\r\nimport sys\r\n  "
    sanitized = security_manager.validator.sanitize_content(dirty_content)
    
    print(f"   Исходное содержимое: {repr(dirty_content)}")
    print(f"   Санитизированное: {repr(sanitized)}")
    
    # Демонстрация хеширования файлов
    print("\n7. Хеширование файлов")
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content for hashing")
        temp_file = Path(f.name)
    
    try:
        file_hash = security_manager.get_file_hash(temp_file)
        print(f"   Хеш файла: {file_hash}")
        
        # Проверка кэширования
        file_hash2 = security_manager.get_file_hash(temp_file)
        print(f"   Хеш из кэша: {file_hash2}")
        print(f"   Кэширование работает: {file_hash == file_hash2}")
    finally:
        if temp_file.exists():
            temp_file.unlink()
    
    # Демонстрация отчета о безопасности
    print("\n8. Отчет о безопасности")
    report = security_manager.get_security_report()
    
    print("   Статистика безопасности:")
    for key, value in report.items():
        if key != "security_config":
            print(f"     {key}: {value}")
    
    print("\n   Конфигурация безопасности:")
    for key, value in report["security_config"].items():
        print(f"     {key}: {value}")


def demonstrate_integration_with_configuration():
    """Демонстрация интеграции с системой конфигурации"""
    print("\n🔧 Интеграция с системой конфигурации")
    print("=" * 60)
    
    # Создание конфигурации
    config = Configuration()
    
    # Получение текущих настроек безопасности
    print("\n1. Текущие настройки безопасности:")
    security_config = config.get_security_config()
    for key, value in security_config.items():
        print(f"   {key}: {value}")
    
    # Обновление настроек безопасности
    print("\n2. Обновление настроек безопасности:")
    config.update_security_config("max_file_size", 1024 * 1024)  # 1MB
    config.update_security_config("check_for_malicious_patterns", False)
    
    print("   - Установлен максимальный размер файла: 1MB")
    print("   - Отключена проверка злонамеренных паттернов")
    
    # Проверка обновленных настроек
    print("\n3. Обновленные настройки:")
    updated_config = config.get_security_config()
    print(f"   max_file_size: {updated_config['max_file_size']}")
    print(f"   check_for_malicious_patterns: {updated_config['check_for_malicious_patterns']}")


def demonstrate_security_validation_flow():
    """Демонстрация полного потока валидации безопасности"""
    print("\n🔄 Полный поток валидации безопасности")
    print("=" * 60)
    
    # Создание временной директории с тестовыми файлами
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Создание безопасных файлов
        (temp_path / "safe_file.py").write_text("import os\nimport sys\n")
        (temp_path / "malicious_file.py").write_text("eval('print(\"hello\")')\n")
        (temp_path / "large_file.py").write_text("import os\n" * 1001)
        
        print(f"Создана тестовая директория: {temp_path}")
        print("Созданы файлы:")
        print("  - safe_file.py (безопасный)")
        print("  - malicious_file.py (злонамеренный)")
        print("  - large_file.py (слишком много импортов)")
        
        # Создание менеджера безопасности
        security_config = SecurityConfig(
            max_file_size=1024,
            max_files_per_scan=5,
            max_total_size=2048,
            check_for_malicious_patterns=True,
            validate_imports=True,
            sanitize_content=True
        )
        security_manager = SecurityManager(security_config)
        
        # Валидация запроса на сканирование
        print("\n1. Валидация запроса на сканирование:")
        is_valid, message = security_manager.validate_scan_request(temp_path)
        print(f"   Результат: {message}")
        
        # Валидация каждого файла
        print("\n2. Валидация отдельных файлов:")
        for py_file in temp_path.glob("*.py"):
            print(f"\n   Файл: {py_file.name}")
            
            # Валидация файла
            is_valid, message = security_manager.validate_file(py_file)
            print(f"     Валидация файла: {'✅' if is_valid else '❌'} {message}")
            
            if is_valid:
                # Валидация содержимого
                content = py_file.read_text()
                is_valid, message, sanitized = security_manager.validate_and_sanitize_content(content, py_file)
                print(f"     Валидация содержимого: {'✅' if is_valid else '❌'} {message}")
                
                if is_valid:
                    # Валидация импортов
                    imports = ["os", "sys"]
                    is_valid, message = security_manager.validate_imports(imports, py_file)
                    print(f"     Валидация импортов: {'✅' if is_valid else '❌'} {message}")
        
        # Финальный отчет
        print("\n3. Финальный отчет о безопасности:")
        report = security_manager.get_security_report()
        print(f"   Обработано файлов: {report['files_processed']}")
        print(f"   Общий размер: {report['total_size_processed']} байт")
        print(f"   Время сканирования: {report['scan_duration']:.2f} сек")


def main():
    """Главная функция"""
    try:
        demonstrate_security_features()
        demonstrate_integration_with_configuration()
        demonstrate_security_validation_flow()
        
        print("\n" + "=" * 60)
        print("✅ Демонстрация модуля безопасности завершена успешно!")
        print("\nОсновные возможности:")
        print("  - Валидация путей файлов (защита от path traversal)")
        print("  - Обнаружение злонамеренных паттернов")
        print("  - Валидация импортов")
        print("  - Санитизация содержимого")
        print("  - Мониторинг ресурсов")
        print("  - Интеграция с системой конфигурации")
        print("  - Подробное логирование")
        
    except Exception as e:
        print(f"\n❌ Ошибка при демонстрации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
