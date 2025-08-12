"""
Тесты для модуля производительности
"""
import unittest
import tempfile
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Импорты для тестирования
from src.core.performance import (
    PerformanceConfig, LRUCache, PerformanceProfiler, 
    MemoryOptimizer, ThreadOptimizer, PerformanceManager
)


class TestPerformanceConfig(unittest.TestCase):
    """Тесты для конфигурации производительности"""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        config = PerformanceConfig()
        
        self.assertTrue(config.enable_caching)
        self.assertEqual(config.cache_size, 1000)
        self.assertEqual(config.cache_ttl, 3600)
        self.assertTrue(config.enable_memory_optimization)
        self.assertTrue(config.enable_profiling)
        self.assertTrue(config.adaptive_threading)
    
    def test_custom_config(self):
        """Тест пользовательской конфигурации"""
        config = PerformanceConfig(
            enable_caching=False,
            cache_size=500,
            enable_profiling=False
        )
        
        self.assertFalse(config.enable_caching)
        self.assertEqual(config.cache_size, 500)
        self.assertFalse(config.enable_profiling)


class TestLRUCache(unittest.TestCase):
    """Тесты для LRU кэша"""
    
    def setUp(self):
        self.cache = LRUCache(max_size=3, ttl=1)
    
    def test_basic_operations(self):
        """Тест основных операций кэша"""
        # Добавление элементов
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        # Получение элементов
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertIsNone(self.cache.get("key3"))
    
    def test_lru_eviction(self):
        """Тест вытеснения по LRU"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        self.cache.put("key4", "value4")  # Должен вытеснить key1
        
        self.assertIsNone(self.cache.get("key1"))
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.get("key3"), "value3")
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_ttl_expiration(self):
        """Тест истечения TTL"""
        self.cache.put("key1", "value1")
        
        # Элемент должен быть доступен
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Ждем истечения TTL
        time.sleep(1.1)
        
        # Элемент должен быть удален
        self.assertIsNone(self.cache.get("key1"))
    
    def test_size_method(self):
        """Тест метода размера кэша"""
        self.assertEqual(self.cache.size(), 0)
        
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.size(), 1)
        
        self.cache.put("key2", "value2")
        self.assertEqual(self.cache.size(), 2)
    
    def test_clear_method(self):
        """Тест очистки кэша"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        self.assertEqual(self.cache.size(), 2)
        
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key1"))


class TestPerformanceProfiler(unittest.TestCase):
    """Тесты для профилировщика производительности"""
    
    def setUp(self):
        self.config = PerformanceConfig(profile_file="test_profile.json")
        self.profiler = PerformanceProfiler(self.config)
    
    def test_timer_operations(self):
        """Тест операций таймера"""
        self.profiler.start_timer("test_operation")
        time.sleep(0.1)
        duration = self.profiler.end_timer("test_operation")
        
        self.assertGreater(duration, 0.09)
        self.assertLess(duration, 0.2)
    
    def test_add_metric(self):
        """Тест добавления метрик"""
        self.profiler.add_metric("test_metric", 1.5)
        self.profiler.add_metric("test_metric", 2.5)
        
        stats = self.profiler.get_statistics()
        self.assertIn("test_metric", stats)
        self.assertEqual(stats["test_metric"]["count"], 2)
        self.assertEqual(stats["test_metric"]["average"], 2.0)
    
    def test_get_statistics(self):
        """Тест получения статистики"""
        # Добавляем несколько метрик
        self.profiler.add_metric("metric1", 1.0)
        self.profiler.add_metric("metric1", 3.0)
        self.profiler.add_metric("metric2", 2.0)
        
        stats = self.profiler.get_statistics()
        
        self.assertIn("metric1", stats)
        self.assertIn("metric2", stats)
        self.assertEqual(stats["metric1"]["count"], 2)
        self.assertEqual(stats["metric1"]["average"], 2.0)
        self.assertEqual(stats["metric1"]["min"], 1.0)
        self.assertEqual(stats["metric1"]["max"], 3.0)
    
    def test_reset(self):
        """Тест сброса профилировщика"""
        self.profiler.add_metric("test_metric", 1.0)
        self.profiler.start_timer("test_timer")
        
        self.profiler.reset()
        
        stats = self.profiler.get_statistics()
        self.assertEqual(len(stats), 0)
        
        # Таймер должен быть сброшен
        duration = self.profiler.end_timer("test_timer")
        self.assertEqual(duration, 0.0)


