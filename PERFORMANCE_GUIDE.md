# Руководство по производительности - Python Import Parser

## Обзор

Модуль производительности обеспечивает комплексную оптимизацию приложения для максимальной скорости работы и эффективного использования ресурсов. Реализованы механизмы кэширования, профилирования, оптимизации памяти и адаптивного управления потоками.

## Архитектура производительности

### Основные компоненты

1. **PerformanceConfig** - Конфигурация параметров производительности
2. **LRUCache** - LRU кэш с TTL для кэширования результатов
3. **PerformanceProfiler** - Профилировщик производительности
4. **MemoryOptimizer** - Оптимизатор памяти
5. **ThreadOptimizer** - Оптимизатор потоков
6. **PerformanceManager** - Менеджер производительности (фасад)

### Принципы оптимизации

- **Кэширование** - Сохранение результатов для повторного использования
- **Профилирование** - Измерение времени выполнения операций
- **Оптимизация памяти** - Автоматическая сборка мусора
- **Адаптивность** - Динамическая настройка параметров
- **Мониторинг** - Отслеживание использования ресурсов

## Конфигурация производительности

### Параметры кэширования

```python
enable_caching: bool = True
cache_size: int = 1000
cache_ttl: int = 3600  # 1 час
cache_file: str = "cache/performance_cache.json"
```

### Параметры оптимизации памяти

```python
enable_memory_optimization: bool = True
gc_threshold: int = 100  # Количество файлов до сборки мусора
memory_check_interval: int = 50  # Проверка памяти каждые N файлов
```

### Параметры профилирования

```python
enable_profiling: bool = True
profile_file: str = "logs/performance_profile.json"
detailed_profiling: bool = False
```

### Параметры оптимизации потоков

```python
optimal_threads: int = 0  # 0 = автоопределение
thread_chunk_size: int = 100
adaptive_threading: bool = True
```

### Параметры кэширования результатов

```python
cache_imports: bool = True
cache_file_hashes: bool = True
cache_directory_structure: bool = True
```

## Компоненты системы

### LRUCache

LRU (Least Recently Used) кэш с поддержкой TTL (Time To Live).

#### Основные методы

```python
# Добавление элемента в кэш
cache.put(key: str, value: Any) -> None

# Получение элемента из кэша
cache.get(key: str) -> Optional[Any]

# Получение размера кэша
cache.size() -> int

# Очистка кэша
cache.clear() -> None
```

#### Пример использования

```python
from src.core.performance import LRUCache

# Создание кэша
cache = LRUCache(max_size=1000, ttl=3600)

# Кэширование результата
cache.put("file_hash_123", ["numpy", "pandas", "matplotlib"])

# Получение из кэша
imports = cache.get("file_hash_123")
if imports:
    print("Результат найден в кэше:", imports)
```

### PerformanceProfiler

Профилировщик для измерения времени выполнения операций.

#### Основные методы

```python
# Запуск таймера
profiler.start_timer(name: str) -> None

# Остановка таймера и получение времени
profiler.end_timer(name: str) -> float

# Добавление метрики
profiler.add_metric(name: str, value: float) -> None

# Получение статистики
profiler.get_statistics() -> Dict[str, Dict[str, float]]

# Сохранение профиля
profiler.save_profile() -> None
```

#### Пример использования

```python
from src.core.performance import PerformanceProfiler, PerformanceConfig

config = PerformanceConfig(profile_file="my_profile.json")
profiler = PerformanceProfiler(config)

# Профилирование операции
profiler.start_timer("scan_directory")
# ... выполнение операции ...
duration = profiler.end_timer("scan_directory")

# Добавление метрики
profiler.add_metric("files_per_second", 150.5)

# Получение статистики
stats = profiler.get_statistics()
print(f"Среднее время сканирования: {stats['scan_directory']['average']:.2f}с")
```

### MemoryOptimizer

Оптимизатор памяти с автоматической сборкой мусора.

#### Основные методы

