"""
Модуль сканера файлов
"""
import time
import datetime
from typing import List, Dict, Optional, Any, Callable, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from collections import Counter
import os

from .interfaces import IFileScanner, ScanResult, ImportData, ProjectData
from .import_parser import ImportParser
from .project_analyzer import ProjectAnalyzer
from .configuration import Configuration
from .logging_config import get_logger
from .security import SecurityManager, SecurityConfig
from .performance import PerformanceManager, PerformanceConfig


class FileScanner(IFileScanner):
    """Сканер файлов с оптимизированной производительностью"""
    
    def __init__(self, config: Configuration, 
                 import_parser: ImportParser,
                 project_analyzer: ProjectAnalyzer) -> None:
        self.config: Configuration = config
        self.import_parser: ImportParser = import_parser
        self.project_analyzer: ProjectAnalyzer = project_analyzer
        self._excluded_dirs: Set[str] = config.get_excluded_directories()
        self._max_file_size: int = config.get_max_file_size()
        self._batch_size: int = config.get_batch_size()
        self._max_workers: int = config.get_max_workers()
        self._supported_encodings: List[str] = config.get_supported_encodings()
        
        # Инициализация логгера
        self.logger = get_logger("FileScanner")
        
        # Инициализация безопасности
        security_config_dict: Dict[str, Any] = config.get_security_config()
        security_config: SecurityConfig = SecurityConfig(**security_config_dict)
        self.security_manager: SecurityManager = SecurityManager(security_config)
        
        # Инициализация производительности
        performance_config_dict: Dict[str, Any] = config.get_performance_config()
        performance_config: PerformanceConfig = PerformanceConfig(**performance_config_dict)
        self.performance_manager: PerformanceManager = PerformanceManager(performance_config)
        
        self.logger.info("FileScanner инициализирован", 
                        extra_data={
                            "max_workers": self._max_workers,
                            "batch_size": self._batch_size,
                            "max_file_size": self._max_file_size
                        })
    
    def scan_directory(self, directory: Path, 
                      progress_callback: Optional[Callable[[str, Optional[float]], None]] = None) -> ScanResult:
        """
        Сканирует директорию и возвращает результаты
        
        Args:
            directory: Директория для сканирования
            progress_callback: Функция обратного вызова для прогресса
            
        Returns:
            Результат сканирования
        """
        self.logger.info("Начало сканирования директории", 
                        extra_data={"directory": str(directory)})
        
        start_time: float = time.time()
        
        if progress_callback:
            progress_callback("Поиск Python файлов...")
        
        # Поиск всех Python файлов
        self.logger.info("Поиск Python файлов")
        file_paths: List[Path] = self._find_python_files(directory)
        
        self.logger.info("Поиск файлов завершен", 
                        extra_data={"files_found": len(file_paths)})
        
        if progress_callback:
            progress_callback(f"Найдено {len(file_paths)} файлов для обработки...")
        
        if not file_paths:
            self.logger.warning("Python файлы не найдены")
            return self._create_empty_result(start_time)
        
        # Сканирование файлов
        self.logger.info("Начало параллельного сканирования файлов")
        all_imports: Dict[str, int] = self._scan_files_parallel(file_paths, progress_callback)
        
        # Анализ проектов
        if progress_callback:
            progress_callback("Анализ структуры проектов...")
        
        self.logger.info("Анализ структуры проектов")
        projects_data: List[ProjectData] = self.project_analyzer.analyze_project_structure(directory)
        
        # Обновление данных проектов с импортами
        self._update_projects_with_imports(projects_data, all_imports)
        
        # Создание результата
        scan_duration: float = time.time() - start_time
        
        self.logger.info("Сканирование завершено", 
                        extra_data={
                            "total_files": len(file_paths),
                            "total_imports": sum(all_imports.values()),
                            "duration": scan_duration,
                            "projects_found": len(projects_data)
                        })
        
        return ScanResult(
            imports_data=self._create_imports_data(all_imports),
            projects_data=projects_data,
            total_files_scanned=len(file_paths),
            total_imports=sum(all_imports.values()),
            scan_duration=scan_duration,
            scan_timestamp=datetime.datetime.now()
        )
    
    def scan_file(self, file_path: Path) -> List[str]:
        """
        Сканирует один файл и возвращает список импортов с кэшированием
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Список найденных библиотек
        """
        # Генерация ключа кэша
        cache_key: str = self.performance_manager.generate_cache_key(
            "scan_file", str(file_path), file_path.stat().st_mtime
        )
        
        # Попытка получить из кэша
        cached_result: Optional[List[str]] = self.performance_manager.get_cached_result(cache_key)
        if cached_result is not None:
            self.logger.debug("Результат найден в кэше", 
                            extra_data={"file": str(file_path)})
            return cached_result
        
        try:
            # Валидация безопасности
            is_valid: bool
            message: str
            is_valid, message = self.security_manager.validate_file(file_path)
            if not is_valid:
                self.logger.warning("Файл не прошел валидацию безопасности", 
                                  extra_data={"file": str(file_path), "error": message})
                return []
            
            # Чтение файла с поддержкой разных кодировок
            content: Optional[str] = self._read_file_content(file_path)
            if not content:
                return []
            
            # Валидация и санитизация содержимого
            sanitized_content: str
            is_valid, message, sanitized_content = self.security_manager.validate_and_sanitize_content(content, file_path)
            if not is_valid:
                self.logger.warning("Содержимое файла не прошло валидацию", 
                                  extra_data={"file": str(file_path), "error": message})
                return []
            
            # Парсинг импортов
            imports: List[str] = self.import_parser.parse_imports(sanitized_content, file_path)
            
            # Валидация импортов
            is_valid, message = self.security_manager.validate_imports(imports, file_path)
            if not is_valid:
                self.logger.warning("Импорты не прошли валидацию", 
                                  extra_data={"file": str(file_path), "error": message})
                return []
            
            # Кэширование результата
            self.performance_manager.cache_result(cache_key, imports)
            
            return imports
            
        except Exception as e:
            self.logger.error("Ошибка сканирования файла", 
                            extra_data={"file": str(file_path), "error": str(e)})
            return []
    
    def _find_python_files(self, directory: Path) -> List[Path]:
        """
        Находит все Python файлы в директории
        
        Args:
            directory: Корневая директория
            
        Returns:
            Список путей к Python файлам
        """
        file_paths: List[Path] = []
        
        for root, dirs, files in os.walk(directory):
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if d not in self._excluded_dirs]
            
            # Поиск Python файлов
            for file in files:
                if file.endswith('.py'):
                    file_path: Path = Path(root) / file
                    file_paths.append(file_path)
        
        return file_paths
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """
        Читает содержимое файла с поддержкой разных кодировок
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Содержимое файла или None
        """
        for encoding in self._supported_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, IOError):
                continue
        
        return None
    
    def _scan_files_parallel(self, file_paths: List[Path], 
                           progress_callback: Optional[Callable[[str, Optional[float]], None]] = None) -> Dict[str, int]:
        """
        Сканирует файлы параллельно с оптимизацией производительности
        
        Args:
            file_paths: Список путей к файлам
            progress_callback: Функция обратного вызова
            
        Returns:
            Словарь с количеством импортов по библиотекам
        """
        # Запуск профилирования
        self.performance_manager.start_profiling("parallel_scan")
        
        # Получение оптимальных параметров
        optimal_threads: int = self.performance_manager.get_optimal_threads(len(file_paths))
        chunk_size: int = self.performance_manager.get_chunk_size(len(file_paths), optimal_threads)
        
        self.logger.info("Оптимизированное сканирование", 
                        extra_data={
                            "file_count": len(file_paths),
                            "optimal_threads": optimal_threads,
                            "chunk_size": chunk_size
                        })
        
        all_imports: List[str] = []
        
        # Создание батчей с оптимальным размером
        batches: List[List[Path]] = [file_paths[i:i + chunk_size] 
                  for i in range(0, len(file_paths), chunk_size)]
        
        if progress_callback:
            progress_callback(f"Запуск {optimal_threads} потоков...")
        
        with ThreadPoolExecutor(max_workers=optimal_threads) as executor:
            futures: Dict[Future[List[str]], int] = {executor.submit(self._process_batch, batch): i 
                      for i, batch in enumerate(batches)}
            
            processed_batches: int = 0
            for future in as_completed(futures):
                batch_imports: List[str] = future.result()
                all_imports.extend(batch_imports)
                
                processed_batches += 1
                
                # Оптимизация памяти
                self.performance_manager.optimize_memory()
                
                if progress_callback and processed_batches % 5 == 0:
                    processed_files: int = processed_batches * chunk_size
                    progress_callback(f"Обработано {min(processed_files, len(file_paths))}/{len(file_paths)} файлов...")
        
        # Завершение профилирования
        scan_duration: float = self.performance_manager.end_profiling("parallel_scan")
        
        self.logger.info("Параллельное сканирование завершено", 
                        extra_data={
                            "duration": scan_duration,
                            "files_per_second": len(file_paths) / scan_duration if scan_duration > 0 else 0
                        })
        
        # Подсчет результатов
        return dict(Counter(all_imports))
    
    def _process_batch(self, file_batch: List[Path]) -> List[str]:
        """
        Обрабатывает батч файлов
        
        Args:
            file_batch: Батч файлов
            
        Returns:
            Список всех импортов из батча
        """
        batch_imports: List[str] = []
        
        for file_path in file_batch:
            imports: List[str] = self.scan_file(file_path)
            batch_imports.extend(imports)
        
        return batch_imports
    
    def _update_projects_with_imports(self, projects_data: List[ProjectData], 
                                    all_imports: Dict[str, int]) -> None:
        """
        Обновляет данные проектов информацией об импортах
        
        Args:
            projects_data: Данные проектов
            all_imports: Словарь с импортами
        """
        # Группировка импортов по проектам
        project_imports: Dict[str, Set[str]] = {}
        
        for project in projects_data:
            project_imports[project.name] = set()
        
        # Здесь можно добавить логику для определения,
        # какие импорты принадлежат каким проектам
        # Пока просто распределяем равномерно
        
        total_projects: int = len(projects_data)
        if total_projects > 0:
            imports_per_project: int = len(all_imports) // total_projects
            
            for i, project in enumerate(projects_data):
                start_idx: int = i * imports_per_project
                end_idx: int = start_idx + imports_per_project if i < total_projects - 1 else len(all_imports)
                
                project_libraries: List[str] = list(all_imports.keys())[start_idx:end_idx]
                project.libraries = set(project_libraries)
                project.total_imports = sum(all_imports[lib] for lib in project_libraries)
                project.unique_libraries = len(project_libraries)
    
    def _create_imports_data(self, imports_counter: Dict[str, int]) -> Dict[str, ImportData]:
        """
        Создает структурированные данные об импортах
        
        Args:
            imports_counter: Счетчик импортов
            
        Returns:
            Словарь с данными об импортах
        """
        total_imports: int = sum(imports_counter.values())
        
        imports_data: Dict[str, ImportData] = {}
        for library, count in imports_counter.items():
            percentage: float = (count / total_imports * 100) if total_imports > 0 else 0
            
            imports_data[library] = ImportData(
                library=library,
                count=count,
                percentage=percentage,
                files=[]  # Можно добавить список файлов, где используется библиотека
            )
        
        return imports_data
    
    def _create_empty_result(self, start_time: float) -> ScanResult:
        """
        Создает пустой результат сканирования
        
        Args:
            start_time: Время начала сканирования
            
        Returns:
            Пустой результат
        """
        return ScanResult(
            imports_data={},
            projects_data=[],
            total_files_scanned=0,
            total_imports=0,
            scan_duration=time.time() - start_time,
            scan_timestamp=datetime.datetime.now()
        )
