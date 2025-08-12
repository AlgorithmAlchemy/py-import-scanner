# Руководство по структурированному логированию

## Обзор

Система структурированного логирования в Python Import Parser предоставляет мощные возможности для мониторинга, отладки и анализа работы приложения. Логирование интегрировано во все основные модули и предоставляет детальную информацию о процессе сканирования.

## Архитектура

### Основные компоненты

1. **LogConfig** - конфигурация логирования
2. **StructuredFormatter** - форматирование логов в различных форматах
3. **LoggerManager** - управление логгерами
4. **Глобальные функции** - setup_logging, get_logger, log_with_context

### Структура логов

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "ScanService",
  "message": "Сканирование завершено успешно",
  "module": "scan_service",
  "function": "scan_directory",
  "line": 85,
  "total_files": 150,
  "total_imports": 1200,
  "duration": 45.67,
  "projects_found": 5
}
```

## Конфигурация

### Настройки в config.json

```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file_enabled": true,
    "console_enabled": true,
    "max_file_size": 10485760,
    "backup_count": 5,
    "log_dir": "logs",
    "include_timestamp": true,
    "include_module": true,
    "include_function": true,
    "include_line": true
  }
}
```

### Параметры конфигурации

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `level` | string | "INFO" | Уровень логирования (DEBUG, INFO, WARNING, ERROR) |
| `format` | string | "json" | Формат логов (json, text, simple) |
| `file_enabled` | boolean | true | Включить запись в файл |
| `console_enabled` | boolean | true | Включить вывод в консоль |
| `max_file_size` | integer | 10MB | Максимальный размер файла лога |
| `backup_count` | integer | 5 | Количество резервных файлов |
| `log_dir` | string | "logs" | Директория для логов |
| `include_timestamp` | boolean | true | Включать временную метку |
| `include_module` | boolean | true | Включать имя модуля |
| `include_function` | boolean | true | Включать имя функции |
| `include_line` | boolean | true | Включать номер строки |

## Использование

### Базовое логирование

```python
from core.logging_config import get_logger

# Получение логгера
logger = get_logger("MyModule")

# Простое логирование
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.debug("Отладочная информация")
```

### Логирование с контекстом

```python
# Логирование с дополнительными данными
logger.info("Обработка файла", 
           extra_data={
               "file_path": str(file_path),
               "file_size": file_size,
               "processing_time": 1.23
           })

# Логирование ошибок с контекстом
try:
    # Код, который может вызвать ошибку
    pass
except Exception as e:
    logger.error("Ошибка при обработке", 
                extra_data={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "file_path": str(file_path)
                })
```

### Настройка логирования

```python
from core.logging_config import setup_logging, LogConfig

# Создание конфигурации
config = LogConfig(
    level="DEBUG",
    format="text",
    file_enabled=True,
    console_enabled=False,
    log_dir="custom_logs"
)

# Настройка глобального логирования
setup_logging(config)
```

## Форматы логов

### JSON формат

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "FileScanner",
  "message": "Найдено 150 Python файлов",
  "module": "file_scanner",
  "function": "scan_directory",
  "line": 67,
  "files_found": 150
}
```

### Текстовый формат

```
[2024-01-15 10:30:45] [INFO    ] [FileScanner] [file_scanner] [scan_directory] [L67] Найдено 150 Python файлов (files_found=150)
```

### Простой формат

```
INFO: Найдено 150 Python файлов
```

## Файлы логов

### Структура директории

```
logs/
├── app_20240115.log          # Основные логи приложения
├── app_20240115.log.1        # Резервные файлы
├── app_20240115.log.2
├── errors_20240115.log       # Логи ошибок
├── errors_20240115.log.1
└── errors_20240115.log.2
```

### Ротация файлов

- Файлы автоматически ротируются при достижении максимального размера
- Старые файлы сохраняются с суффиксами .1, .2, и т.д.
- Количество резервных файлов настраивается в конфигурации

## Интеграция в модули

### ScanService

```python
class ScanService:
    def __init__(self, config: Configuration = None):
        # Настройка логирования
        log_config_dict = self.config.get_logging_config()
        log_config = LogConfig(**log_config_dict)
        setup_logging(log_config)
        self.logger = get_logger("ScanService")
        
        self.logger.info("ScanService инициализирован")
    
    def scan_directory(self, directory: Path):
        self.logger.info("Начало сканирования", 
                        extra_data={"directory": str(directory)})
        
        try:
            # Логика сканирования
            result = self.file_scanner.scan_directory(directory)
            
            self.logger.info("Сканирование завершено", 
                           extra_data={
                               "total_files": result.total_files_scanned,
                               "total_imports": result.total_imports,
                               "duration": result.scan_duration
                           })
            
            return result
        except Exception as e:
            self.logger.error("Ошибка при сканировании", 
                            extra_data={"error": str(e)})
            raise
```

### FileScanner