```python
# Проверка использования памяти
optimizer.check_memory_usage() -> Dict[str, float]

# Определение необходимости сборки мусора
optimizer.should_gc() -> bool

# Выполнение оптимизации памяти
optimizer.optimize_memory() -> None

# Логирование использования памяти
optimizer.log_memory_usage() -> None
```

#### Пример использования

```python
from src.core.performance import MemoryOptimizer, PerformanceConfig

config = PerformanceConfig(gc_threshold=50)
optimizer = MemoryOptimizer(config)

# Проверка памяти
memory_info = optimizer.check_memory_usage()
print(f"Использование памяти: {memory_info['rss']:.1f} MB")

# Оптимизация памяти
if optimizer.should_gc():
    optimizer.optimize_memory()
```

### ThreadOptimizer

Оптимизатор потоков с адаптивной настройкой.

#### Основные методы

```python
# Определение оптимального количества потоков
optimizer.get_optimal_thread_count(file_count: int, available_memory: float) -> int

# Определение размера чанка
optimizer.get_chunk_size(file_count: int, thread_count: int) -> int

# Запись производительности для адаптации
optimizer.record_performance(thread_count: int, processing_time: float) -> None
```

#### Пример использования

```python
from src.core.performance import ThreadOptimizer, PerformanceConfig

config = PerformanceConfig(adaptive_threading=True)
optimizer = ThreadOptimizer(config)

# Определение оптимальных параметров
file_count = 1000
available_memory = 2048  # MB

threads = optimizer.get_optimal_thread_count(file_count, available_memory)
chunk_size = optimizer.get_chunk_size(file_count, threads)

print(f"Оптимальное количество потоков: {threads}")
print(f"Размер чанка: {chunk_size}")

# Запись производительности
optimizer.record_performance(threads, 15.5)
```

### PerformanceManager

Главный менеджер производительности, объединяющий все компоненты.

#### Основные методы

```python
# Кэширование
manager.cache_result(key: str, value: Any) -> None
manager.get_cached_result(key: str) -> Optional[Any]
manager.clear_cache() -> None

# Профилирование
manager.start_profiling(name: str) -> None
manager.end_profiling(name: str) -> float

# Оптимизация памяти
manager.optimize_memory() -> None
manager.get_memory_usage() -> Dict[str, float]

# Оптимизация потоков
manager.get_optimal_threads(file_count: int) -> int
manager.get_chunk_size(file_count: int, thread_count: int) -> int

# Утилиты
manager.generate_cache_key(*args, **kwargs) -> str
manager.get_performance_report() -> Dict[str, Any]
manager.save_performance_data() -> None
```

#### Пример использования

```python
from src.core.performance import PerformanceManager, PerformanceConfig

# Создание менеджера
config = PerformanceConfig(
    enable_caching=True,
    enable_profiling=True,
    enable_memory_optimization=True,
    cache_size=2000,
    adaptive_threading=True
)
manager = PerformanceManager(config)

# Кэширование результата
cache_key = manager.generate_cache_key("scan_file", "path/to/file.py", 12345)
manager.cache_result(cache_key, ["numpy", "pandas"])

# Профилирование операции
manager.start_profiling("file_scanning")
# ... выполнение операции ...
duration = manager.end_profiling("file_scanning")

# Оптимизация памяти
manager.optimize_memory()

# Получение отчета
report = manager.get_performance_report()
print(f"Размер кэша: {report['cache']['size']}")
print(f"Использование памяти: {report['memory']['rss']:.1f} MB")
```

## Декораторы

### @cached

Декоратор для автоматического кэширования результатов функций.

```python
from src.core.performance import cached, PerformanceManager

manager = PerformanceManager()

@cached(manager)
def expensive_operation(file_path: str, content: str) -> List[str]:
    # Дорогая операция
    return parse_imports(content)

# Первый вызов выполнит операцию и кэширует результат
result1 = expensive_operation("file1.py", "import numpy")
# Второй вызов с теми же параметрами вернет результат из кэша
result2 = expensive_operation("file1.py", "import numpy")
```

