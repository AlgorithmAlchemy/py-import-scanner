"""
Модуль безопасности - валидация и санитизация
"""
import os
import re
import hashlib
import tempfile
from pathlib import Path, PurePath

from typing import Optional, List, Dict, Any, Tuple, Set, Pattern
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .logging_config import get_logger


@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    # Ограничения файлов
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_files_per_scan: int = 10000
    max_total_size: int = 1024 * 1024 * 1024  # 1GB
    
    # Ограничения содержимого
    max_line_length: int = 10000
    max_imports_per_file: int = 1000
    max_ast_nodes: int = 100000
    
    # Ограничения путей
    max_path_length: int = 4096
    allowed_extensions: Set[str] = field(default_factory=lambda: {'.py', '.pyw', '.pyx', '.pxd'})
    blocked_patterns: Set[str] = field(default_factory=lambda: {
        '__pycache__', '.git', '.svn', '.hg', '.bzr',
        'node_modules', 'venv', '.venv', 'env', '.env',
        'build', 'dist', '.pytest_cache', '.coverage',
        '.tox', '.mypy_cache', '.cache', 'tmp', 'temp'
    })
    safe_directories: Set[str] = field(default_factory=set)
    
    # Ограничения ресурсов
    max_scan_duration: int = 3600  # 1 час
    max_memory_usage: int = 1024 * 1024 * 1024  # 1GB
    max_threads: int = 8
    
    # Валидация содержимого
    check_for_malicious_patterns: bool = True
    validate_imports: bool = True
    sanitize_content: bool = True


