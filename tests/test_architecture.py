"""
Тесты для проверки новой архитектуры
"""
import pytest
from pathlib import Path
import tempfile
import os

# Добавляем src в путь для импортов
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.configuration import Configuration
from core.import_parser import ImportParser
from core.project_analyzer import ProjectAnalyzer
from core.file_scanner import FileScanner
from core.data_exporter import DataExporter
from core.scan_service import ScanService


class TestArchitecture:
    """Тесты архитектуры"""
    
    def test_configuration_creation(self):
        """Тест создания конфигурации"""
        config = Configuration()
        
        assert config is not None
        assert isinstance(config.get_excluded_libraries(), set)
        assert isinstance(config.get_excluded_directories(), set)
        assert config.get_max_file_size() > 0
        assert config.get_max_depth() > 0
    
    def test_import_parser_creation(self):
        """Тест создания парсера импортов"""
        config = Configuration()
        parser = ImportParser(config)
        
        assert parser is not None
        assert parser.config == config
    
    def test_project_analyzer_creation(self):
        """Тест создания анализатора проектов"""
        config = Configuration()
        analyzer = ProjectAnalyzer(config)
        
        assert analyzer is not None
        assert analyzer.config == config
    
    def test_file_scanner_creation(self):
        """Тест создания сканера файлов"""
        config = Configuration()
        parser = ImportParser(config)
        analyzer = ProjectAnalyzer(config)
        scanner = FileScanner(config, parser, analyzer)
        
        assert scanner is not None
        assert scanner.config == config
        assert scanner.import_parser == parser
        assert scanner.project_analyzer == analyzer
    
    def test_data_exporter_creation(self):
        """Тест создания экспортера данных"""
        exporter = DataExporter()
        
        assert exporter is not None
    
    def test_scan_service_creation(self):
        """Тест создания сервиса сканирования"""
        service = ScanService()
        
        assert service is not None
        assert service.config is not None
        assert service.import_parser is not None
        assert service.project_analyzer is not None
        assert service.file_scanner is not None
        assert service.data_exporter is not None
    
    def test_import_parser_functionality(self):
        """Тест функциональности парсера импортов"""
        config = Configuration()
        parser = ImportParser(config)
        
        # Тестовый код с импортами
        test_code = """
import os
import sys
import numpy as np
from pathlib import Path
import pandas as pd
from typing import List, Dict
"""
        
        imports = parser.parse_imports(test_code, Path("test.py"))
        
        # Проверяем, что стандартные библиотеки отфильтрованы
        assert "os" not in imports
        assert "sys" not in imports
        assert "pathlib" not in imports
        assert "typing" not in imports
        
        # Проверяем, что сторонние библиотеки найдены
        assert "numpy" in imports
        assert "pandas" in imports
    
    def test_configuration_persistence(self):
        """Тест сохранения конфигурации"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = Path(f.name)
        
        try:
            config = Configuration(config_file)
            
            # Изменяем конфигурацию
            config.update_config("max_depth", 10)
            
            # Создаем новую конфигурацию и проверяем, что изменения сохранились
            new_config = Configuration(config_file)
            assert new_config.get_max_depth() == 10
            
        finally:
            # Удаляем временный файл
            if config_file.exists():
                config_file.unlink()
    
    def test_scan_service_validation(self):
        """Тест валидации директории в сервисе"""
        service = ScanService()
        
        # Тест с несуществующей директорией
        is_valid, message = service.validate_directory(Path("/nonexistent/path"))
        assert not is_valid
        assert "не существует" in message
        
        # Тест с файлом вместо директории
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            is_valid, message = service.validate_directory(temp_file)
            assert not is_valid
            assert "не является директорией" in message
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_dependency_injection(self):
        """Тест dependency injection"""
        config = Configuration()
        parser = ImportParser(config)
        analyzer = ProjectAnalyzer(config)
        scanner = FileScanner(config, parser, analyzer)
        
        # Проверяем, что зависимости правильно инжектированы
        assert scanner.config is config
        assert scanner.import_parser is parser
        assert scanner.project_analyzer is analyzer
        
        # Проверяем, что все используют одну и ту же конфигурацию
        assert parser.config is config
        assert analyzer.config is config


if __name__ == "__main__":
    pytest.main([__file__])