class TestMemoryOptimizer(unittest.TestCase):
    """Тесты для оптимизатора памяти"""
    
    def setUp(self):
        self.config = PerformanceConfig()
        self.optimizer = MemoryOptimizer(self.config)
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    def test_check_memory_usage(self, mock_virtual_memory, mock_process):
        """Тест проверки использования памяти"""
        # Мокаем psutil
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = Mock(rss=1024*1024*100, vms=1024*1024*200)
        mock_process_instance.memory_percent.return_value = 25.0
        mock_process.return_value = mock_process_instance
        
        mock_virtual_memory.return_value = Mock(available=1024*1024*1000)
        
        memory_info = self.optimizer.check_memory_usage()
        
        self.assertIn('rss', memory_info)
        self.assertIn('vms', memory_info)
        self.assertIn('percent', memory_info)
        self.assertIn('available', memory_info)
        self.assertEqual(memory_info['rss'], 100.0)  # MB
        self.assertEqual(memory_info['vms'], 200.0)  # MB
        self.assertEqual(memory_info['percent'], 25.0)
        self.assertEqual(memory_info['available'], 1000.0)  # MB
    
    def test_should_gc(self):
        """Тест определения необходимости сборки мусора"""
        # Первые 99 вызовов должны возвращать False
        for i in range(99):
            self.assertFalse(self.optimizer.should_gc())
        
        # 100-й вызов должен возвращать True
        self.assertTrue(self.optimizer.should_gc())


class TestThreadOptimizer(unittest.TestCase):
    """Тесты для оптимизатора потоков"""
    
    def setUp(self):
        self.config = PerformanceConfig()
        self.optimizer = ThreadOptimizer(self.config)
    
    @patch('os.cpu_count')
    def test_get_optimal_thread_count(self, mock_cpu_count):
        """Тест определения оптимального количества потоков"""
        mock_cpu_count.return_value = 8
        
        # Тест с небольшим количеством файлов
        threads = self.optimizer.get_optimal_thread_count(50, 2048)
        self.assertEqual(threads, 4)  # cpu_count // 2
        
        # Тест с большим количеством файлов
        threads = self.optimizer.get_optimal_thread_count(2000, 2048)
        self.assertEqual(threads, 16)  # cpu_count * 2
        
        # Тест с ограниченной памятью
        threads = self.optimizer.get_optimal_thread_count(1000, 512)
        self.assertEqual(threads, 4)  # (cpu_count // 2) // 2
    
    def test_get_chunk_size(self):
        """Тест определения размера чанка"""
        # Тест с фиксированным размером
        self.config.thread_chunk_size = 50
        chunk_size = self.optimizer.get_chunk_size(1000, 8)
        self.assertEqual(chunk_size, 50)
        
        # Тест с адаптивным размером
        self.config.thread_chunk_size = 0
        chunk_size = self.optimizer.get_chunk_size(1000, 8)
        self.assertGreater(chunk_size, 0)
        self.assertLessEqual(chunk_size, 200)
    
    def test_record_performance(self):
        """Тест записи производительности"""
        self.optimizer.record_performance(8, 1.5)
        self.optimizer.record_performance(16, 1.2)
        
        self.assertEqual(len(self.optimizer.performance_history), 2)
        self.assertEqual(self.optimizer.performance_history[0], (8, 1.5))
        self.assertEqual(self.optimizer.performance_history[1], (16, 1.2))