class SecurityValidator:
    """Валидатор безопасности"""
    
    def __init__(self, config: SecurityConfig) -> None:
        self.config: SecurityConfig = config
        self.logger = get_logger("SecurityValidator")
        
        # Компилируем регулярные выражения для производительности
        self._malicious_patterns: List[Pattern] = [
            re.compile(r'eval\s*\(', re.IGNORECASE),
            re.compile(r'exec\s*\(', re.IGNORECASE),
            re.compile(r'__import__\s*\(', re.IGNORECASE),
            re.compile(r'compile\s*\(', re.IGNORECASE),
            re.compile(r'input\s*\(', re.IGNORECASE),
            re.compile(r'raw_input\s*\(', re.IGNORECASE),
            re.compile(r'os\.system\s*\(', re.IGNORECASE),
            re.compile(r'subprocess\..*\(', re.IGNORECASE),
            re.compile(r'open\s*\(.*[\'"]w[\'"]', re.IGNORECASE),
            re.compile(r'file\s*\(.*[\'"]w[\'"]', re.IGNORECASE),
        ]
        
        # Паттерны для подозрительных импортов
        self._suspicious_imports: Set[str] = {
            'pickle', 'marshal', 'shelve', 'dill', 'cloudpickle',
            'subprocess', 'os', 'sys', 'ctypes', 'mmap',
            'socket', 'urllib', 'requests', 'ftplib', 'smtplib',
            'telnetlib', 'poplib', 'imaplib', 'nntplib'
        }
        
        # Счетчики для отслеживания ресурсов
        self._scan_start_time: Optional[float] = None
        self._total_files_processed: int = 0
        self._total_size_processed: int = 0
        self._lock: threading.Lock = threading.Lock()
    
    def start_scan(self) -> None:
        """Начинает новое сканирование"""
        with self._lock:
            self._scan_start_time = time.time()
            self._total_files_processed = 0
            self._total_size_processed = 0
            self.logger.info("Начало сканирования с валидацией безопасности")
    
    def validate_file_path(self, file_path: Path) -> Tuple[bool, str]:
        """
        Валидирует путь к файлу
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        try:
            # Проверка длины пути
            if len(str(file_path)) > self.config.max_path_length:
                return False, f"Путь слишком длинный: {len(str(file_path))} символов"
            
            # Проверка на абсолютный путь
            if file_path.is_absolute():
                return False, "Абсолютные пути не разрешены"
            
            # Проверка на path traversal
            normalized_path: PurePath = PurePath(file_path).resolve()
            if self._contains_path_traversal(str(normalized_path)):
                return False, "Обнаружена попытка path traversal"
            
            # Проверка расширения файла
            if file_path.suffix.lower() not in self.config.allowed_extensions:
                return False, f"Неподдерживаемое расширение: {file_path.suffix}"
            
            # Проверка на заблокированные паттерны
            for pattern in self.config.blocked_patterns:
                if pattern in str(file_path):
                    return False, f"Путь содержит заблокированный паттерн: {pattern}"
            
            # Проверка существования файла
            if not file_path.exists():
                return False, "Файл не существует"
            
            # Проверка, что это файл
            if not file_path.is_file():
                return False, "Путь не является файлом"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка валидации пути: {str(e)}"
    
    def validate_file_size(self, file_path: Path) -> Tuple[bool, str]:
        """
        Валидирует размер файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        try:
            file_size: int = file_path.stat().st_size
            
            # Проверка максимального размера файла
            if file_size > self.config.max_file_size:
                return False, f"Файл слишком большой: {file_size} байт"
            
            # Проверка общего размера
            with self._lock:
                if self._total_size_processed + file_size > self.config.max_total_size:
                    return False, "Превышен лимит общего размера файлов"
                
                self._total_size_processed += file_size
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка проверки размера: {str(e)}"
    
    def validate_file_content(self, content: str, file_path: Path) -> Tuple[bool, str]:
        """
        Валидирует содержимое файла
        
        Args:
            content: Содержимое файла
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        try:
            # Проверка длины содержимого
            if len(content) > self.config.max_file_size:
                return False, "Содержимое файла слишком большое"
            
            # Проверка длины строк
            lines: List[str] = content.split('\n')
            for i, line in enumerate(lines, 1):
                if len(line) > self.config.max_line_length:
                    return False, f"Строка {i} слишком длинная: {len(line)} символов"
            
            # Проверка на злонамеренные паттерны
            if self.config.check_for_malicious_patterns:
                for pattern in self._malicious_patterns:
                    if pattern.search(content):
                        self.logger.warning("Обнаружен подозрительный паттерн", 
                                          extra_data={
                                              "file": str(file_path),
                                              "pattern": pattern.pattern
                                          })
                        return False, f"Обнаружен подозрительный паттерн: {pattern.pattern}"
            
            # Проверка количества импортов
            import_count: int = content.count('import ') + content.count('from ')
            if import_count > self.config.max_imports_per_file:
                return False, f"Слишком много импортов: {import_count}"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка валидации содержимого: {str(e)}"
    
    def validate_imports(self, imports: List[str], file_path: Path) -> Tuple[bool, str]:
        """
        Валидирует список импортов
        
        Args:
            imports: Список импортов
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        if not self.config.validate_imports:
            return True, "OK"
        
        try:
            suspicious_imports: List[str] = []
            
            for import_name in imports:
                # Проверка на подозрительные импорты
                if import_name in self._suspicious_imports:
                    suspicious_imports.append(import_name)
                
                # Проверка на валидность имени
                if not self._is_valid_import_name(import_name):
                    return False, f"Недопустимое имя импорта: {import_name}"
            
            if suspicious_imports:
                self.logger.warning("Обнаружены подозрительные импорты", 
                                  extra_data={
                                      "file": str(file_path),
                                      "imports": suspicious_imports
                                  })
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка валидации импортов: {str(e)}"
    
    def sanitize_content(self, content: str) -> str:
        """
        Санитизирует содержимое файла
        
        Args:
            content: Исходное содержимое
            
        Returns:
            Санитизированное содержимое
        """
        if not self.config.sanitize_content:
            return content
        
        try:
            # Удаление null-байтов
            content = content.replace('\x00', '')
            
            # Удаление управляющих символов (кроме табуляции и новой строки)
            content = ''.join(char for char in content 
                            if char.isprintable() or char in '\t\n\r')
            
            # Нормализация окончаний строк
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            # Удаление лишних пробелов в конце строк
            lines: List[str] = content.split('\n')
            lines = [line.rstrip() for line in lines]
            content = '\n'.join(lines)
            
            return content
            
        except Exception as e:
            self.logger.error("Ошибка санитизации содержимого", 
                            extra_data={"error": str(e)})
            return content
    
    def check_resource_limits(self) -> Tuple[bool, str]:
        """
        Проверяет лимиты ресурсов
        
        Returns:
            Кортеж (в пределах лимитов, сообщение об ошибке)
        """
        try:
            # Проверка времени сканирования
            if self._scan_start_time:
                elapsed_time: float = time.time() - self._scan_start_time
                if elapsed_time > self.config.max_scan_duration:
                    return False, f"Превышено время сканирования: {elapsed_time:.2f}с"
            
            # Проверка количества файлов
            with self._lock:
                if self._total_files_processed > self.config.max_files_per_scan:
                    return False, f"Превышено количество файлов: {self._total_files_processed}"
            
            # Проверка памяти (базовая)
            import psutil
            process = psutil.Process()
            memory_usage: int = process.memory_info().rss
            if memory_usage > self.config.max_memory_usage:
                return False, f"Превышено использование памяти: {memory_usage} байт"
            
            return True, "OK"
            
        except ImportError:
            # psutil не установлен, пропускаем проверку памяти
            return True, "OK"
        except Exception as e:
            return False, f"Ошибка проверки ресурсов: {str(e)}"
    
    def increment_file_count(self) -> None:
        """Увеличивает счетчик обработанных файлов"""
        with self._lock:
            self._total_files_processed += 1
    
    def _contains_path_traversal(self, path: str) -> bool:
        """Проверяет наличие path traversal в пути"""
        dangerous_patterns: List[str] = [
            '..', '../', '..\\', '..%2f', '..%5c',
            '%2e%2e', '%2e%2e%2f', '%2e%2e%5c'
        ]
        
        normalized_path: str = path.lower()
        for pattern in dangerous_patterns:
            if pattern in normalized_path:
                return True
        
        return False
    
    def _is_valid_import_name(self, import_name: str) -> bool:
        """Проверяет валидность имени импорта"""
        if not import_name:
            return False
        
        # Проверка на валидный Python идентификатор
        if not import_name.isidentifier():
            return False
        
        # Проверка на зарезервированные слова
        import keyword
        if keyword.iskeyword(import_name):
            return False
        
        # Проверка длины
        if len(import_name) > 100:
            return False
        
        return True


