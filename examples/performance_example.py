"""
Пример использования модуля производительности
"""
import time
import tempfile
from pathlib import Path
from typing import List

# Импорты для работы с производительностью
from src.core.performance import (
    PerformanceManager, PerformanceConfig, 
    cached, profiled
)
from src.core.configuration import Configuration


def create_test_files(directory: Path, count: int = 100) -> List[Path]:
    """Создает тестовые Python файлы"""
    files = []
    
    for i in range(count):
        file_path = directory / f"test_file_{i}.py"
        
        # Создаем файл с разными импортами
        content = f"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def test_function_{i}():
    print("Test function {i}")
    
if __name__ == "__main__":
    test_function_{i}()
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        files.append(file_path)
    
    return files


def simulate_file_scanning(file_paths: List[Path], 
                          performance_manager: PerformanceManager) -> List[str]:
    """Симулирует сканирование файлов с использованием производительности"""
    all_imports = []
    
    for i, file_path in enumerate(file_paths):
        # Профилирование сканирования отдельного файла
        performance_manager.start_profiling(f"scan_file_{i}")
        
        # Симуляция чтения файла
        time.sleep(0.001)  # Имитация I/O
        
        # Генерация ключа кэша
        cache_key = performance_manager.generate_cache_key(
            "simulate_scan", str(file_path), file_path.stat().st_mtime
        )
        
        # Попытка получить из кэша
        cached_result = performance_manager.get_cached_result(cache_key)
        if cached_result is not None:
            all_imports.extend(cached_result)
            performance_manager.end_profiling(f"scan_file_{i}")
            continue
        
        # Симуляция парсинга импортов
        imports = [
            "os", "sys", "numpy", "pandas", 
            "pathlib", "matplotlib", "plt"
        ]
        
        # Кэширование результата
        performance_manager.cache_result(cache_key, imports)
        all_imports.extend(imports)
        
        # Завершение профилирования
        duration = performance_manager.end_profiling(f"scan_file_{i}")
        
        # Оптимизация памяти каждые 20 файлов
        if i % 20 == 0:
            performance_manager.optimize_memory()
        
        # Логирование прогресса
        if i % 10 == 0:
            print(f"Обработано файлов: {i + 1}/{len(file_paths)}")
    
    return all_imports


@cached(manager=None)  # Будет установлен позже
def expensive_parsing_operation(content: str, file_path: str) -> List[str]:
    """Дорогая операция парсинга (симуляция)"""
    # Симуляция сложного парсинга
    time.sleep(0.01)
    
    # Извлекаем импорты из содержимого
    imports = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('import '):
            lib = line.split('import ')[1].split()[0]
            imports.append(lib)
        elif line.startswith('from '):
            parts = line.split('import ')[0].split()
            if len(parts) >= 2:
                lib = parts[1]
                imports.append(lib)
    
    return list(set(imports))


@profiled(manager=None)  # Будет установлен позже
def analyze_project_structure(directory: Path) -> dict:
    """Анализ структуры проекта с профилированием"""
    # Симуляция анализа структуры
    time.sleep(0.1)
    
    return {
        'total_files': len(list(directory.rglob('*.py'))),
        'total_directories': len([d for d in directory.iterdir() if d.is_dir()]),
        'project_size': sum(f.stat().st_size for f in directory.rglob('*.py'))
    }


def demonstrate_caching(performance_manager: PerformanceManager):
    """Демонстрация работы кэширования"""
    print("\n=== ДЕМОНСТРАЦИЯ КЭШИРОВАНИЯ ===")
    
    # Тестовые данные
    test_data = [
        ("file1.py", "import numpy\nimport pandas"),
        ("file2.py", "import matplotlib\nimport seaborn"),
        ("file1.py", "import numpy\nimport pandas"),  # Дубликат для демонстрации кэша
    ]
    
    for file_path, content in test_data:
        print(f"\nОбработка файла: {file_path}")
        
        # Генерация ключа кэша
        cache_key = performance_manager.generate_cache_key(
            "parse_content", file_path, hash(content)
        )
        
        # Попытка получить из кэша
        cached_result = performance_manager.get_cached_result(cache_key)
        if cached_result is not None:
            print(f"  ✓ Результат найден в кэше: {cached_result}")
            continue
        
        # Симуляция парсинга
        print(f"  ⚙️  Выполняется парсинг...")
        time.sleep(0.01)
        
        # Извлечение импортов
        imports = []
        for line in content.split('\n'):
            if line.startswith('import '):
                lib = line.split('import ')[1]
                imports.append(lib)
        
        # Кэширование результата
        performance_manager.cache_result(cache_key, imports)
        print(f"  ✓ Результат сохранен в кэш: {imports}")
    
    print(f"\nРазмер кэша: {performance_manager.cache.size()}")


