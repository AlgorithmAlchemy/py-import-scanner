"""
Пример использования системы структурированного логирования
"""
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging_config import setup_logging, get_logger, LogConfig
from core.configuration import Configuration
from core.scan_service import ScanService


def example_basic_logging():
    """Пример базового логирования"""
    print("=== Пример базового логирования ===")
    
    # Настройка логирования
    config = LogConfig(
        level="DEBUG",
        format="text",
        file_enabled=True,
        console_enabled=True,
        log_dir="example_logs"
    )
    setup_logging(config)
    
    # Получение логгера
    logger = get_logger("Example")
    
    # Простое логирование
    logger.info("Приложение запущено")
    logger.debug("Отладочная информация")
    logger.warning("Предупреждение")
    logger.error("Ошибка")
    
    print("Логи сохранены в директории 'example_logs'")


def example_context_logging():
    """Пример логирования с контекстом"""
    print("\n=== Пример логирования с контекстом ===")
    
    # Настройка логирования в JSON формате
    config = LogConfig(
        level="INFO",
        format="json",
        file_enabled=True,
        console_enabled=False,
        log_dir="example_logs"
    )
    setup_logging(config)
    
    logger = get_logger("ContextExample")
    
    # Логирование с дополнительными данными
    logger.info("Обработка файла", 
               extra_data={
                   "file_path": "/path/to/file.py",
                   "file_size": 1024,
                   "processing_time": 1.23,
                   "status": "success"
               })
    
    # Логирование ошибки с контекстом
    try:
        raise ValueError("Тестовая ошибка")
    except Exception as e:
        logger.error("Ошибка при обработке", 
                    extra_data={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "file_path": "/path/to/file.py"
                    })
    
    print("Контекстные логи сохранены в JSON формате")


def example_scan_service_logging():
    """Пример логирования в ScanService"""
    print("\n=== Пример логирования в ScanService ===")
    
    # Создание конфигурации с логированием
    config = Configuration()
    config.update_logging_config("level", "INFO")
    config.update_logging_config("format", "text")
    config.update_logging_config("log_dir", "example_logs")
    
    # Создание сервиса (автоматически настроит логирование)
    service = ScanService(config)
    
    # Попытка сканирования (будет залогирована)
    try:
        # Сканируем текущую директорию
        result = service.scan_directory(Path("."))
        print(f"Сканирование завершено: {result.total_files_scanned} файлов")
    except Exception as e:
        print(f"Ошибка сканирования: {e}")
    
    print("Логи ScanService сохранены")


def example_log_analysis():
    """Пример анализа логов"""
    print("\n=== Пример анализа логов ===")
    
    import json
    from collections import defaultdict
    
    log_file = Path("example_logs/app_20240115.log")
    
    if log_file.exists():
        stats = defaultdict(int)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        stats["total_entries"] += 1
                        stats[data["level"]] += 1
                        
                        if "logger" in data:
                            stats[f"logger_{data['logger']}"] += 1
                            
                    except json.JSONDecodeError:
                        continue
        
        print("Статистика логов:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("Файл логов не найден")


def main():
    """Главная функция примера"""
    print("🚀 Примеры использования системы логирования\n")
    
    # Создаем директорию для логов
    log_dir = Path("example_logs")
    log_dir.mkdir(exist_ok=True)
    
    # Запускаем примеры
    example_basic_logging()
    example_context_logging()
    example_scan_service_logging()
    example_log_analysis()
    
    print("\n✅ Все примеры выполнены!")
    print("📁 Проверьте директорию 'example_logs' для просмотра логов")


if __name__ == "__main__":
    main()
