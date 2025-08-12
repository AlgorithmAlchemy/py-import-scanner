"""
Модуль для настройки структурированного логирования
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LogConfig:
    """Конфигурация логирования"""
    level: str = "INFO"
    format: str = "json"  # json, text, simple
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_dir: str = "logs"
    include_timestamp: bool = True
    include_module: bool = True
    include_function: bool = True
    include_line: bool = True


class StructuredFormatter(logging.Formatter):
    """Структурированный форматтер для логов"""
    
    def __init__(self, format_type: str = "json", include_extra: bool = True):
        super().__init__()
        self.format_type = format_type
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в структурированном виде"""
        if self.format_type == "json":
            return self._format_json(record)
        elif self.format_type == "text":
            return self._format_text(record)
        else:
            return self._format_simple(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Форматирует в JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Добавляем дополнительную информацию
        if hasattr(record, 'module') and record.module:
            log_data["module"] = record.module
        if hasattr(record, 'funcName') and record.funcName:
            log_data["function"] = record.funcName
        if hasattr(record, 'lineno') and record.lineno:
            log_data["line"] = record.lineno
        
        # Добавляем экстра поля
        if self.include_extra and hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Добавляем исключения
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Форматирует в текстовом виде"""
        parts = [
            f"[{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')}]",
            f"[{record.levelname:8}]",
            f"[{record.name}]"
        ]
        
        if hasattr(record, 'module') and record.module:
            parts.append(f"[{record.module}]")
        if hasattr(record, 'funcName') and record.funcName:
            parts.append(f"[{record.funcName}]")
        if hasattr(record, 'lineno') and record.lineno:
            parts.append(f"[L{record.lineno}]")
        
        parts.append(record.getMessage())
        
        # Добавляем экстра поля
        if self.include_extra and hasattr(record, 'extra_data'):
            extra_str = " ".join(
                [f"{k}={v}" for k, v in record.extra_data.items()]
            )
            parts.append(f"({extra_str})")
        
        result = " ".join(parts)
        
        if record.exc_info:
            result += f"\n{self.formatException(record.exc_info)}"
        
        return result
    
    def _format_simple(self, record: logging.LogRecord) -> str:
        """Простое форматирование"""
        return f"{record.levelname}: {record.getMessage()}"


class LoggerManager:
    """Менеджер логирования"""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Настраивает систему логирования"""
        # Создаем директорию для логов
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(exist_ok=True)
        
        # Настраиваем корневой логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # Очищаем существующие обработчики
        root_logger.handlers.clear()
        
        # Создаем форматтеры
        formatters = {
            "json": StructuredFormatter("json"),
            "text": StructuredFormatter("text"),
            "simple": StructuredFormatter("simple")
        }
        
        # Консольный обработчик
        if self.config.console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config.level.upper()))
            console_handler.setFormatter(formatters.get(self.config.format, formatters["text"]))
            root_logger.addHandler(console_handler)
        
        # Файловый обработчик
        if self.config.file_enabled:
            log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, self.config.level.upper()))
            file_handler.setFormatter(formatters.get(self.config.format, formatters["json"]))
            root_logger.addHandler(file_handler)
        
        # Обработчик ошибок
        error_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatters.get(self.config.format, formatters["json"]))
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Получает логгер по имени"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def log_with_context(self, logger: logging.Logger, level: int, message: str, 
                        extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Логирует сообщение с дополнительным контекстом"""
        if extra_data is None:
            extra_data = {}
        
        # Добавляем дополнительные поля
        extra_data.update(kwargs)
        
        # Создаем запись с экстра данными
        record = logger.makeRecord(
            logger.name, level, "", 0, message, (), None
        )
        record.extra_data = extra_data
        
        logger.handle(record)


# Глобальный менеджер логирования
_logger_manager: Optional[LoggerManager] = None


def setup_logging(config: LogConfig) -> LoggerManager:
    """Настраивает глобальное логирование"""
    global _logger_manager
    _logger_manager = LoggerManager(config)
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """Получает логгер по имени"""
    if _logger_manager is None:
        # Создаем дефолтную конфигурацию
        setup_logging(LogConfig())
    return _logger_manager.get_logger(name)


def log_with_context(logger: logging.Logger, level: int, message: str,
                    extra_data: Optional[Dict[str, Any]] = None, **kwargs):
    """Логирует сообщение с контекстом"""
    if _logger_manager is None:
        setup_logging(LogConfig())
    _logger_manager.log_with_context(logger, level, message, extra_data, **kwargs)