class SecurityManager:
    """Менеджер безопасности"""
    
    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        self.config: SecurityConfig = config or SecurityConfig()
        self.validator: SecurityValidator = SecurityValidator(self.config)
        self.logger = get_logger("SecurityManager")
        
        # Кэш для хешей файлов
        self._file_hashes: Dict[str, str] = {}
        self._hash_lock: threading.Lock = threading.Lock()
    
    def validate_scan_request(self, directory: Path) -> Tuple[bool, str]:
        """
        Валидирует запрос на сканирование
        
        Args:
            directory: Директория для сканирования
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        try:
            # Проверка существования директории
            if not directory.exists():
                return False, "Директория не существует"
            
            if not directory.is_dir():
                return False, "Путь не является директорией"
            
            # Проверка прав доступа
            if not os.access(directory, os.R_OK):
                return False, "Нет прав на чтение директории"
            
            # Проверка на безопасные директории
            if self.config.safe_directories:
                is_safe: bool = False
                for safe_dir in self.config.safe_directories:
                    try:
                        directory.resolve().relative_to(Path(safe_dir).resolve())
                        is_safe = True
                        break
                    except ValueError:
                        continue
                
                if not is_safe:
                    return False, "Директория не входит в список безопасных"
            
            # Начало сканирования
            self.validator.start_scan()
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка валидации запроса: {str(e)}"
    
    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Валидирует файл для обработки
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        try:
            # Валидация пути
            is_valid: bool
            message: str
            is_valid, message = self.validator.validate_file_path(file_path)
            if not is_valid:
                return False, message
            
            # Валидация размера
            is_valid, message = self.validator.validate_file_size(file_path)
            if not is_valid:
                return False, message
            
            # Проверка ресурсов
            is_valid, message = self.validator.check_resource_limits()
            if not is_valid:
                return False, message
            
            # Увеличение счетчика файлов
            self.validator.increment_file_count()
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка валидации файла: {str(e)}"
    
    def validate_and_sanitize_content(self, content: str, file_path: Path) -> Tuple[bool, str, str]:
        """
        Валидирует и санитизирует содержимое файла
        
        Args:
            content: Исходное содержимое
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке, санитизированное содержимое)
        """
        try:
            # Валидация содержимого
            is_valid: bool
            message: str
            is_valid, message = self.validator.validate_file_content(content, file_path)
            if not is_valid:
                return False, message, content
            
            # Санитизация содержимого
            sanitized_content: str = self.validator.sanitize_content(content)
            
            return True, "OK", sanitized_content
            
        except Exception as e:
            return False, f"Ошибка обработки содержимого: {str(e)}", content
    
    def validate_imports(self, imports: List[str], file_path: Path) -> Tuple[bool, str]:
        """
        Валидирует импорты
        
        Args:
            imports: Список импортов
            file_path: Путь к файлу
            
        Returns:
            Кортеж (валиден, сообщение об ошибке)
        """
        return self.validator.validate_imports(imports, file_path)
    
    def get_file_hash(self, file_path: Path) -> str:
        """
        Получает хеш файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Хеш файла
        """
        file_str: str = str(file_path)
        
        with self._hash_lock:
            if file_str in self._file_hashes:
                return self._file_hashes[file_str]
        
        try:
            # Вычисление хеша
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            file_hash: str = hash_md5.hexdigest()
            
            with self._hash_lock:
                self._file_hashes[file_str] = file_hash
            
            return file_hash
            
        except Exception as e:
            self.logger.error("Ошибка вычисления хеша", 
                            extra_data={"file": str(file_path), "error": str(e)})
            return ""
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        Возвращает отчет о безопасности
        
        Returns:
            Отчет о безопасности
        """
        return {
            "files_processed": self.validator._total_files_processed,
            "total_size_processed": self.validator._total_size_processed,
            "scan_duration": time.time() - self.validator._scan_start_time if self.validator._scan_start_time else 0,
            "file_hashes_count": len(self._file_hashes),
            "security_config": {
                "max_file_size": self.config.max_file_size,
                "max_files_per_scan": self.config.max_files_per_scan,
                "max_total_size": self.config.max_total_size,
                "check_for_malicious_patterns": self.config.check_for_malicious_patterns,
                "validate_imports": self.config.validate_imports,
                "sanitize_content": self.config.sanitize_content
            }
        }
