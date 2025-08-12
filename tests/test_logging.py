"""
Тесты для системы логирования
"""
import pytest
import tempfile
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging_config import (
    LogConfig, StructuredFormatter, LoggerManager, 
    setup_logging, get_logger, log_with_context
)


class TestLogConfig:
    """Тесты для конфигурации логирования"""
    
    def test_default_config(self):
        """Тест дефолтной конфигурации"""
        config = LogConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.file_enabled is True
        assert config.console_enabled is True
    
    def test_custom_config(self):
        """Тест кастомной конфигурации"""
        config = LogConfig(
            level="DEBUG",
            format="text",
            file_enabled=False,
            console_enabled=True
        )
        assert config.level == "DEBUG"
        assert config.format == "text"
        assert config.file_enabled is False
        assert config.console_enabled is True


class TestStructuredFormatter:
    """Тесты для структурированного форматтера"""
    
    def test_json_format(self):
        """Тест JSON форматирования"""
        formatter = StructuredFormatter("json")
        record = self._create_test_record("Test message")
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert "timestamp" in data
    
    def test_text_format(self):
        """Тест текстового форматирования"""
        formatter = StructuredFormatter("text")
        record = self._create_test_record("Test message")
        
        result = formatter.format(record)
        
        assert "Test message" in result
        assert "[INFO]" in result
        assert "[test]" in result
    
    def test_simple_format(self):
        """Тест простого форматирования"""
        formatter = StructuredFormatter("simple")
        record = self._create_test_record("Test message")
        
        result = formatter.format(record)
        
        assert result == "INFO: Test message"
    
    def test_json_with_extra_data(self):
        """Тест JSON с дополнительными данными"""
        formatter = StructuredFormatter("json")
        record = self._create_test_record("Test message")
        record.extra_data = {"user_id": 123, "action": "test"}
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["user_id"] == 123
        assert data["action"] == "test"
    
    def _create_test_record(self, message: str):
        """Создает тестовую запись лога"""
        import logging
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.created = datetime.now().timestamp()
        return record


class TestLoggerManager:
    """Тесты для менеджера логирования"""
    
    def test_logger_creation(self):
        """Тест создания логгера"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(log_dir=temp_dir, file_enabled=False)
            manager = LoggerManager(config)
            
            logger = manager.get_logger("test")
            assert logger is not None
            assert logger.name == "test"
    
    def test_log_with_context(self):
        """Тест логирования с контекстом"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(log_dir=temp_dir, file_enabled=False)
            manager = LoggerManager(config)
            
            logger = manager.get_logger("test")
            manager.log_with_context(
                logger, 
                logging.INFO, 
                "Test message",
                extra_data={"key": "value"}
            )
    
    def test_file_logging(self):
        """Тест файлового логирования"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(
                log_dir=temp_dir,
                file_enabled=True,
                console_enabled=False
            )
            manager = LoggerManager(config)
            
            logger = manager.get_logger("test")
            logger.info("Test message")
            
            # Проверяем, что файл создался
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) > 0


class TestGlobalLogging:
    """Тесты для глобального логирования"""
    
    def test_setup_logging(self):
        """Тест настройки глобального логирования"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(log_dir=temp_dir, file_enabled=False)
            manager = setup_logging(config)
            
            assert manager is not None
            assert isinstance(manager, LoggerManager)
    
    def test_get_logger(self):
        """Тест получения логгера"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(log_dir=temp_dir, file_enabled=False)
            setup_logging(config)
            
            logger = get_logger("test")
            assert logger is not None
            assert logger.name == "test"
    
    def test_log_with_context_function(self):
        """Тест функции логирования с контекстом"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(log_dir=temp_dir, file_enabled=False)
            setup_logging(config)
            
            logger = get_logger("test")
            log_with_context(
                logger,
                logging.INFO,
                "Test message",
                extra_data={"test": True}
            )


class TestLoggingIntegration:
    """Интеграционные тесты логирования"""
    
    def test_full_logging_flow(self):
        """Тест полного цикла логирования"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Настройка
            config = LogConfig(
                level="DEBUG",
                format="json",
                log_dir=temp_dir,
                file_enabled=True,
                console_enabled=False
            )
            manager = setup_logging(config)
            
            # Логирование
            logger = get_logger("integration_test")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Проверка файлов
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) > 0
            
            # Проверка содержимого
            with open(log_files[0], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) >= 3  # Минимум 3 сообщения
            
            # Проверка JSON формата
            for line in lines:
                if line.strip():
                    data = json.loads(line)
                    assert "message" in data
                    assert "level" in data
                    assert "timestamp" in data
    
    def test_error_logging(self):
        """Тест логирования ошибок"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LogConfig(
                level="ERROR",
                log_dir=temp_dir,
                file_enabled=True,
                console_enabled=False
            )
            setup_logging(config)
            
            logger = get_logger("error_test")
            
            try:
                raise ValueError("Test error")
            except ValueError as e:
                logger.error("Caught error", extra_data={"error_type": type(e).__name__})
            
            # Проверяем файл ошибок
            error_files = list(Path(temp_dir).glob("errors_*.log"))
            assert len(error_files) > 0


if __name__ == "__main__":
    pytest.main([__file__])
