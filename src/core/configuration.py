"""
Модуль конфигурации приложения
"""
from typing import Set
from pathlib import Path
import json
from .interfaces import IConfiguration


class Configuration(IConfiguration):
    """Класс конфигурации приложения"""
    
    def __init__(self, config_file: Path = None):
        self.config_file = config_file or Path("config.json")
        self._load_config()
    
    def _load_config(self) -> None:
        """Загружает конфигурацию из файла или использует значения по умолчанию"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self._save_config()
    
    def _save_config(self) -> None:
        """Сохраняет конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Игнорируем ошибки сохранения
    
    def _get_default_config(self) -> dict:
        """Возвращает конфигурацию по умолчанию"""
        return {
            "excluded_libraries": [
                "__future__", "warnings", "io", "typing", "collections",
                "contextlib", "types", "abc", "forwarding", "ssl",
                "distutils", "operator", "pathlib", "dataclasses",
                "inspect", "socket", "shutil", "attr", "tempfile",
                "zipfile", "betterproto", "the", "struct", "base64",
                "optparse", "textwrap", "setuptools", "pkg_resources",
                "multidict", "enum", "copy", "importlib", "traceback",
                "six", "binascii", "stat", "errno", "grpclib",
                "posixpath", "zlib", "pytz", "bisect", "weakref",
                "winreg", "fnmatch", "site", "email", "html",
                "mimetypes", "locale", "calendar", "shlex",
                "unicodedata", "babel", "pkgutil", "ipaddress",
                "arq", "rsa", "handlers", "opentele", "states",
                "os", "sys", "re", "json", "datetime", "time",
                "math", "random", "itertools", "functools", "logging",
                "subprocess", "threading", "multiprocessing"
            ],
            "excluded_directories": [
                "venv", ".venv", "env", ".env", "__pycache__",
                ".git", "node_modules", "build", "dist",
                ".pytest_cache", ".coverage", ".tox", ".mypy_cache"
            ],
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "max_depth": 6,
            "batch_size": 100,
            "max_workers": 4,
            "supported_encodings": ["utf-8", "cp1251", "latin-1"],
            "file_extensions": [".py"],
            "progress_update_interval": 500
        }
    
    def get_excluded_libraries(self) -> Set[str]:
        """Возвращает список исключенных библиотек"""
        return set(self._config.get("excluded_libraries", []))
    
    def get_excluded_directories(self) -> Set[str]:
        """Возвращает список исключенных директорий"""
        return set(self._config.get("excluded_directories", []))
    
    def get_max_file_size(self) -> int:
        """Возвращает максимальный размер файла для обработки"""
        return self._config.get("max_file_size", 10 * 1024 * 1024)
    
    def get_max_depth(self) -> int:
        """Возвращает максимальную глубину сканирования"""
        return self._config.get("max_depth", 6)
    
    def get_batch_size(self) -> int:
        """Возвращает размер батча для обработки"""
        return self._config.get("batch_size", 100)
    
    def get_max_workers(self) -> int:
        """Возвращает максимальное количество потоков"""
        return self._config.get("max_workers", 4)
    
    def get_supported_encodings(self) -> list:
        """Возвращает поддерживаемые кодировки"""
        return self._config.get("supported_encodings", ["utf-8"])
    
    def get_file_extensions(self) -> list:
        """Возвращает поддерживаемые расширения файлов"""
        return self._config.get("file_extensions", [".py"])
    
    def get_progress_update_interval(self) -> int:
        """Возвращает интервал обновления прогресса"""
        return self._config.get("progress_update_interval", 500)
    
    def update_config(self, key: str, value) -> None:
        """Обновляет значение конфигурации"""
        self._config[key] = value
        self._save_config()
    
    def reset_to_defaults(self) -> None:
        """Сбрасывает конфигурацию к значениям по умолчанию"""
        self._config = self._get_default_config()
        self._save_config()
