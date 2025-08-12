"""
Модуль оптимизации производительности - кэширование и оптимизация
"""
import time
import threading
import functools
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
import psutil
import gc

from .logging_config import get_logger


@dataclass
class PerformanceConfig:
    """Конфигурация производительности"""
    # Кэширование
    enable_caching: bool = True
    cache_size: int = 1000
    cache_ttl: int = 3600  # 1 час
    cache_file: str = "cache/performance_cache.json"
    
    # Оптимизация памяти
    enable_memory_optimization: bool = True
    gc_threshold: int = 100  # Количество файлов до сборки мусора
    memory_check_interval: int = 50  # Проверка памяти каждые N файлов
    
    # Профилирование
    enable_profiling: bool = True
    profile_file: str = "logs/performance_profile.json"
    detailed_profiling: bool = False
    
    # Оптимизация потоков
    optimal_threads: int = 0  # 0 = автоопределение
    thread_chunk_size: int = 100
    adaptive_threading: bool = True
    
    # Кэширование результатов
    cache_imports: bool = True
    cache_file_hashes: bool = True
    cache_directory_structure: bool = True


class LRUCache:
    """LRU кэш с TTL"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Получает значение из кэша"""
        with self.lock:
            if key in self.cache:
                # Проверка TTL
                if time.time() - self.timestamps[key] > self.ttl:
                    del self.cache[key]
                    del self.timestamps[key]
                    return None
                
                # Перемещаем в конец (LRU)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Добавляет значение в кэш"""
        with self.lock:
            if key in self.cache:
                # Обновляем существующий
                self.cache.move_to_end(key)
            else:
                # Проверяем размер кэша
                if len(self.cache) >= self.max_size:
                    # Удаляем самый старый элемент
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Очищает кэш"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Возвращает размер кэша"""
        with self.lock:
            return len(self.cache)


class PerformanceProfiler:
    """Профилировщик производительности"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = get_logger("PerformanceProfiler")
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.start_times: Dict[str, float] = {}
        self.lock = threading.RLock()
        
        # Создаем директорию для профилей
        profile_dir = Path(self.config.profile_file).parent
        profile_dir.mkdir(parents=True, exist_ok=True)
    
    def start_timer(self, name: str) -> None:
        """Запускает таймер для метрики"""
        with self.lock:
            self.start_times[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """Останавливает таймер и возвращает время"""
        with self.lock:
            if name in self.start_times:
                duration = time.time() - self.start_times[name]
                self.metrics[name].append(duration)
                del self.start_times[name]
                return duration
            return 0.0
    
    def add_metric(self, name: str, value: float) -> None:
        """Добавляет метрику"""
        with self.lock:
            self.metrics[name].append(value)
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Возвращает статистику по метрикам"""
        stats = {}
        with self.lock:
            for name, values in self.metrics.items():
                if values:
                    stats[name] = {
                        'count': len(values),
                        'total': sum(values),
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'last': values[-1]
                    }
        return stats
    
    def save_profile(self) -> None:
        """Сохраняет профиль в файл"""
        try:
            stats = self.get_statistics()
            profile_data = {
                'timestamp': time.time(),
                'config': self.config.__dict__,
                'statistics': stats
            }
            
            with open(self.config.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Профиль производительности сохранен", 
                           extra_data={"file": self.config.profile_file})
            
        except Exception as e:
            self.logger.error("Ошибка сохранения профиля", 
                            extra_data={"error": str(e)})
    
    def reset(self) -> None:
        """Сбрасывает все метрики"""
        with self.lock:
            self.metrics.clear()
            self.start_times.clear()


class MemoryOptimizer:
    """Оптимизатор памяти"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = get_logger("MemoryOptimizer")
        self.file_counter = 0
        self.last_memory_check = 0
        self.lock = threading.RLock()
    
    def check_memory_usage(self) -> Dict[str, float]:
        """Проверяет использование памяти"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent(),
                'available': psutil.virtual_memory().available / 1024 / 1024  # MB
            }
        except ImportError:
            return {'rss': 0, 'vms': 0, 'percent': 0, 'available': 0}
        except Exception as e:
            self.logger.error("Ошибка проверки памяти", 
                            extra_data={"error": str(e)})
            return {'rss': 0, 'vms': 0, 'percent': 0, 'available': 0}
    
    def should_gc(self) -> bool:
        """Определяет, нужно ли запустить сборку мусора"""
        with self.lock:
            self.file_counter += 1
            return self.file_counter % self.config.gc_threshold == 0
    
    def optimize_memory(self) -> None:
        """Выполняет оптимизацию памяти"""
        if self.should_gc():
            self.logger.debug("Запуск сборки мусора")
            gc.collect()
    
    def log_memory_usage(self) -> None:
        """Логирует использование памяти"""
        memory_info = self.check_memory_usage()
        self.logger.info("Использование памяти", extra_data=memory_info)