### @profiled

Декоратор для автоматического профилирования функций.

```python
from src.core.performance import profiled, PerformanceManager

manager = PerformanceManager()

@profiled(manager)
def scan_file(file_path: str) -> List[str]:
    # Операция будет автоматически профилироваться
    return parse_file(file_path)

# Вызов функции с автоматическим профилированием
imports = scan_file("example.py")
```

## Интеграция с основными модулями

### ScanService

```python
# Инициализация в конструкторе
performance_config_dict = self.config.get_performance_config()
performance_config = PerformanceConfig(**performance_config_dict)
self.performance_manager = PerformanceManager(performance_config)

# Использование в методе сканирования
def scan_directory(self, directory: Path, progress_callback=None) -> ScanResult:
    # Запуск профилирования
    self.performance_manager.start_profiling("scan_directory")
    
    # ... выполнение сканирования ...
    
    # Завершение профилирования
    scan_duration = self.performance_manager.end_profiling("scan_directory")
    
    # Сохранение данных производительности
    self.performance_manager.save_performance_data()
    
    return result

# Получение отчета о производительности
def get_performance_report(self) -> dict:
    return self.performance_manager.get_performance_report()
```

### FileScanner

```python
# Инициализация в конструкторе
performance_config_dict = config.get_performance_config()
performance_config = PerformanceConfig(**performance_config_dict)
self.performance_manager = PerformanceManager(performance_config)

# Кэширование в методе сканирования файла
def scan_file(self, file_path: Path) -> List[str]:
    # Генерация ключа кэша
    cache_key = self.performance_manager.generate_cache_key(
        "scan_file", str(file_path), file_path.stat().st_mtime
    )
    
    # Попытка получить из кэша
    cached_result = self.performance_manager.get_cached_result(cache_key)
    if cached_result is not None:
        return cached_result
    
    # ... выполнение сканирования ...
    
    # Кэширование результата
    self.performance_manager.cache_result(cache_key, imports)
    return imports

# Оптимизация в параллельном сканировании
def _scan_files_parallel(self, file_paths: List[Path], progress_callback=None) -> Dict[str, int]:
    # Получение оптимальных параметров
    optimal_threads = self.performance_manager.get_optimal_threads(len(file_paths))
    chunk_size = self.performance_manager.get_chunk_size(len(file_paths), optimal_threads)
    
    # ... выполнение сканирования ...
    
    # Оптимизация памяти
    self.performance_manager.optimize_memory()
```

### ImportParser

```python
# Инициализация в конструкторе
performance_config_dict = config.get_performance_config()
performance_config = PerformanceConfig(**performance_config_dict)
self.performance_manager = PerformanceManager(performance_config)

# Кэширование в методе парсинга
def parse_imports(self, content: str, file_path: Path) -> List[str]:
    # Генерация ключа кэша
    cache_key = self.performance_manager.generate_cache_key(
        "parse_imports", str(file_path), hash(content)
    )
    
    # Попытка получить из кэша
    cached_result = self.performance_manager.get_cached_result(cache_key)
    if cached_result is not None:
        return cached_result
    
    # ... выполнение парсинга ...
    
    # Кэширование результата
    self.performance_manager.cache_result(cache_key, imports)
    return imports
```

## Конфигурация

### Добавление в config.json

```json
{
  "performance": {
    "enable_caching": true,
    "cache_size": 1000,
    "cache_ttl": 3600,
    "cache_file": "cache/performance_cache.json",
    "enable_memory_optimization": true,
    "gc_threshold": 100,
    "memory_check_interval": 50,
    "enable_profiling": true,
    "profile_file": "logs/performance_profile.json",
    "detailed_profiling": false,
    "optimal_threads": 0,
    "thread_chunk_size": 100,
    "adaptive_threading": true,
    "cache_imports": true,
    "cache_file_hashes": true,
    "cache_directory_structure": true
  }
}
```

