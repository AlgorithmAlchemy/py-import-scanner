#!/usr/bin/env python3
"""
Тесты для анализатора качества кода
"""
import unittest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.code_quality_analyzer import (
    CodeQualityAnalyzer, PEP8Violation, FunctionQuality,
    CognitiveComplexity, CodeDuplication, CodeQualityReport,
    ProjectQualityReport
)


class TestCodeQualityAnalyzer(unittest.TestCase):
    def setUp(self):
        """Настройка тестов"""
        self.analyzer = CodeQualityAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Очистка после тестов"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, name: str, content: str) -> Path:
        """Создает тестовый файл"""
        file_path = self.temp_path / name
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_pep8_violations_detection(self):
        """Тест обнаружения PEP8 нарушений"""
        content = '''def bad_function():
    x=1+2  # E225: missing whitespace around operator
    if x==None:  # E711: comparison to None
        print("bad")
    return x
'''
        file_path = self.create_test_file("test_pep8.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertGreater(len(report.pep8_violations), 0)
        self.assertIsInstance(report.pep8_violations[0], PEP8Violation)
    
    def test_cyclomatic_complexity_calculation(self):
        """Тест вычисления цикломатической сложности"""
        content = '''def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "very large"
            else:
                return "large"
        else:
            return "small"
    else:
        return "negative"
'''
        file_path = self.create_test_file("test_complexity.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertEqual(len(report.functions_quality), 1)
        func = report.functions_quality[0]
        self.assertEqual(func.cyclomatic_complexity, 5)  # 1 + 4 if statements
    
    def test_cognitive_complexity_calculation(self):
        """Тест вычисления когнитивной сложности"""
        content = '''def cognitive_function(x, y, z):
    if x > 0 and y > 0 and z > 0:
        if x + y > z:
            return True
        else:
            return False
    else:
        return False
'''
        file_path = self.create_test_file("test_cognitive.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertEqual(len(report.cognitive_complexity), 1)
        cognitive = report.cognitive_complexity[0]
        self.assertGreater(cognitive.complexity, 0)
        self.assertIn('if', cognitive.factors)
    
    def test_code_duplication_detection(self):
        """Тест обнаружения дублирования кода"""
        content = '''def function1():
    for i in range(10):
        if i % 2 == 0:
            print(f"Even: {i}")
        else:
            print(f"Odd: {i}")

def function2():
    for i in range(10):
        if i % 2 == 0:
            print(f"Even: {i}")
        else:
            print(f"Odd: {i}")
'''
        file_path = self.create_test_file("test_duplication.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertGreater(len(report.code_duplications), 0)
        dup = report.code_duplications[0]
        self.assertGreater(dup.occurrences, 1)
    
    def test_function_quality_analysis(self):
        """Тест анализа качества функций"""
        content = '''def good_function(x):
    return x * 2

def bad_function(param1, param2, param3, param4, param5, param6):
    result = 0
    if param1 > 0:
        if param2 > 10:
            if param3 > 100:
                if param4 > 1000:
                    if param5 > 10000:
                        if param6 > 100000:
                            result = 1
                        else:
                            result = 2
                    else:
                        result = 3
                else:
                    result = 4
            else:
                result = 5
        else:
            result = 6
    else:
        result = 7
    return result
'''
        file_path = self.create_test_file("test_quality.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertEqual(len(report.functions_quality), 2)
        
        # Хорошая функция
        good_func = next(f for f in report.functions_quality if f.name == 'good_function')
        self.assertEqual(good_func.cyclomatic_complexity, 1)
        self.assertEqual(len(good_func.issues), 0)
        
        # Плохая функция
        bad_func = next(f for f in report.functions_quality if f.name == 'bad_function')
        self.assertGreater(bad_func.cyclomatic_complexity, 10)
        self.assertGreater(len(bad_func.issues), 0)
    
    def test_quality_score_calculation(self):
        """Тест вычисления общего балла качества"""
        content = '''def perfect_function():
    return "perfect"

def terrible_function(param1, param2, param3, param4, param5, param6, param7):
    x=1+2
    if param1>0:
        if param2>10:
            if param3>100:
                if param4>1000:
                    if param5>10000:
                        if param6>100000:
                            if param7>1000000:
                                return 1
                            else:
                                return 2
                        else:
                            return 3
                    else:
                        return 4
                else:
                    return 5
            else:
                return 6
        else:
            return 7
    else:
        return 8
'''
        file_path = self.create_test_file("test_score.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertGreater(report.overall_score, 0)
        self.assertLessEqual(report.overall_score, 100)
        self.assertGreater(report.issues_count, 0)
    
    def test_project_analysis(self):
        """Тест анализа проекта"""
        # Создаем несколько файлов
        files_content = [
            ("good.py", "def good(): return True"),
            ("bad.py", "def bad(x,y,z):\n    if x>0:\n        if y>0:\n            if z>0:\n                return True\n    return False"),
            ("ugly.py", "def ugly(param1,param2,param3,param4,param5,param6,param7,param8):\n    x=1+2\n    if param1>0:\n        if param2>10:\n            if param3>100:\n                return 1\n    return 0")
        ]
        
        for name, content in files_content:
            self.create_test_file(name, content)
        
        report = self.analyzer.analyze_project(self.temp_path)
        
        self.assertEqual(report.total_files, 3)
        self.assertGreater(report.total_issues, 0)
        self.assertGreater(report.average_score, 0)
        self.assertLessEqual(report.average_score, 100)
        self.assertGreater(len(report.worst_files), 0)
        self.assertGreater(len(report.best_files), 0)
    
    def test_recommendations_generation(self):
        """Тест генерации рекомендаций"""
        content = '''def problematic_function(param1, param2, param3, param4, param5, param6):
    x=1+2
    if param1>0:
        if param2>10:
            if param3>100:
                if param4>1000:
                    if param5>10000:
                        if param6>100000:
                            return 1
                        else:
                            return 2
                    else:
                        return 3
                else:
                    return 4
            else:
                return 5
        else:
            return 6
    else:
        return 7
'''
        file_path = self.create_test_file("test_recommendations.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        self.assertGreater(len(report.recommendations), 0)
        recommendations_text = ' '.join(report.recommendations).lower()
        self.assertIn('pep8', recommendations_text or 'complex', recommendations_text)
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        # Тест с несуществующим файлом
        non_existent_file = self.temp_path / "non_existent.py"
        report = self.analyzer.analyze_file(non_existent_file)
        
        self.assertEqual(report.file_path, non_existent_file)
        self.assertEqual(report.overall_score, 0.0)
        self.assertEqual(report.issues_count, 0)


class TestPEP8Violation(unittest.TestCase):
    def test_pep8_violation_creation(self):
        """Тест создания PEP8 нарушения"""
        violation = PEP8Violation(
            line_number=10,
            column=5,
            code='E501',
            message='Line too long',
            severity='error'
        )
        
        self.assertEqual(violation.line_number, 10)
        self.assertEqual(violation.column, 5)
        self.assertEqual(violation.code, 'E501')
        self.assertEqual(violation.message, 'Line too long')
        self.assertEqual(violation.severity, 'error')


class TestFunctionQuality(unittest.TestCase):
    def test_function_quality_creation(self):
        """Тест создания качества функции"""
        func_quality = FunctionQuality(
            name='test_function',
            line_number=5,
            cyclomatic_complexity=3,
            cognitive_complexity=2,
            lines_of_code=10,
            parameters_count=2,
            nesting_depth=1
        )
        
        self.assertEqual(func_quality.name, 'test_function')
        self.assertEqual(func_quality.cyclomatic_complexity, 3)
        self.assertEqual(func_quality.cognitive_complexity, 2)
        self.assertEqual(func_quality.lines_of_code, 10)
        self.assertEqual(func_quality.parameters_count, 2)
        self.assertEqual(func_quality.nesting_depth, 1)
        self.assertEqual(len(func_quality.issues), 0)


class TestCognitiveComplexity(unittest.TestCase):
    def test_cognitive_complexity_creation(self):
        """Тест создания когнитивной сложности"""
        cognitive = CognitiveComplexity(
            function_name='test_func',
            line_number=10,
            complexity=5,
            factors=['if', 'for', 'and']
        )
        
        self.assertEqual(cognitive.function_name, 'test_func')
        self.assertEqual(cognitive.line_number, 10)
        self.assertEqual(cognitive.complexity, 5)
        self.assertEqual(len(cognitive.factors), 3)


class TestCodeDuplication(unittest.TestCase):
    def test_code_duplication_creation(self):
        """Тест создания дублирования кода"""
        duplication = CodeDuplication(
            block_hash='abc123',
            lines=[10, 25],
            content='print("hello")',
            occurrences=2,
            similarity=0.95
        )
        
        self.assertEqual(duplication.block_hash, 'abc123')
        self.assertEqual(duplication.lines, [10, 25])
        self.assertEqual(duplication.content, 'print("hello")')
        self.assertEqual(duplication.occurrences, 2)
        self.assertEqual(duplication.similarity, 0.95)


if __name__ == "__main__":
    unittest.main()