def demonstrate_profiling(performance_manager: PerformanceManager):
    """Демонстрация работы профилирования"""
    print("\n=== ДЕМОНСТРАЦИЯ ПРОФИЛИРОВАНИЯ ===")
    
    # Профилирование различных операций
    operations = [
        ("file_reading", 0.02),
        ("ast_parsing", 0.05),
        ("import_extraction", 0.01),
        ("data_processing", 0.03)
    ]
    
    for operation_name, duration in operations:
        print(f"\nПрофилирование операции: {operation_name}")
        
        performance_manager.start_profiling(operation_name)
        
        # Симуляция операции
        time.sleep(duration)
        
        # Завершение профилирования
        actual_duration = performance_manager.end_profiling(operation_name)
        print(f"  Время выполнения: {actual_duration:.3f}с")
    
    # Получение статистики
    stats = performance_manager.profiler.get_statistics()
    
    print("\nСтатистика профилирования:")
    for operation, metrics in stats.items():
        print(f"  {operation}:")
        print(f"    Количество вызовов: {metrics['count']}")
        print(f"    Среднее время: {metrics['average']:.3f}с")
        print(f"    Минимальное время: {metrics['min']:.3f}с")
        print(f"    Максимальное время: {metrics['max']:.3f}с")


def demonstrate_memory_optimization(performance_manager: PerformanceManager):
    """Демонстрация оптимизации памяти"""
    print("\n=== ДЕМОНСТРАЦИЯ ОПТИМИЗАЦИИ ПАМЯТИ ===")
    
    # Проверка текущего использования памяти
    memory_info = performance_manager.get_memory_usage()
    print(f"Текущее использование памяти: {memory_info['rss']:.1f} MB")
    print(f"Доступная память: {memory_info['available']:.1f} MB")
    
    # Симуляция обработки файлов с оптимизацией памяти
    for i in range(50):
        # Симуляция обработки файла
        time.sleep(0.001)
        
        # Оптимизация памяти
        performance_manager.optimize_memory()
        
        if i % 10 == 0:
            print(f"Обработано файлов: {i + 1}, выполняется оптимизация памяти...")
    
    # Проверка памяти после оптимизации
    memory_info_after = performance_manager.get_memory_usage()
    print(f"Использование памяти после оптимизации: {memory_info_after['rss']:.1f} MB")


def demonstrate_thread_optimization(performance_manager: PerformanceManager):
    """Демонстрация оптимизации потоков"""
    print("\n=== ДЕМОНСТРАЦИЯ ОПТИМИЗАЦИИ ПОТОКОВ ===")
    
    # Тестирование с разным количеством файлов
    test_scenarios = [
        (50, "небольшой проект"),
        (500, "средний проект"),
        (2000, "крупный проект")
    ]
    
    for file_count, description in test_scenarios:
        print(f"\n{description} ({file_count} файлов):")
        
        # Получение оптимальных параметров
        optimal_threads = performance_manager.get_optimal_threads(file_count)
        chunk_size = performance_manager.get_chunk_size(file_count, optimal_threads)
        
        print(f"  Оптимальное количество потоков: {optimal_threads}")
        print(f"  Размер чанка: {chunk_size}")
        
        # Симуляция обработки
        start_time = time.time()
        for i in range(0, file_count, chunk_size):
            # Симуляция обработки чанка
            time.sleep(0.001 * min(chunk_size, file_count - i))
        
        processing_time = time.time() - start_time
        
        # Запись производительности для адаптации
        performance_manager.thread_optimizer.record_performance(
            optimal_threads, processing_time
        )
        
        print(f"  Время обработки: {processing_time:.3f}с")
        print(f"  Скорость: {file_count / processing_time:.1f} файлов/сек")


def demonstrate_decorators(performance_manager: PerformanceManager):
    """Демонстрация работы декораторов"""
    print("\n=== ДЕМОНСТРАЦИЯ ДЕКОРАТОРОВ ===")
    
    # Установка менеджера для декораторов
    global expensive_parsing_operation, analyze_project_structure
    
    # Обновляем декораторы с менеджером
    expensive_parsing_operation = cached(performance_manager)(expensive_parsing_operation)
    analyze_project_structure = profiled(performance_manager)(analyze_project_structure)
    
    # Тестирование кэширующего декоратора
    print("\nТестирование @cached декоратора:")
    
    content1 = "import numpy\nimport pandas\nimport matplotlib"
    content2 = "import os\nimport sys\nimport json"
    
    # Первые вызовы (без кэша)
    print("  Первый вызов с content1...")
    result1_1 = expensive_parsing_operation(content1, "test1.py")
    print(f"  Результат: {result1_1}")
    
    print("  Первый вызов с content2...")
    result2_1 = expensive_parsing_operation(content2, "test2.py")
    print(f"  Результат: {result2_1}")
    
    # Повторные вызовы (из кэша)
    print("  Повторный вызов с content1 (из кэша)...")
    result1_2 = expensive_parsing_operation(content1, "test1.py")
    print(f"  Результат: {result1_2}")
    
    print("  Повторный вызов с content2 (из кэша)...")
    result2_2 = expensive_parsing_operation(content2, "test2.py")
    print(f"  Результат: {result2_2}")
    
    # Тестирование профилирующего декоратора
    print("\nТестирование @profiled декоратора:")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Создаем тестовые файлы
        for i in range(5):
            (temp_path / f"test_{i}.py").write_text(f"import module_{i}")
        
        print("  Анализ структуры проекта...")
        structure = analyze_project_structure(temp_path)
        print(f"  Результат: {structure}")


