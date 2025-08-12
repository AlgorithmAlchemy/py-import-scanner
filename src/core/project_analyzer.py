"""
Модуль анализатора проектов
"""
import os
import datetime
from typing import List, Set, Optional
from pathlib import Path
from .interfaces import IProjectAnalyzer, ProjectData
from .configuration import Configuration


class ProjectAnalyzer(IProjectAnalyzer):
    """Анализатор структуры проектов"""
    
    def __init__(self, config: Configuration):
        self.config = config
        self._excluded_dirs = config.get_excluded_directories()
        self._max_depth = config.get_max_depth()
    
    def analyze_project_structure(self, directory: Path) -> List[ProjectData]:
        """
        Анализирует структуру проекта
        
        Args:
            directory: Корневая директория для анализа
            
        Returns:
            Список данных о проектах
        """
        projects = []
        
        for root, dirs, files in os.walk(directory):
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if not self._is_excluded_directory(d)]
            
            # Проверка глубины
            rel_path = Path(root).relative_to(directory)
            if rel_path.parts and len(rel_path.parts) > self._max_depth:
                continue
            
            # Поиск Python файлов
            py_files = [f for f in files if f.endswith('.py')]
            if not py_files:
                continue
            
            # Создание данных проекта
            project_data = self._create_project_data(
                directory, Path(root), py_files
            )
            if project_data:
                projects.append(project_data)
        
        return projects
    
    def find_projects(self, root_directory: Path) -> List[Path]:
        """
        Находит все проекты в директории
        
        Args:
            root_directory: Корневая директория
            
        Returns:
            Список путей к проектам
        """
        projects = []
        visited = set()
        
        for root, dirs, files in os.walk(root_directory):
            # Пропускаем уже посещенные директории
            if any(str(Path(root)).startswith(p) for p in visited):
                continue
            
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if not self._is_excluded_directory(d)]
            
            # Проверка на наличие Python файлов
            if any(f.endswith('.py') for f in files):
                project_path = Path(root)
                projects.append(project_path)
                visited.add(str(project_path))
        
        return projects
    
    def _is_excluded_directory(self, dir_name: str) -> bool:
        """
        Проверяет, должна ли директория быть исключена
        
        Args:
            dir_name: Имя директории
            
        Returns:
            True если директория должна быть исключена
        """
        return dir_name in self._excluded_dirs
    
    def _create_project_data(self, root_dir: Path, project_dir: Path, 
                           py_files: List[str]) -> Optional[ProjectData]:
        """
        Создает данные проекта
        
        Args:
            root_dir: Корневая директория
            project_dir: Директория проекта
            py_files: Список Python файлов
            
        Returns:
            Данные проекта или None
        """
        try:
            # Определение имени проекта
            rel_path = project_dir.relative_to(root_dir)
            project_name = str(rel_path).replace(os.sep, " / ") if str(rel_path) != "." else "ROOT"
            
            # Подсчет файлов и директорий
            py_files_count = len(py_files)
            
            # Анализ даты создания
            created_date = self._get_earliest_creation_date(project_dir, py_files)
            
            # Сбор директорий
            directories = self._collect_directories(project_dir, root_dir)
            
            # Сбор библиотек (пока пустой, будет заполнен позже)
            libraries = set()
            
            return ProjectData(
                name=project_name,
                path=project_dir,
                py_files_count=py_files_count,
                total_imports=0,  # Будет заполнено позже
                unique_libraries=0,  # Будет заполнено позже
                created_date=created_date,
                directories=directories,
                libraries=libraries
            )
            
        except Exception:
            return None
    
    def _get_earliest_creation_date(self, project_dir: Path, 
                                  py_files: List[str]) -> Optional[datetime.datetime]:
        """
        Получает самую раннюю дату создания файлов
        
        Args:
            project_dir: Директория проекта
            py_files: Список Python файлов
            
        Returns:
            Дата создания или None
        """
        earliest_date = None
        
        for file_name in py_files:
            file_path = project_dir / file_name
            try:
                creation_time = os.path.getctime(file_path)
                creation_date = datetime.datetime.fromtimestamp(creation_time)
                
                if earliest_date is None or creation_date < earliest_date:
                    earliest_date = creation_date
                    
            except (OSError, ValueError):
                continue
        
        return earliest_date
    
    def _collect_directories(self, project_dir: Path, 
                           root_dir: Path) -> Set[str]:
        """
        Собирает список директорий проекта
        
        Args:
            project_dir: Директория проекта
            root_dir: Корневая директория
            
        Returns:
            Множество относительных путей директорий
        """
        directories = set()
        
        try:
            rel_path = project_dir.relative_to(root_dir)
            if str(rel_path) != ".":
                directories.add(str(rel_path))
        except ValueError:
            pass
        
        return directories
    
    def get_project_statistics(self, projects: List[ProjectData]) -> dict:
        """
        Создает статистику по проектам
        
        Args:
            projects: Список проектов
            
        Returns:
            Словарь со статистикой
        """
        if not projects:
            return {
                'total_projects': 0,
                'total_files': 0,
                'total_imports': 0,
                'avg_files_per_project': 0,
                'avg_imports_per_project': 0,
                'oldest_project': None,
                'newest_project': None
            }
        
        total_files = sum(p.py_files_count for p in projects)
        total_imports = sum(p.total_imports for p in projects)
        
        # Даты проектов
        dates = [p.created_date for p in projects if p.created_date]
        oldest_project = min(dates) if dates else None
        newest_project = max(dates) if dates else None
        
        return {
            'total_projects': len(projects),
            'total_files': total_files,
            'total_imports': total_imports,
            'avg_files_per_project': total_files / len(projects),
            'avg_imports_per_project': total_imports / len(projects),
            'oldest_project': oldest_project,
            'newest_project': newest_project
        }