### Программная настройка

```python
from src.core.configuration import Configuration

config = Configuration()

# Обновление настроек производительности
config.update_performance_config("cache_size", 2000)
config.update_performance_config("enable_profiling", True)
config.update_performance_config("adaptive_threading", True)

# Получение настроек
performance_config = config.get_performance_config()
print(f"Размер кэша: {performance_config['cache_size']}")
```

## Мониторинг и анализ

### Отчет о производительности

```python
# Получение полного отчета
report = scan_service.get_performance_report()

print("=== ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ ===")
print(f"Размер кэша: {report['cache']['size']}/{report['cache']['max_size']}")
print(f"Использование памяти: {report['memory']['rss']:.1f} MB")
print(f"Доступная память: {report['memory']['available']:.1f} MB")

print("\n=== ПРОФИЛИРОВАНИЕ ===")
for operation, stats in report['profiling'].items():
    print(f"{operation}:")
    print(f"  Количество вызовов: {stats['count']}")
    print(f"  Среднее время: {stats['average']:.3f}с")
    print(f"  Минимальное время: {stats['min']:.3f}с")
    print(f"  Максимальное время: {stats['max']:.3f}с")
```

### Анализ профиля

```python
import json

# Загрузка профиля из файла
with open("logs/performance_profile.json", "r") as f:
    profile = json.load(f)

# Анализ статистики
statistics = profile['statistics']

# Поиск самых медленных операций
slow_operations = sorted(
    statistics.items(),
    key=lambda x: x[1]['average'],
    reverse=True
)[:5]

print("Самые медленные операции:")
for operation, stats in slow_operations:
    print(f"{operation}: {stats['average']:.3f}с (в среднем)")
```

## Рекомендации по использованию

### Настройка кэша

1. **Размер кэша**: Устанавливайте в зависимости от доступной памяти
   - 1000-2000 элементов для небольших проектов
   - 5000-10000 элементов для крупных проектов

2. **TTL кэша**: Зависит от частоты изменений файлов
   - 1800 секунд (30 минут) для стабильных проектов
   - 3600 секунд (1 час) для активной разработки

### Оптимизация памяти

1. **Порог сборки мусора**: Настройте в зависимости от размера файлов
   - 50-100 файлов для больших файлов
   - 200-500 файлов для маленьких файлов

2. **Мониторинг памяти**: Регулярно проверяйте отчеты о производительности

### Настройка потоков

1. **Адаптивное управление**: Включите для автоматической оптимизации
2. **Фиксированное количество**: Используйте только при необходимости
3. **Размер чанка**: Автоматически настраивается, но можно переопределить

### Профилирование

1. **Детальное профилирование**: Включайте только для отладки
2. **Сохранение профилей**: Регулярно анализируйте для оптимизации
3. **Мониторинг**: Отслеживайте тренды производительности

## Устранение неполадок

### Высокое использование памяти

```python
# Уменьшите размер кэша
config.update_performance_config("cache_size", 500)

# Увеличьте частоту сборки мусора
config.update_performance_config("gc_threshold", 50)

# Отключите кэширование при необходимости
config.update_performance_config("enable_caching", False)
```

### Медленная работа

```python
# Увеличьте размер кэша
config.update_performance_config("cache_size", 2000)

# Уменьшите частоту сборки мусора
config.update_performance_config("gc_threshold", 200)

# Настройте количество потоков
config.update_performance_config("optimal_threads", 8)
```

### Проблемы с кэшем

```python
# Очистите кэш
performance_manager.clear_cache()

# Проверьте TTL
config.update_performance_config("cache_ttl", 1800)

# Отключите кэширование для отладки
config.update_performance_config("enable_caching", False)
```

## Заключение

Модуль производительности обеспечивает комплексную оптимизацию приложения, значительно улучшая скорость работы и эффективность использования ресурсов. Правильная настройка и мониторинг позволяют достичь оптимальной производительности для различных сценариев использования.
