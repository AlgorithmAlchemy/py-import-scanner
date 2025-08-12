"""
Интерфейсы для определения контрактов между модулями
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ImportData:
    """Данные об импорте"""
    library: str
    count: int
    percentage: float
    files: List[str]


@dataclass
class ProjectData:
    """Данные о проекте"""
    name: str
    path: Path
    py_files_count: int
    total_imports: int
    unique_libraries: int
    created_date: Optional[datetime]
    directories: Set[str]
    libraries: Set[str]


@dataclass
class ScanResult:
    """Результат сканирования"""
    imports_data: Dict[str, ImportData]
    projects_data: List[ProjectData]
    total_files_scanned: int
    total_imports: int
    scan_duration: float
    scan_timestamp: datetime


class IFileScanner(ABC):
    """Интерфейс для сканера файлов"""
    
    @abstractmethod
    def scan_directory(self, directory: Path,
                       progress_callback=None) -> ScanResult:
        """Сканирует директорию и возвращает результаты"""
        pass
    
    @abstractmethod
    def scan_file(self, file_path: Path) -> List[str]:
        """Сканирует один файл и возвращает список импортов"""
        pass


class IImportParser(ABC):
    """Интерфейс для парсера импортов"""
    
    @abstractmethod
    def parse_imports(self, content: str, file_path: Path) -> List[str]:
        """Парсит импорты из содержимого файла"""
        pass
    
    @abstractmethod
    def is_standard_library(self, library: str) -> bool:
        """Проверяет, является ли библиотека стандартной"""
        pass


class IProjectAnalyzer(ABC):
    """Интерфейс для анализатора проектов"""
    
    @abstractmethod
    def analyze_project_structure(self, directory: Path) -> List[ProjectData]:
        """Анализирует структуру проекта"""
        pass
    
    @abstractmethod
    def find_projects(self, root_directory: Path) -> List[Path]:
        """Находит все проекты в директории"""
        pass


class IDataExporter(ABC):
    """Интерфейс для экспорта данных"""
    
    @abstractmethod
    def export_to_csv(self, data: ScanResult, file_path: Path) -> None:
        """Экспортирует данные в CSV"""
        pass
    
    @abstractmethod
    def export_to_json(self, data: ScanResult, file_path: Path) -> None:
        """Экспортирует данные в JSON"""
        pass


class IProgressReporter(ABC):
    """Интерфейс для отчетов о прогрессе"""
    
    @abstractmethod
    def report_progress(self, message: str, percentage: Optional[float] = None) -> None:
        """Отправляет отчет о прогрессе"""
        pass
    
    @abstractmethod
    def report_error(self, error: str) -> None:
        """Отправляет отчет об ошибке"""
        pass


class IConfiguration(ABC):
    """Интерфейс для конфигурации"""
    
    @abstractmethod
    def get_excluded_libraries(self) -> Set[str]:
        """Возвращает список исключенных библиотек"""
        pass
    
    @abstractmethod
    def get_excluded_directories(self) -> Set[str]:
        """Возвращает список исключенных директорий"""
        pass
    
    @abstractmethod
    def get_max_file_size(self) -> int:
        """Возвращает максимальный размер файла для обработки"""
        pass
    
    @abstractmethod
    def get_max_depth(self) -> int:
        """Возвращает максимальную глубину сканирования"""
        pass
    
    @abstractmethod
    def get_logging_config(self) -> dict:
        """Возвращает конфигурацию логирования"""
        pass
    
    @abstractmethod
    def update_logging_config(self, key: str, value) -> None:
        """Обновляет настройку логирования"""
        pass
