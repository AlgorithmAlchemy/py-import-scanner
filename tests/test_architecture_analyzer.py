"""
Тесты для анализатора архитектуры
"""
import unittest
from pathlib import Path
import tempfile
import sys

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.architecture_analyzer import (
    ArchitectureAnalyzer, ArchitectureReport, ModuleInfo, 
    DependencyEdge, ModuleAnalyzerVisitor
)


class TestArchitectureAnalyzer(unittest.TestCase):
    """Тесты для ArchitectureAnalyzer"""

    def setUp(self):
        """Настройка тестов"""
        self.analyzer = ArchitectureAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        self.test_project = Path(self.temp_dir) / "test_project"

    def tearDown(self):
        """Очистка после тестов"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_project(self) -> Path:
        """Создает тестовый проект"""
        self.test_project.mkdir(exist_ok=True)
        
        # Создаем структуру проекта
        (self.test_project / "module1").mkdir()
        (self.test_project / "module2").mkdir()
        (self.test_project / "module3").mkdir()
        
        # Создаем файлы
        files = {
            "main.py": """
import module1
from module2 import ClassB
from module3 import function_c

def main():
    pass
""",
            "module1/__init__.py": """
from .core import CoreClass
""",
            "module1/core.py": """
class CoreClass:
    def __init__(self):
        pass
""",
            "module2/__init__.py": """
from .utils import ClassB
""",
            "module2/utils.py": """
from module1.core import CoreClass

class ClassB(CoreClass):
    def method(self):
        pass
""",
            "module3/__init__.py": """
from .helpers import function_c
""",
            "module3/helpers.py": """
from module2.utils import ClassB

def function_c():
    return ClassB()
