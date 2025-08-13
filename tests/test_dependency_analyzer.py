"""
Тесты для анализатора зависимостей
"""
import unittest
from pathlib import Path
import tempfile
import sys

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.dependency_analyzer import (
    DependencyAnalyzer, DependencyReport, PackageInfo, 
    Vulnerability, LicenseInfo, DuplicateDependency
)


class TestDependencyAnalyzer(unittest.TestCase):
    """Тесты для DependencyAnalyzer"""

    def setUp(self):
        """Настройка тестов"""
        self.analyzer = DependencyAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        self.test_requirements = Path(self.temp_dir) / "requirements.txt"

    def tearDown(self):
        """Очистка после тестов"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_requirements(self, content: str) -> Path:
        """Создает тестовый файл requirements.txt"""
        with open(self.test_requirements, 'w', encoding='utf-8') as f:
            f.write(content)
        return self.test_requirements

    def test_parse_requirements_basic(self):
        """Тест базового парсинга requirements"""
        content = """requests>=2.25.0
numpy==1.21.0
pandas>=1.3.0
"""
        self.create_test_requirements(content)
        
        packages = self.analyzer._parse_requirements(self.test_requirements)
        
        self.assertEqual(len(packages), 3)
        self.assertEqual(packages[0].name, "requests")
        self.assertEqual(packages[0].version, ">=2.25.0")
        self.assertEqual(packages[1].name, "numpy")
        self.assertEqual(packages[1].version, "==1.21.0")

    def test_parse_requirements_with_comments(self):
        """Тест парсинга requirements с комментариями"""
        content = """# Основные зависимости
requests>=2.25.0
# Научные вычисления
numpy==1.21.0
# Пустая строка

pandas>=1.3.0
"""
        self.create_test_requirements(content)
        
        packages = self.analyzer._parse_requirements(self.test_requirements)
        
        self.assertEqual(len(packages), 3)
        self.assertEqual(packages[0].name, "requests")
        self.assertEqual(packages[1].name, "numpy")
        self.assertEqual(packages[2].name, "pandas")

    def test_parse_requirements_invalid_line(self):
        """Тест обработки некорректных строк"""
        content = """requests>=2.25.0
invalid-package-name
numpy==1.21.0
"""
        self.create_test_requirements(content)
        
        packages = self.analyzer._parse_requirements(self.test_requirements)
        
        # Должны быть обработаны только корректные строки
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[0].name, "requests")
        self.assertEqual(packages[1].name, "numpy")

    def test_license_compatibility_check(self):
        """Тест проверки совместимости лицензий"""
        # Совместимые лицензии
        self.assertTrue(self.analyzer._check_license_compatibility("MIT"))
        self.assertTrue(self.analyzer._check_license_compatibility("Apache-2.0"))
        self.assertTrue(self.analyzer._check_license_compatibility("BSD-3-Clause"))
        
        # Ограничительные лицензии
        self.assertFalse(self.analyzer._check_license_compatibility("GPL-3.0"))
        self.assertFalse(self.analyzer._check_license_compatibility("AGPL-3.0"))
        
        # Неизвестные лицензии
        self.assertTrue(self.analyzer._check_license_compatibility("Unknown"))
        self.assertTrue(self.analyzer._check_license_compatibility(""))

    def test_extract_version(self):
        """Тест извлечения версии из строки requirements"""
        # Простые версии
        self.assertEqual(
            str(self.analyzer._extract_version("2.25.0")), 
            "2.25.0"
        )
        
        # Версии с операторами
        self.assertEqual(
            str(self.analyzer._extract_version(">=2.25.0")), 
            "2.25.0"
        )
        self.assertEqual(
            str(self.analyzer._extract_version("==1.21.0")), 
            "1.21.0"
        )
        self.assertEqual(
            str(self.analyzer._extract_version("~=1.3.0")), 
            "1.3.0"
        )
        
        # Некорректные версии
        self.assertIsNone(self.analyzer._extract_version("invalid"))
        self.assertIsNone(self.analyzer._extract_version(""))

    def test_find_duplicate_dependencies(self):
        """Тест поиска дублирующихся зависимостей"""
        # Создаем несколько файлов requirements
        req1 = Path(self.temp_dir) / "requirements.txt"
        req2 = Path(self.temp_dir) / "requirements-dev.txt"
        
        with open(req1, 'w', encoding='utf-8') as f:
            f.write("requests>=2.25.0\nnumpy==1.21.0\n")
        
        with open(req2, 'w', encoding='utf-8') as f:
            f.write("requests>=2.28.0\npandas>=1.3.0\n")
        
        duplicates = self.analyzer._find_duplicate_dependencies(req1)
        
        # Должен найти дубликат requests
        self.assertGreater(len(duplicates), 0)
        requests_dup = next((d for d in duplicates if d.package_name == "requests"), None)
        self.assertIsNotNone(requests_dup)
        self.assertEqual(len(requests_dup.versions), 2)

    def test_generate_recommendations(self):
        """Тест генерации рекомендаций"""
        report = DependencyReport()
        
        # Без проблем
        recommendations = self.analyzer._generate_recommendations(report)
        self.assertIn("хорошем состоянии", recommendations[0])
        
        # С уязвимостями
        report.vulnerable_packages = 2
        recommendations = self.analyzer._generate_recommendations(report)
        self.assertIn("уязвимых пакетов", recommendations[0])
        
        # С устаревшими пакетами
        report.outdated_count = 3
        recommendations = self.analyzer._generate_recommendations(report)
        self.assertIn("устаревших пакетов", recommendations[0])

    def test_analyze_requirements_integration(self):
        """Интеграционный тест анализа requirements"""
        content = """requests>=2.25.0
