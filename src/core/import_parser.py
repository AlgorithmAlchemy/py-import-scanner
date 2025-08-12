"""
Модуль парсера импортов Python
"""
import ast
from typing import List
from pathlib import Path
from .interfaces import IImportParser
from .configuration import Configuration
from .logging_config import get_logger
from .security import SecurityManager, SecurityConfig
from .performance import PerformanceManager, PerformanceConfig


class ImportParser(IImportParser):
    """Парсер импортов Python с оптимизациями"""
    
    def __init__(self, config: Configuration):
        self.config = config
        self._excluded_libs = config.get_excluded_libraries()
        
        # Инициализация логгера
        self.logger = get_logger("ImportParser")
        
        # Инициализация безопасности
        security_config_dict = config.get_security_config()
        security_config = SecurityConfig(**security_config_dict)
        self.security_manager = SecurityManager(security_config)
        
        # Инициализация производительности
        performance_config_dict = config.get_performance_config()
        performance_config = PerformanceConfig(**performance_config_dict)
        self.performance_manager = PerformanceManager(performance_config)
        
        self.logger.info("ImportParser инициализирован", 
                        extra_data={"excluded_libs_count": len(self._excluded_libs)})
    
    def parse_imports(self, content: str, file_path: Path) -> List[str]:
        """
        Парсит импорты из содержимого файла
        
        Args:
            content: Содержимое файла
            file_path: Путь к файлу
            
        Returns:
            Список найденных библиотек
        """
        # Генерация ключа кэша
        cache_key = self.performance_manager.generate_cache_key(
            "parse_imports", str(file_path), hash(content)
        )
        
        # Попытка получить из кэша
        cached_result = self.performance_manager.get_cached_result(cache_key)
        if cached_result is not None:
            self.logger.debug("Результат парсинга найден в кэше", 
                            extra_data={"file": str(file_path)})
            return cached_result
        
        imports = []
        
        # Быстрая проверка на наличие импортов
        if 'import ' not in content and 'from ' not in content:
            return imports
        
        try:
            # Проверка лимитов AST
            if len(content) > self.security_manager.config.max_ast_nodes:
                self.logger.warning("Файл слишком большой для AST парсинга", 
                                  extra_data={"file": str(file_path)})
                return imports
            
            # Парсинг AST
            tree = ast.parse(content, filename=str(file_path))
            
            # Обход AST
            node_count = 0
            for node in ast.walk(tree):
                node_count += 1
                
                # Проверка лимита узлов AST
                if node_count > self.security_manager.config.max_ast_nodes:
                    self.logger.warning("Превышен лимит узлов AST", 
                                      extra_data={"file": str(file_path)})
                    break
                
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        lib = self._extract_library_name(alias.name)
                        if lib and self._is_valid_library(lib):
                            imports.append(lib)
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        lib = self._extract_library_name(node.module)
                        if lib and self._is_valid_library(lib):
                            imports.append(lib)
                
                # Ранний выход для оптимизации
                if len(imports) > self.security_manager.config.max_imports_per_file:
                    break
                    
        except (SyntaxError, ValueError) as e:
            # Логируем синтаксические ошибки
            self.logger.warning("Синтаксическая ошибка при парсинге файла", 
                              extra_data={
                                  "file": str(file_path),
                                  "error": str(e)
                              })
        
        # Кэширование результата
        self.performance_manager.cache_result(cache_key, imports)
        
        self.logger.debug("Парсинг импортов завершен", 
                         extra_data={
                             "file": str(file_path),
                             "imports_found": len(imports)
                         })
        
        return imports
    
    def _extract_library_name(self, import_name: str) -> str:
        """
        Извлекает имя библиотеки из импорта
        
        Args:
            import_name: Полное имя импорта
            
        Returns:
            Имя библиотеки
        """
        if not import_name:
            return ""
        
        # Берем только первую часть импорта
        library = import_name.split('.')[0]
        
        # Проверяем, что это валидный идентификатор
        if not library or not library.isidentifier():
            return ""
        
        return library
    
    def _is_valid_library(self, library: str) -> bool:
        """
        Проверяет, является ли библиотека валидной для анализа
        
        Args:
            library: Имя библиотеки
            
        Returns:
            True если библиотека валидна
        """
        if not library:
            return False
        
        # Проверяем, не является ли стандартной библиотекой
        if self.is_standard_library(library):
            return False
        
        # Дополнительные проверки
        if library.startswith('_'):
            return False
        
        return True
    
    def is_standard_library(self, library: str) -> bool:
        """
        Проверяет, является ли библиотека стандартной
        
        Args:
            library: Имя библиотеки
            
        Returns:
            True если это стандартная библиотека
        """
        return library in self._excluded_libs
    
    def get_import_statistics(self, imports: List[str]) -> dict:
        """
        Создает статистику по импортам
        
        Args:
            imports: Список импортов
            
        Returns:
            Словарь со статистикой
        """
        if not imports:
            return {
                'total': 0,
                'unique': 0,
                'standard_libs': 0,
                'third_party': 0,
                'most_common': []
            }
        
        # Подсчет уникальных импортов
        unique_imports = set(imports)
        
        # Разделение на стандартные и сторонние
        standard_libs = sum(1 for lib in unique_imports
                            if self.is_standard_library(lib))
        third_party = len(unique_imports) - standard_libs
        
        # Самые частые импорты
        from collections import Counter
        counter = Counter(imports)
        most_common = counter.most_common(10)
        
        return {
            'total': len(imports),
            'unique': len(unique_imports),
            'standard_libs': standard_libs,
            'third_party': third_party,
            'most_common': most_common
        }