def generate_performance_report(performance_manager: PerformanceManager):
    """Генерация отчета о производительности"""
    print("\n=== ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ ===")
    
    # Получение полного отчета
    report = performance_manager.get_performance_report()
    
    # Вывод информации о кэше
    cache_info = report['cache']
    print(f"\nКэш:")
    print(f"  Размер: {cache_info['size']}/{cache_info['max_size']}")
    print(f"  Заполненность: {cache_info['size'] / cache_info['max_size'] * 100:.1f}%")
    
    # Вывод информации о памяти
    memory_info = report['memory']
    print(f"\nПамять:")
    print(f"  Использование RSS: {memory_info['rss']:.1f} MB")
    print(f"  Использование VMS: {memory_info['vms']:.1f} MB")
    print(f"  Процент использования: {memory_info['percent']:.1f}%")
    print(f"  Доступная память: {memory_info['available']:.1f} MB")
    
    # Вывод информации о профилировании
    profiling_info = report['profiling']
    if profiling_info:
        print(f"\nПрофилирование:")
        for operation, stats in profiling_info.items():
            print(f"  {operation}:")
            print(f"    Вызовов: {stats['count']}")
            print(f"    Среднее время: {stats['average']:.3f}с")
            print(f"    Общее время: {stats['total']:.3f}с")
    
    # Вывод конфигурации
    config_info = report['config']
    print(f"\nКонфигурация:")
    print(f"  Кэширование: {'включено' if config_info['enable_caching'] else 'выключено'}")
    print(f"  Профилирование: {'включено' if config_info['enable_profiling'] else 'выключено'}")
    print(f"  Оптимизация памяти: {'включена' if config_info['enable_memory_optimization'] else 'выключена'}")
    print(f"  Адаптивные потоки: {'включены' if config_info['adaptive_threading'] else 'выключены'}")


def main():
    """Главная функция демонстрации"""
    print("🚀 ДЕМОНСТРАЦИЯ МОДУЛЯ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 50)
    
    # Создание конфигурации производительности
    config = PerformanceConfig(
        enable_caching=True,
        enable_profiling=True,
        enable_memory_optimization=True,
        cache_size=500,
        gc_threshold=20,
        adaptive_threading=True,
        detailed_profiling=True
    )
    
    # Создание менеджера производительности
    performance_manager = PerformanceManager(config)
    
    try:
        # Демонстрация различных возможностей
        demonstrate_caching(performance_manager)
        demonstrate_profiling(performance_manager)
        demonstrate_memory_optimization(performance_manager)
        demonstrate_thread_optimization(performance_manager)
        demonstrate_decorators(performance_manager)
        
        # Создание тестовых файлов и симуляция сканирования
        print("\n=== СИМУЛЯЦИЯ СКАНИРОВАНИЯ ФАЙЛОВ ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создание тестовых файлов
            print("Создание тестовых файлов...")
            test_files = create_test_files(temp_path, 50)
            print(f"Создано {len(test_files)} тестовых файлов")
            
            # Симуляция сканирования
            print("Начало сканирования...")
            start_time = time.time()
            
            imports = simulate_file_scanning(test_files, performance_manager)
            
            scan_time = time.time() - start_time
            
            print(f"Сканирование завершено за {scan_time:.3f}с")
            print(f"Найдено уникальных импортов: {len(set(imports))}")
            print(f"Общее количество импортов: {len(imports)}")
        
        # Генерация отчета
        generate_performance_report(performance_manager)
        
        # Сохранение данных производительности
        performance_manager.save_performance_data()
        print(f"\nДанные производительности сохранены в: {config.profile_file}")
        
    except Exception as e:
        print(f"Ошибка при демонстрации: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очистка ресурсов
        performance_manager.clear_cache()
        performance_manager.reset_profiler()
        print("\nРесурсы очищены")


if __name__ == "__main__":
    main()
