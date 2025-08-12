"""
Тесты модуля безопасности
"""
import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.security import SecurityConfig, SecurityValidator, SecurityManager


class TestSecurityConfig:
    """Тесты конфигурации безопасности"""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        config = SecurityConfig()
        
        assert config.max_file_size == 50 * 1024 * 1024
        assert config.max_files_per_scan == 10000
        assert config.max_total_size == 1024 * 1024 * 1024
        assert config.check_for_malicious_patterns is True
        assert config.validate_imports is True
        assert config.sanitize_content is True
        assert '.py' in config.allowed_extensions
        assert '__pycache__' in config.blocked_patterns
    
    def test_custom_config(self):
        """Тест пользовательской конфигурации"""
        config = SecurityConfig(
            max_file_size=1024,
            max_files_per_scan=100,
            check_for_malicious_patterns=False
        )
        
        assert config.max_file_size == 1024
        assert config.max_files_per_scan == 100
        assert config.check_for_malicious_patterns is False


class TestSecurityValidator:
    """Тесты валидатора безопасности"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.config = SecurityConfig(
            max_file_size=1024,
            max_files_per_scan=10,
            max_total_size=2048
        )
        self.validator = SecurityValidator(self.config)
    
    def test_validate_file_path_valid(self):
        """Тест валидации корректного пути"""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_path(temp_file)
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_file_path_too_long(self):
        """Тест валидации слишком длинного пути"""
        long_path = Path("a" * 5000)
        is_valid, message = self.validator.validate_file_path(long_path)
        assert not is_valid
        assert "слишком длинный" in message
    
    def test_validate_file_path_absolute(self):
        """Тест валидации абсолютного пути"""
        absolute_path = Path("/etc/passwd")
        is_valid, message = self.validator.validate_file_path(absolute_path)
        assert not is_valid
        assert "Абсолютные пути не разрешены" in message
    
    def test_validate_file_path_traversal(self):
        """Тест валидации path traversal"""
        traversal_path = Path("../../../etc/passwd")
        is_valid, message = self.validator.validate_file_path(traversal_path)
        assert not is_valid
        assert "path traversal" in message
    
    def test_validate_file_path_wrong_extension(self):
        """Тест валидации неправильного расширения"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_path(temp_file)
            assert not is_valid
            assert "Неподдерживаемое расширение" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_file_path_blocked_pattern(self):
        """Тест валидации заблокированного паттерна"""
        blocked_path = Path("test/__pycache__/file.py")
        is_valid, message = self.validator.validate_file_path(blocked_path)
        assert not is_valid
        assert "заблокированный паттерн" in message
    
    def test_validate_file_size_valid(self):
        """Тест валидации корректного размера файла"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_size(temp_file)
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_file_size_too_large(self):
        """Тест валидации слишком большого файла"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 2048)  # Больше лимита в 1024
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_size(temp_file)
            assert not is_valid
            assert "слишком большой" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_file_content_valid(self):
        """Тест валидации корректного содержимого"""
        content = "import os\nimport sys\n"
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_content(content, temp_file)
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_file_content_malicious_pattern(self):
        """Тест валидации злонамеренного паттерна"""
        content = "eval('print(\"hello\")')"
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_content(content, temp_file)
            assert not is_valid
            assert "подозрительный паттерн" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_file_content_too_many_imports(self):
        """Тест валидации слишком большого количества импортов"""
        content = "import os\n" * 1001  # Больше лимита в 1000
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_file_content(content, temp_file)
            assert not is_valid
            assert "слишком много импортов" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_imports_valid(self):
        """Тест валидации корректных импортов"""
        imports = ["os", "sys", "json"]
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_imports(imports, temp_file)
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_imports_suspicious(self):
        """Тест валидации подозрительных импортов"""
        imports = ["pickle", "subprocess"]
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_imports(imports, temp_file)
            # Подозрительные импорты должны вызывать предупреждение, но не блокировать
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_imports_invalid_name(self):
        """Тест валидации недопустимого имени импорта"""
        imports = ["123invalid", "class"]  # class - зарезервированное слово
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.validator.validate_imports(imports, temp_file)
            assert not is_valid
            assert "Недопустимое имя импорта" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_sanitize_content(self):
        """Тест санитизации содержимого"""
        content = "import os\x00\n\r\nimport sys\r\n  "
        sanitized = self.validator.sanitize_content(content)
        
        assert "\x00" not in sanitized
        assert sanitized == "import os\n\nimport sys\n"
    
    def test_check_resource_limits(self):
        """Тест проверки лимитов ресурсов"""
        is_valid, message = self.validator.check_resource_limits()
        assert is_valid
        assert message == "OK"
    
    def test_contains_path_traversal(self):
        """Тест обнаружения path traversal"""
        assert self.validator._contains_path_traversal("../etc/passwd")
        assert self.validator._contains_path_traversal("..\\windows\\system32")
        assert self.validator._contains_path_traversal("%2e%2e/etc/passwd")
        assert not self.validator._contains_path_traversal("normal/path")
    
    def test_is_valid_import_name(self):
        """Тест валидации имени импорта"""
        assert self.validator._is_valid_import_name("os")
        assert self.validator._is_valid_import_name("my_module")
        assert not self.validator._is_valid_import_name("123module")
        assert not self.validator._is_valid_import_name("class")
        assert not self.validator._is_valid_import_name("")