class ThreadOptimizer:
    """Оптимизатор потоков"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = get_logger("ThreadOptimizer")
        self.performance_history: List[Tuple[int, float]] = []
    
    def get_optimal_thread_count(self, file_count: int, 
                                available_memory: float) -> int:
        """Определяет оптимальное количество потоков"""
        if self.config.optimal_threads > 0:
            return min(self.config.optimal_threads, file_count)
        
        # Базовое количество потоков
        cpu_count = os.cpu_count() or 4
        
        # Адаптивная настройка
        if self.config.adaptive_threading:
            # Учитываем количество файлов
            if file_count < 100:
                threads = max(1, cpu_count // 2)
            elif file_count < 1000:
                threads = cpu_count
            else:
                threads = min(cpu_count * 2, 16)
            
            # Учитываем доступную память
            if available_memory < 1024:  # Меньше 1GB
                threads = max(1, threads // 2)
            elif available_memory > 8192:  # Больше 8GB
                threads = min(threads + 2, 20)
        else:
            threads = cpu_count
        
        return min(threads, file_count, 20)  # Максимум 20 потоков
    
    def get_chunk_size(self, file_count: int, thread_count: int) -> int:
        """Определяет размер чанка для обработки"""
        if self.config.thread_chunk_size > 0:
            return self.config.thread_chunk_size
        
        # Адаптивный размер чанка
        base_chunk = max(10, file_count // (thread_count * 4))
        return min(base_chunk, 200)  # Максимум 200 файлов в чанке
    
    def record_performance(self, thread_count: int, 
                          processing_time: float) -> None:
        """Записывает производительность для адаптации"""
        self.performance_history.append((thread_count, processing_time))
        
        # Оставляем только последние 10 записей
        if len(self.performance_history) > 10:
            self.performance_history.pop(0)


class PerformanceManager:
    """Менеджер производительности (фасад)"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.logger = get_logger("PerformanceManager")
        
        # Инициализация компонентов
        self.cache = LRUCache(self.config.cache_size, self.config.cache_ttl)
        self.profiler = PerformanceProfiler(self.config)
        self.memory_optimizer = MemoryOptimizer(self.config)
        self.thread_optimizer = ThreadOptimizer(self.config)
        
        # Создаем директории
        self._create_directories()
        
        self.logger.info("PerformanceManager инициализирован")
    
    def _create_directories(self) -> None:
        """Создает необходимые директории"""
        cache_dir = Path(self.config.cache_file).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        profile_dir = Path(self.config.profile_file).parent
        profile_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Получает результат из кэша"""
        if not self.config.enable_caching:
            return None
        
        result = self.cache.get(key)
        if result:
            self.logger.debug("Результат найден в кэше", 
                            extra_data={"key": key})
        return result
    
    def cache_result(self, key: str, value: Any) -> None:
        """Кэширует результат"""
        if not self.config.enable_caching:
            return
        
        self.cache.put(key, value)
        self.logger.debug("Результат сохранен в кэш", 
                         extra_data={"key": key})
    
    def start_profiling(self, name: str) -> None:
        """Запускает профилирование"""
        if self.config.enable_profiling:
            self.profiler.start_timer(name)
    
    def end_profiling(self, name: str) -> float:
        """Завершает профилирование"""
        if self.config.enable_profiling:
            return self.profiler.end_timer(name)
        return 0.0
    
    def optimize_memory(self) -> None:
        """Выполняет оптимизацию памяти"""
        if self.config.enable_memory_optimization:
            self.memory_optimizer.optimize_memory()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Возвращает информацию об использовании памяти"""
        return self.memory_optimizer.check_memory_usage()
    
    def get_optimal_threads(self, file_count: int) -> int:
        """Возвращает оптимальное количество потоков"""
        memory_info = self.get_memory_usage()
        return self.thread_optimizer.get_optimal_thread_count(
            file_count, memory_info['available']
        )
    
    def get_chunk_size(self, file_count: int, thread_count: int) -> int:
        """Возвращает оптимальный размер чанка"""
        return self.thread_optimizer.get_chunk_size(file_count, thread_count)
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Генерирует ключ кэша из аргументов"""
        # Создаем строку из аргументов
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        
        # Создаем хеш
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def save_performance_data(self) -> None:
        """Сохраняет данные производительности"""
        if self.config.enable_profiling:
            self.profiler.save_profile()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Возвращает отчет о производительности"""
        report = {
            'cache': {
                'size': self.cache.size(),
                'max_size': self.config.cache_size,
                'hit_rate': 0.0  # TODO: Реализовать подсчет hit rate
            },
            'memory': self.get_memory_usage(),
            'profiling': self.profiler.get_statistics() if self.config.enable_profiling else {},
            'config': self.config.__dict__
        }
        
        return report
    
    def clear_cache(self) -> None:
        """Очищает кэш"""
        self.cache.clear()
        self.logger.info("Кэш очищен")
    
    def reset_profiler(self) -> None:
        """Сбрасывает профилировщик"""
        self.profiler.reset()
        self.logger.info("Профилировщик сброшен")


# Декоратор для кэширования функций
def cached(manager: PerformanceManager, ttl: int = None):
    """Декоратор для кэширования результатов функций"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = manager.generate_cache_key(func.__name__, *args, **kwargs)
            
            # Пытаемся получить из кэша
            cached_result = manager.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Кэшируем результат
            manager.cache_result(cache_key, result)
            
            return result
        return wrapper
    return decorator


# Декоратор для профилирования функций
def profiled(manager: PerformanceManager):
    """Декоратор для профилирования функций"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler_name = f"{func.__module__}.{func.__name__}"
            
            manager.start_profiling(profiler_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = manager.end_profiling(profiler_name)
                if manager.config.detailed_profiling:
                    manager.logger.debug("Функция выполнена", 
                                       extra_data={
                                           "function": profiler_name,
                                           "duration": duration
                                       })
        return wrapper
    return decorator