class TestPerformanceManager(unittest.TestCase):
    """Тесты для менеджера производительности"""
    
    def setUp(self):
        self.config = PerformanceConfig(
            enable_caching=True,
            enable_profiling=True,
            enable_memory_optimization=True
        )
        self.manager = PerformanceManager(self.config)
    
    def test_cache_operations(self):
        """Тест операций кэша"""
        # Кэширование результата
        self.manager.cache_result("test_key", "test_value")
        
        # Получение из кэша
        result = self.manager.get_cached_result("test_key")
        self.assertEqual(result, "test_value")
        
        # Получение несуществующего ключа
        result = self.manager.get_cached_result("nonexistent_key")
        self.assertIsNone(result)
    
    def test_profiling_operations(self):
        """Тест операций профилирования"""
        self.manager.start_profiling("test_operation")
        time.sleep(0.1)
        duration = self.manager.end_profiling("test_operation")
        
        self.assertGreater(duration, 0.09)
        self.assertLess(duration, 0.2)
    
    def test_generate_cache_key(self):
        """Тест генерации ключа кэша"""
        key1 = self.manager.generate_cache_key("func", "arg1", "arg2")
        key2 = self.manager.generate_cache_key("func", "arg1", "arg2")
        key3 = self.manager.generate_cache_key("func", "arg1", "arg3")
        
        # Одинаковые аргументы должны давать одинаковые ключи
        self.assertEqual(key1, key2)
        
        # Разные аргументы должны давать разные ключи
        self.assertNotEqual(key1, key3)
    
    def test_get_performance_report(self):
        """Тест получения отчета о производительности"""
        # Добавляем некоторые данные
        self.manager.cache_result("test_key", "test_value")
        self.manager.start_profiling("test_operation")
        time.sleep(0.01)
        self.manager.end_profiling("test_operation")
        
        report = self.manager.get_performance_report()
        
        self.assertIn('cache', report)
        self.assertIn('memory', report)
        self.assertIn('profiling', report)
        self.assertIn('config', report)
        
        self.assertEqual(report['cache']['size'], 1)
        self.assertIn('test_operation', report['profiling'])
    
    def test_clear_cache(self):
        """Тест очистки кэша"""
        self.manager.cache_result("test_key", "test_value")
        self.assertEqual(self.manager.cache.size(), 1)
        
        self.manager.clear_cache()
        self.assertEqual(self.manager.cache.size(), 0)
    
    def test_reset_profiler(self):
        """Тест сброса профилировщика"""
        self.manager.add_metric("test_metric", 1.0)
        
        report_before = self.manager.get_performance_report()
        self.assertIn('test_metric', report_before['profiling'])
        
        self.manager.reset_profiler()
        
        report_after = self.manager.get_performance_report()
        self.assertEqual(len(report_after['profiling']), 0)


class TestPerformanceIntegration(unittest.TestCase):
    """Интеграционные тесты производительности"""
    
    def setUp(self):
        self.config = PerformanceConfig(
            enable_caching=True,
            enable_profiling=True,
            enable_memory_optimization=True,
            cache_size=100,
            gc_threshold=10
        )
        self.manager = PerformanceManager(self.config)
    
    def test_full_workflow(self):
        """Тест полного рабочего процесса"""
        # Симуляция сканирования файлов
        for i in range(20):
            # Кэширование результатов
            self.manager.cache_result(f"file_{i}", f"imports_{i}")
            
            # Профилирование
            self.manager.start_profiling(f"scan_file_{i}")
            time.sleep(0.01)
            self.manager.end_profiling(f"scan_file_{i}")
            
            # Оптимизация памяти
            self.manager.optimize_memory()
        
        # Проверка результатов
        report = self.manager.get_performance_report()
        
        self.assertEqual(report['cache']['size'], 20)
        self.assertIn('scan_file_0', report['profiling'])
        self.assertIn('scan_file_19', report['profiling'])
    
    def test_memory_optimization_workflow(self):
        """Тест процесса оптимизации памяти"""
        # Симуляция обработки файлов
        for i in range(15):
            self.manager.optimize_memory()
        
        # Проверка, что сборка мусора была вызвана
        # (это сложно проверить напрямую, но мы можем убедиться, что нет ошибок)
        memory_info = self.manager.get_memory_usage()
        self.assertIsInstance(memory_info, dict)
        self.assertIn('rss', memory_info)


if __name__ == '__main__':
    unittest.main()