numpy==1.21.0
pandas>=1.3.0
"""
        self.create_test_requirements(content)
        
        report = self.analyzer.analyze_requirements(self.test_requirements)
        
        # Проверяем базовую структуру отчета
        self.assertIsInstance(report, DependencyReport)
        self.assertEqual(report.total_packages, 3)
        self.assertIsInstance(report.packages, list)
        self.assertIsInstance(report.vulnerabilities, list)
        self.assertIsInstance(report.recommendations, list)

    def test_export_report_json(self):
        """Тест экспорта в JSON"""
        report = DependencyReport()
        report.total_packages = 2
        report.packages = [
            PackageInfo(name="requests", version=">=2.25.0"),
            PackageInfo(name="numpy", version="==1.21.0")
        ]
        
        output_path = Path(self.temp_dir) / "test_report.json"
        self.analyzer.export_report(report, output_path, 'json')
        
        self.assertTrue(output_path.exists())
        
        # Проверяем содержимое
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['summary']['total_packages'], 2)
        self.assertEqual(len(data['packages']), 2)

    def test_export_report_csv(self):
        """Тест экспорта в CSV"""
        report = DependencyReport()
        report.packages = [
            PackageInfo(name="requests", version=">=2.25.0"),
            PackageInfo(name="numpy", version="==1.21.0")
        ]
        
        output_path = Path(self.temp_dir) / "test_report.csv"
        self.analyzer.export_report(report, output_path, 'csv')
        
        self.assertTrue(output_path.exists())
        
        # Проверяем содержимое
        with open(output_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.assertGreater(len(lines), 1)  # Заголовок + данные
        self.assertIn("Package", lines[0])
        self.assertIn("requests", lines[1])

    def test_export_report_txt(self):
        """Тест экспорта в TXT"""
        report = DependencyReport()
        report.total_packages = 2
        report.vulnerable_packages = 1
        report.recommendations = ["Тестовая рекомендация"]
        
        output_path = Path(self.temp_dir) / "test_report.txt"
        self.analyzer.export_report(report, output_path, 'txt')
        
        self.assertTrue(output_path.exists())
        
        # Проверяем содержимое
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("АНАЛИЗ ЗАВИСИМОСТЕЙ", content)
        self.assertIn("Всего пакетов: 2", content)
        self.assertIn("Тестовая рекомендация", content)

    def test_export_report_invalid_format(self):
        """Тест экспорта с неподдерживаемым форматом"""
        report = DependencyReport()
        output_path = Path(self.temp_dir) / "test_report.xyz"
        
        with self.assertRaises(ValueError):
            self.analyzer.export_report(report, output_path, 'xyz')

    def test_analyze_requirements_file_not_found(self):
        """Тест обработки отсутствующего файла"""
        non_existent_path = Path(self.temp_dir) / "non_existent.txt"
        
        with self.assertRaises(FileNotFoundError):
            self.analyzer.analyze_requirements(non_existent_path)


if __name__ == '__main__':
    unittest.main()