"""
        }
        
        for file_path, content in files.items():
            full_path = self.test_project / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return self.test_project

    def test_find_python_files(self):
        """Тест поиска Python файлов"""
        project = self.create_test_project()
        
        files = self.analyzer._find_python_files(project)
        
        # Должны найти все Python файлы
        self.assertGreater(len(files), 0)
        
        # Проверяем, что найдены основные файлы
        file_names = [f.name for f in files]
        self.assertIn("main.py", file_names)
        self.assertIn("core.py", file_names)
        self.assertIn("utils.py", file_names)
        self.assertIn("helpers.py", file_names)

    def test_get_module_name(self):
        """Тест определения имени модуля"""
        project = self.create_test_project()
        
        # Тестируем разные пути
        test_cases = [
            (project / "main.py", "main"),
            (project / "module1" / "core.py", "module1.core"),
            (project / "module2" / "utils.py", "module2.utils"),
        ]
        
        for file_path, expected_name in test_cases:
            module_name = self.analyzer._get_module_name(file_path, project)
            self.assertEqual(module_name, expected_name)

    def test_analyze_file(self):
        """Тест анализа отдельного файла"""
        project = self.create_test_project()
        file_path = project / "main.py"
        
        module_info = self.analyzer._analyze_file(file_path, project)
        
        self.assertIsNotNone(module_info)
        self.assertEqual(module_info.name, "main")
        self.assertIn("module1", module_info.imports)
        self.assertIn("module2", module_info.imports)
        self.assertIn("module3", module_info.imports)
        self.assertIn("main", module_info.functions)

    def test_resolve_import(self):
        """Тест разрешения импортов"""
        project = self.create_test_project()
        
        # Анализируем все файлы для заполнения modules_info
        for file_path in self.analyzer._find_python_files(project):
            module_info = self.analyzer._analyze_file(file_path, project)
            if module_info:
                self.analyzer.modules_info[module_info.name] = module_info
        
        # Тестируем разрешение импортов
        test_cases = [
            ("module1", "main", "module1"),
            ("module2", "main", "module2"),
            ("module3", "main", "module3"),
        ]
        
        for import_name, current_module, expected_target in test_cases:
            target = self.analyzer._resolve_import(import_name, current_module)
            self.assertEqual(target, expected_target)

    def test_analyze_project_integration(self):
        """Интеграционный тест анализа проекта"""
        project = self.create_test_project()
        
        report = self.analyzer.analyze_project(project)
        
        # Проверяем базовую структуру отчета
        self.assertIsInstance(report, ArchitectureReport)
        self.assertGreater(report.total_modules, 0)
        self.assertIsInstance(report.modules, list)
        self.assertIsInstance(report.dependencies, list)
        self.assertIsInstance(report.recommendations, list)

    def test_build_dependency_graph(self):
        """Тест построения графа зависимостей"""
        project = self.create_test_project()
        
        # Анализируем проект
        report = self.analyzer.analyze_project(project)
        
        # Проверяем граф
        self.assertIsNotNone(report.graph)
        self.assertGreater(len(report.graph.nodes()), 0)
        self.assertGreater(len(report.graph.edges()), 0)

    def test_analyze_architecture_patterns(self):
        """Тест анализа паттернов архитектуры"""
        project = self.create_test_project()
        
        # Анализируем проект
        report = self.analyzer.analyze_project(project)
        
        # Проверяем, что анализ паттернов выполнен
        self.assertIsInstance(report.circular_dependencies, list)
        self.assertIsInstance(report.isolated_modules, list)
        self.assertIsInstance(report.highly_coupled_modules, list)

    def test_generate_recommendations(self):
        """Тест генерации рекомендаций"""
        report = ArchitectureReport()
        
        # Без проблем
        recommendations = self.analyzer._generate_recommendations(report)
        self.assertIn("хорошо структурированной", recommendations[0])
        
        # С циклическими зависимостями
        report.circular_dependencies = [["module1", "module2", "module1"]]
        recommendations = self.analyzer._generate_recommendations(report)
        self.assertIn("циклических зависимостей", recommendations[0])

    def test_export_report_json(self):
        """Тест экспорта в JSON"""
        project = self.create_test_project()
        report = self.analyzer.analyze_project(project)
        
        output_path = Path(self.temp_dir) / "test_report.json"
        self.analyzer.export_report(report, output_path, 'json')
        
        self.assertTrue(output_path.exists())
        
        # Проверяем содержимое
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('summary', data)
        self.assertIn('modules', data)
        self.assertIn('dependencies', data)

    def test_export_report_dot(self):
        """Тест экспорта в DOT"""
        project = self.create_test_project()
        report = self.analyzer.analyze_project(project)
        
        output_path = Path(self.temp_dir) / "test_report.dot"
        self.analyzer.export_report(report, output_path, 'dot')
        
        self.assertTrue(output_path.exists())
        
        # Проверяем содержимое
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("digraph Dependencies", content)
        self.assertIn("rankdir=TB", content)

    def test_export_report_invalid_format(self):
        """Тест экспорта с неподдерживаемым форматом"""
        project = self.create_test_project()
        report = self.analyzer.analyze_project(project)
        
        output_path = Path(self.temp_dir) / "test_report.xyz"
        
        with self.assertRaises(ValueError):
            self.analyzer.export_report(report, output_path, 'xyz')

    def test_analyze_project_file_not_found(self):
        """Тест обработки отсутствующего проекта"""
        non_existent_path = Path(self.temp_dir) / "non_existent"
        
        with self.assertRaises(FileNotFoundError):
            self.analyzer.analyze_project(non_existent_path)


class TestModuleAnalyzerVisitor(unittest.TestCase):
    """Тесты для ModuleAnalyzerVisitor"""

    def setUp(self):
        """Настройка тестов"""
        self.module_info = ModuleInfo(name="test", path=Path("test.py"))

    def test_visit_import(self):
        """Тест обработки import statements"""
        import ast
        
        # Создаем AST для import
        tree = ast.parse("import module1\nimport module2 as m2")
        visitor = ModuleAnalyzerVisitor(self.module_info)
        visitor.visit(tree)
        
        self.assertIn("module1", self.module_info.imports)
        self.assertIn("module2", self.module_info.imports)

    def test_visit_import_from(self):
        """Тест обработки from ... import statements"""
        import ast
        
        # Создаем AST для from import
        tree = ast.parse("from module1 import Class1\nfrom module2 import func1, func2")
        visitor = ModuleAnalyzerVisitor(self.module_info)
        visitor.visit(tree)
        
        self.assertIn("module1", self.module_info.imports)
        self.assertIn("module2", self.module_info.imports)

    def test_visit_class_def(self):
        """Тест обработки определений классов"""
        import ast
        
        # Создаем AST для класса
        tree = ast.parse("class TestClass:\n    pass")
        visitor = ModuleAnalyzerVisitor(self.module_info)
        visitor.visit(tree)
        
        self.assertIn("TestClass", self.module_info.classes)

    def test_visit_function_def(self):
        """Тест обработки определений функций"""
        import ast
        
        # Создаем AST для функции
        tree = ast.parse("def test_function():\n    pass")
        visitor = ModuleAnalyzerVisitor(self.module_info)
        visitor.visit(tree)
        
        self.assertIn("test_function", self.module_info.functions)


if __name__ == '__main__':
    unittest.main()