```python
class FileScanner:
    def __init__(self, config, import_parser, project_analyzer):
        self.logger = get_logger("FileScanner")
        self.logger.info("FileScanner инициализирован")
    
    def scan_directory(self, directory: Path):
        self.logger.info("Начало сканирования директории")
        
        # Поиск файлов
        file_paths = self._find_python_files(directory)
        self.logger.info("Поиск файлов завершен", 
                        extra_data={"files_found": len(file_paths)})
        
        # Сканирование
        all_imports = self._scan_files_parallel(file_paths)
        
        self.logger.info("Сканирование завершено", 
                        extra_data={
                            "total_files": len(file_paths),
                            "total_imports": sum(all_imports.values())
                        })
```

### ImportParser

```python
class ImportParser:
    def __init__(self, config):
        self.logger = get_logger("ImportParser")
        self.logger.info("ImportParser инициализирован")
    
    def parse_imports(self, content: str, file_path: Path):
        try:
            # Парсинг импортов
            imports = self._parse_ast(content)
            
            self.logger.debug("Парсинг завершен", 
                            extra_data={
                                "file": str(file_path),
                                "imports_found": len(imports)
                            })
            
            return imports
        except (SyntaxError, ValueError) as e:
            self.logger.warning("Синтаксическая ошибка", 
                              extra_data={
                                  "file": str(file_path),
                                  "error": str(e)
                              })
            return []
```

## Мониторинг и анализ

### Ключевые метрики

1. **Производительность**
   - Время сканирования
   - Количество обработанных файлов
   - Скорость обработки (файлов/сек)

2. **Качество данных**
   - Количество найденных импортов
   - Количество проектов
   - Ошибки парсинга

3. **Системные метрики**
   - Использование памяти
   - Количество потоков
   - Размер файлов

### Анализ логов

```python
import json
from pathlib import Path

def analyze_logs(log_file: Path):
    """Анализ логов для извлечения метрик"""
    metrics = {
        "total_entries": 0,
        "errors": 0,
        "warnings": 0,
        "scan_sessions": 0,
        "avg_scan_duration": 0
    }
    
    durations = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    metrics["total_entries"] += 1
                    
                    if data["level"] == "ERROR":
                        metrics["errors"] += 1
                    elif data["level"] == "WARNING":
                        metrics["warnings"] += 1
                    
                    if "Сканирование завершено" in data["message"]:
                        metrics["scan_sessions"] += 1
                        if "duration" in data:
                            durations.append(data["duration"])
                            
                except json.JSONDecodeError:
                    continue
    
    if durations:
        metrics["avg_scan_duration"] = sum(durations) / len(durations)
    
    return metrics
```

## Лучшие практики

### 1. Используйте контекстные данные

```python
# Хорошо
logger.info("Обработка файла", 
           extra_data={"file_path": str(file_path), "size": file_size})

# Плохо
logger.info(f"Обработка файла {file_path} размером {file_size}")
```

### 2. Логируйте исключения правильно

```python
try:
    # Код
    pass
except Exception as e:
    logger.error("Ошибка при обработке", 
                extra_data={"error_type": type(e).__name__, "error": str(e)})
    # Не логируйте и не поднимайте исключение повторно
    raise
```

### 3. Используйте правильные уровни

- **DEBUG** - детальная отладочная информация
- **INFO** - общая информация о ходе выполнения
- **WARNING** - предупреждения, которые не прерывают работу
- **ERROR** - ошибки, которые влияют на функциональность

### 4. Избегайте логирования в циклах

```python
# Плохо - много логов
for file in files:
    logger.info(f"Обработка файла {file}")

# Хорошо - логируем только важные события
logger.info("Начало обработки файлов", extra_data={"count": len(files)})
for file in files:
    # Обработка файла
    pass
logger.info("Обработка файлов завершена")
```

## Тестирование

### Запуск тестов логирования

```bash
# Запуск всех тестов логирования
pytest tests/test_logging.py -v

# Запуск конкретного теста
pytest tests/test_logging.py::TestLoggingIntegration::test_full_logging_flow -v

# Запуск с выводом логов
pytest tests/test_logging.py -v -s
```

### Тестирование в коде

```python
def test_logging_integration():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Настройка логирования для тестов
        config = LogConfig(
            level="DEBUG",
            log_dir=temp_dir,
            file_enabled=True,
            console_enabled=False
        )
        setup_logging(config)
        
        # Тестирование
        logger = get_logger("test")
        logger.info("Test message")
        
        # Проверка результатов
        log_files = list(Path(temp_dir).glob("*.log"))
        assert len(log_files) > 0
```

## Заключение

Структурированное логирование предоставляет мощные возможности для мониторинга и отладки приложения. Правильное использование системы логирования поможет:

- Отслеживать производительность приложения
- Диагностировать проблемы
- Анализировать использование ресурсов
- Улучшать качество кода

Система полностью интегрирована в архитектуру приложения и готова к использованию в продакшене.