class TestSecurityManager:
    """Тесты менеджера безопасности"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.config = SecurityConfig(
            max_file_size=1024,
            max_files_per_scan=10,
            max_total_size=2048
        )
        self.manager = SecurityManager(self.config)
    
    def test_validate_scan_request_valid(self):
        """Тест валидации корректного запроса на сканирование"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Создаем Python файл
            (temp_path / "test.py").write_text("import os")
            
            is_valid, message = self.manager.validate_scan_request(temp_path)
            assert is_valid
            assert message == "OK"
    
    def test_validate_scan_request_nonexistent(self):
        """Тест валидации несуществующей директории"""
        nonexistent_path = Path("/nonexistent/directory")
        is_valid, message = self.manager.validate_scan_request(nonexistent_path)
        assert not is_valid
        assert "не существует" in message
    
    def test_validate_scan_request_no_python_files(self):
        """Тест валидации директории без Python файлов"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Создаем не-Python файл
            (temp_path / "test.txt").write_text("content")
            
            is_valid, message = self.manager.validate_scan_request(temp_path)
            assert not is_valid
            assert "не найдено Python файлов" in message
    
    def test_validate_file(self):
        """Тест валидации файла"""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b"import os")
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.manager.validate_file(temp_file)
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_and_sanitize_content(self):
        """Тест валидации и санитизации содержимого"""
        content = "import os\x00\nimport sys\r\n"
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message, sanitized = self.manager.validate_and_sanitize_content(content, temp_file)
            assert is_valid
            assert message == "OK"
            assert sanitized == "import os\nimport sys\n"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_validate_imports(self):
        """Тест валидации импортов"""
        imports = ["os", "sys"]
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = self.manager.validate_imports(imports, temp_file)
            assert is_valid
            assert message == "OK"
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_get_file_hash(self):
        """Тест получения хеша файла"""
        content = "test content"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content.encode())
            temp_file = Path(f.name)
        
        try:
            file_hash = self.manager.get_file_hash(temp_file)
            assert len(file_hash) == 32  # MD5 hash length
            assert file_hash.isalnum()
            
            # Проверяем кэширование
            file_hash2 = self.manager.get_file_hash(temp_file)
            assert file_hash == file_hash2
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_get_security_report(self):
        """Тест получения отчета о безопасности"""
        report = self.manager.get_security_report()
        
        assert "files_processed" in report
        assert "total_size_processed" in report
        assert "scan_duration" in report
        assert "file_hashes_count" in report
        assert "security_config" in report
        
        assert report["files_processed"] == 0
        assert report["total_size_processed"] == 0
        assert report["file_hashes_count"] == 0


class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""
    
    def test_full_scan_validation_flow(self):
        """Тест полного потока валидации сканирования"""
        config = SecurityConfig(
            max_file_size=1024,
            max_files_per_scan=5,
            max_total_size=2048
        )
        manager = SecurityManager(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создаем несколько Python файлов
            (temp_path / "test1.py").write_text("import os")
            (temp_path / "test2.py").write_text("import sys")
            (temp_path / "test3.py").write_text("import json")
            
            # Валидируем запрос на сканирование
            is_valid, message = manager.validate_scan_request(temp_path)
            assert is_valid
            assert message == "OK"
            
            # Валидируем каждый файл
            for py_file in temp_path.glob("*.py"):
                is_valid, message = manager.validate_file(py_file)
                assert is_valid
                assert message == "OK"
                
                # Валидируем содержимое
                content = py_file.read_text()
                is_valid, message, sanitized = manager.validate_and_sanitize_content(content, py_file)
                assert is_valid
                assert message == "OK"
                
                # Валидируем импорты
                imports = ["os", "sys", "json"]
                is_valid, message = manager.validate_imports(imports, py_file)
                assert is_valid
                assert message == "OK"
    
    def test_security_with_malicious_content(self):
        """Тест безопасности с злонамеренным содержимым"""
        config = SecurityConfig(
            max_file_size=1024,
            check_for_malicious_patterns=True
        )
        manager = SecurityManager(config)
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            # Тестируем различные злонамеренные паттерны
            malicious_patterns = [
                "eval('print(\"hello\")')",
                "exec('import os')",
                "__import__('os')",
                "os.system('ls')",
                "subprocess.call(['ls'])",
                "open('file.txt', 'w')"
            ]
            
            for pattern in malicious_patterns:
                is_valid, message, sanitized = manager.validate_and_sanitize_content(pattern, temp_file)
                assert not is_valid
                assert "подозрительный паттерн" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__])
