"""
Модуль сканера файлов
"""
import time
import datetime
from typing import List, Dict, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import os

from .interfaces import IFileScanner, ScanResult, ImportData, ProjectData
from .import_parser import ImportParser
from .project_analyzer import ProjectAnalyzer
from .configuration import Configuration


class FileScanner(IFileScanner):
    """Сканер файлов с оптимизированной производительностью"""
    
    def __init__(self, config: Configuration, 
                 import_parser: ImportParser,
                 project_analyzer: ProjectAnalyzer):
        self.config = config
        self.import_parser = import_parser
        self.project_analyzer = project_analyzer
        self._excluded_dirs = config.get_excluded_directories()
        self._max_file_size = config.get_max_file_size()
        self._batch_size = config.get_batch_size()
        self._max_workers = config.get_max_workers()
        self._supported_encodings = config.get_supported_encodings()
    
    def scan_directory(self, directory: Path, 
                      progress_callback=None) -> ScanResult:
        """
        Сканирует директорию и возвращает результаты
        
        Args:
            directory: Директория для сканирования
            progress_callback: Функция обратного вызова для прогресса
            
        Returns:
            Результат сканирования
        """
        start_time = time.time()
        
        if progress_callback:
            progress_callback("Поиск Python файлов...")
        
        # Поиск всех Python файлов
        file_paths = self._find_python_files(directory)
        
        if progress_callback:
            progress_callback(f"Найдено {len(file_paths)} файлов для обработки...")
        
        if not file_paths:
            return self._create_empty_result(start_time)
        
        # Сканирование файлов
        all_imports = self._scan_files_parallel(file_paths, progress_callback)
        
        # Анализ проектов
        if progress_callback:
            progress_callback("Анализ структуры проектов...")
        
        projects_data = self.project_analyzer.analyze_project_structure(directory)
        
        # Обновление данных проектов с импортами
        self._update_projects_with_imports(projects_data, all_imports)
        
        # Создание результата
        scan_duration = time.time() - start_time
        
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
        Сканирует один файл и возвращает список импортов
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Список найденных библиотек
        """
        try:
            # Проверка размера файла
            if file_path.stat().st_size > self._max_file_size:
                return []
            
            # Чтение файла с поддержкой разных кодировок
            content = self._read_file_content(file_path)
            if not content:
                return []
            
            # Парсинг импортов
            return self.import_parser.parse_imports(content, file_path)
            
        except Exception:
            return []
    
    def _find_python_files(self, directory: Path) -> List[Path]:
        """
        Находит все Python файлы в директории
        
        Args:
            directory: Корневая директория
            
        Returns:
            Список путей к Python файлам
        """
        file_paths = []
        
        for root, dirs, files in os.walk(directory):
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if d not in self._excluded_dirs]
            
            # Поиск Python файлов
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
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
                           progress_callback=None) -> Dict[str, int]:
        """
        Сканирует файлы параллельно
        
        Args:
            file_paths: Список путей к файлам
            progress_callback: Функция обратного вызова
            
        Returns:
            Словарь с количеством импортов по библиотекам
        """
        all_imports = []
        
        # Создание батчей
        batches = [file_paths[i:i + self._batch_size] 
                  for i in range(0, len(file_paths), self._batch_size)]
        
        if progress_callback:
            progress_callback(f"Запуск {self._max_workers} потоков...")
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {executor.submit(self._process_batch, batch): i 
                      for i, batch in enumerate(batches)}
            
            processed_batches = 0
            for future in as_completed(futures):
                batch_imports = future.result()
                all_imports.extend(batch_imports)
                
                processed_batches += 1
                if progress_callback and processed_batches % 5 == 0:
                    processed_files = processed_batches * self._batch_size
                    progress_callback(f"Обработано {min(processed_files, len(file_paths))}/{len(file_paths)} файлов...")
        
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
        batch_imports = []
        
        for file_path in file_batch:
            imports = self.scan_file(file_path)
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
        project_imports = {}
        
        for project in projects_data:
            project_imports[project.name] = set()
        
        # Здесь можно добавить логику для определения,
        # какие импорты принадлежат каким проектам
        # Пока просто распределяем равномерно
        
        total_projects = len(projects_data)
        if total_projects > 0:
            imports_per_project = len(all_imports) // total_projects
            
            for i, project in enumerate(projects_data):
                start_idx = i * imports_per_project
                end_idx = start_idx + imports_per_project if i < total_projects - 1 else len(all_imports)
                
                project_libraries = list(all_imports.keys())[start_idx:end_idx]
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
        total_imports = sum(imports_counter.values())
        
        imports_data = {}
        for library, count in imports_counter.items():
            percentage = (count / total_imports * 100) if total_imports > 0 else 0
            
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
