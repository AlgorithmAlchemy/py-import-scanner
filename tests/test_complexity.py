#!/usr/bin/env python3
"""
Тесты для анализатора сложности кода
"""

import unittest
from pathlib import Path
import tempfile
import sys

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.complexity_analyzer import (
    ComplexityAnalyzer, ComplexityMetrics, FunctionMetrics, 
    ClassMetrics, FileComplexityReport, ProjectComplexityReport
)


class TestComplexityAnalyzer(unittest.TestCase):
    """Тесты для анализатора сложности"""
    
    def setUp(self):
        """Настройка тестов"""
        self.analyzer = ComplexityAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Очистка после тестов"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, name: str, content: str) -> Path:
        """Создает тестовый файл"""
        file_path = self.temp_path / name
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_basic_metrics_calculation(self):
        """Тест вычисления базовых метрик"""
        content = '''
# Простой тестовый файл
import os
import sys

def simple_function():
    """Простая функция"""
    return "Hello"

class SimpleClass:
    """Простой класс"""
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

# Основной код
if __name__ == "__main__":
    obj = SimpleClass()
    print(obj.get_value())
'''
        
        file_path = self.create_test_file("test_basic.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        # Проверяем базовые метрики
        self.assertGreater(report.metrics.lines_of_code, 0)
        self.assertGreater(report.metrics.lines_of_comments, 0)
        self.assertEqual(report.metrics.function_count, 2)  # simple_function + get_value
        self.assertEqual(report.metrics.class_count, 1)     # SimpleClass
        self.assertGreater(report.metrics.import_count, 0)
    
    def test_cyclomatic_complexity(self):
        """Тест вычисления цикломатической сложности"""
        content = '''
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return "very large"
            else:
                return "large"
        else:
            return "small"
    else:
        if x < -10:
            return "very small"
        else:
            return "negative"
    
    for i in range(x):
        if i % 2 == 0:
            continue
        else:
            break
    
    while x > 0:
        x -= 1
        if x == 5:
            break
    
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = 0
    
    return result
'''
        
        file_path = self.create_test_file("test_complexity.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        # Функция должна иметь высокую цикломатическую сложность
        self.assertGreater(report.metrics.cyclomatic_complexity, 10)
        self.assertEqual(len(report.functions), 1)
        self.assertGreater(report.functions[0].cyclomatic_complexity, 10)
    
    def test_nesting_depth(self):
        """Тест вычисления глубины вложенности"""
        content = '''
def deeply_nested():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            return "deep"
                        else:
                            return "not so deep"
                    else:
                        return "medium"
                else:
                    return "shallow"
            else:
                return "very shallow"
        else:
            return "almost surface"
    else:
        return "surface"
'''
        
        file_path = self.create_test_file("test_nesting.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        # Проверяем максимальную глубину вложенности
        self.assertGreaterEqual(report.metrics.max_nesting_depth, 6)
        self.assertGreater(report.metrics.average_nesting_depth, 0)
    
    def test_function_metrics(self):
        """Тест метрик функций"""
        content = '''
def function_with_many_params(a, b, c, d, e, f, g, h, i, j):
    """Функция с многими параметрами"""
    result = a + b + c + d + e + f + g + h + i + j
    magic_number = 42
    another_magic = 100
    
    if result > magic_number:
        if result > another_magic:
            return "very large"
        else:
            return "large"
    else:
        return "small"

def simple_function():
    return "simple"
'''
        
        file_path = self.create_test_file("test_functions.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        # Проверяем метрики функций
        self.assertEqual(len(report.functions), 2)
        
        # Первая функция должна иметь много параметров и магических чисел
        complex_func = next(f for f in report.functions if f.name == "function_with_many_params")
        self.assertEqual(complex_func.parameters, 10)
        self.assertGreaterEqual(complex_func.magic_numbers, 2)
        self.assertGreater(complex_func.cyclomatic_complexity, 1)
    
    def test_class_metrics(self):
        """Тест метрик классов"""
        content = '''
class BaseClass:
    """Базовый класс"""
    def __init__(self):
        self.base_value = 1

class DerivedClass(BaseClass):
    """Производный класс"""
    def __init__(self):
        super().__init__()
        self.derived_value = 2
        self.another_value = 3
    
    def method1(self):
        return self.derived_value
    
    def method2(self):
        return self.another_value
    
    def complex_method(self):
        if self.derived_value > 0:
            if self.another_value > 0:
                return "both positive"
            else:
                return "only derived positive"
        else:
            return "derived not positive"
'''
        
        file_path = self.create_test_file("test_classes.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        # Проверяем метрики классов
        self.assertEqual(len(report.classes), 2)
        
        # Проверяем производный класс
        derived_class = next(c for c in report.classes if c.name == "DerivedClass")
        self.assertEqual(derived_class.methods, 3)  # method1, method2, complex_method
        self.assertGreaterEqual(derived_class.attributes, 2)  # derived_value, another_value
        self.assertEqual(derived_class.inheritance_depth, 1)  # наследует от BaseClass
    
    def test_maintainability_index(self):
        """Тест вычисления индекса поддерживаемости"""
        # Простой код должен иметь высокий индекс поддерживаемости
        simple_content = '''
def simple():
    return 42
'''
        
        simple_file = self.create_test_file("simple.py", simple_content)
        simple_report = self.analyzer.analyze_file(simple_file)
        
        # Сложный код должен иметь низкий индекс поддерживаемости
        complex_content = '''
def very_complex_function(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t):
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    if i > 0:
                                        if j > 0:
                                            if k > 0:
                                                if l > 0:
                                                    if m > 0:
                                                        if n > 0:
                                                            if o > 0:
                                                                if p > 0:
                                                                    if q > 0:
                                                                        if r > 0:
                                                                            if s > 0:
                                                                                if t > 0:
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
                                                        else:
                                                            result = 8
                                                    else:
                                                        result = 9
                                                else:
                                                    result = 10
                                            else:
                                                result = 11
                                        else:
                                            result = 12
                                    else:
                                        result = 13
                                else:
                                    result = 14
                            else:
                                result = 15
                        else:
                            result = 16
                    else:
                        result = 17
                else:
                    result = 18
            else:
                result = 19
        else:
            result = 20
    else:
        result = 21
    
    return result
'''
        
        complex_file = self.create_test_file("complex.py", complex_content)
        complex_report = self.analyzer.analyze_file(complex_file)
        
        # Простой код должен иметь более высокий индекс поддерживаемости
        self.assertGreater(simple_report.metrics.maintainability_index, 
                          complex_report.metrics.maintainability_index)
    
    def test_grade_calculation(self):
        """Тест вычисления оценок"""
        # Простой код должен получить высокую оценку
        simple_content = '''
def simple():
    return 42
'''
        
        simple_file = self.create_test_file("simple_grade.py", simple_content)
        simple_report = self.analyzer.analyze_file(simple_file)
        
        # Сложный код должен получить низкую оценку
        complex_content = '''
def complex():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            if True:
                                if True:
                                    if True:
                                        if True:
                                            return "very deep"
                                        else:
                                            return "deep"
                                    else:
                                        return "medium"
                                else:
                                    return "shallow"
                            else:
                                return "very shallow"
                        else:
                            return "almost surface"
                    else:
                        return "surface"
                else:
                    return "above surface"
            else:
                return "high above"
        else:
            return "very high"
    else:
        return "highest"
'''
        
        complex_file = self.create_test_file("complex_grade.py", complex_content)
        complex_report = self.analyzer.analyze_file(complex_file)
        
        # Простой код должен получить более высокую оценку
        grade_order = ["A", "B", "C", "D", "F"]
        simple_grade_index = grade_order.index(simple_report.grade)
        complex_grade_index = grade_order.index(complex_report.grade)
        
        self.assertLess(simple_grade_index, complex_grade_index)
    
    def test_project_analysis(self):
        """Тест анализа проекта"""
        # Создаем несколько файлов
        files_content = [
            ("file1.py", "def simple(): return 1"),
            ("file2.py", "def medium(): if True: return 1 else: return 2"),
            ("file3.py", """
def complex():
    if True:
        if True:
            if True:
                if True:
                    return 1
                else:
                    return 2
            else:
                return 3
        else:
            return 4
    else:
        return 5
""")
        ]
        
        for name, content in files_content:
            self.create_test_file(name, content)
        
        # Анализируем проект
        report = self.analyzer.analyze_project(self.temp_path)
        
        # Проверяем результаты
        self.assertEqual(report.total_files, 3)
        self.assertGreater(report.total_lines, 0)
        self.assertGreater(report.average_complexity, 0)
        self.assertEqual(len(report.most_complex_files), 3)
        self.assertGreater(len(report.recommendations), 0)
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        # Тест с несуществующим файлом
        non_existent_file = self.temp_path / "non_existent.py"
        report = self.analyzer.analyze_file(non_existent_file)
        
        self.assertEqual(report.grade, "F")
        self.assertGreater(len(report.issues), 0)
        
        # Тест с файлом с синтаксической ошибкой
        invalid_content = '''
def invalid_function(
    # Незакрытая скобка
'''
        
        invalid_file = self.create_test_file("invalid.py", invalid_content)
        report = self.analyzer.analyze_file(invalid_file)
        
        self.assertEqual(report.grade, "F")
        self.assertGreater(len(report.issues), 0)
    
    def test_halstead_metrics(self):
        """Тест метрик Холстеда"""
        content = '''
def calculate(a, b, c):
    result = a + b * c
    if result > 10:
        return result / 2
    else:
        return result * 2
'''
        
        file_path = self.create_test_file("halstead.py", content)
        report = self.analyzer.analyze_file(file_path)
        
        # Проверяем, что метрики Холстеда вычислены
        self.assertGreaterEqual(report.metrics.halstead_volume, 0)
        self.assertGreaterEqual(report.metrics.halstead_difficulty, 0)
        self.assertGreaterEqual(report.metrics.halstead_effort, 0)


class TestComplexityMetrics(unittest.TestCase):
    """Тесты для метрик сложности"""
    
    def test_complexity_metrics_creation(self):
        """Тест создания метрик сложности"""
        metrics = ComplexityMetrics()
        
        self.assertEqual(metrics.lines_of_code, 0)
        self.assertEqual(metrics.cyclomatic_complexity, 0)
        self.assertEqual(metrics.function_count, 0)
        self.assertEqual(metrics.class_count, 0)
        self.assertEqual(metrics.maintainability_index, 0.0)
    
    def test_function_metrics_creation(self):
        """Тест создания метрик функции"""
        func_metrics = FunctionMetrics(
            name="test_function",
            line_number=10,
            cyclomatic_complexity=5,
            lines_of_code=20,
            parameters=3,
            nesting_depth=2,
            variables=5,
            magic_numbers=1,
            maintainability_index=75.0
        )
        
        self.assertEqual(func_metrics.name, "test_function")
        self.assertEqual(func_metrics.line_number, 10)
        self.assertEqual(func_metrics.cyclomatic_complexity, 5)
        self.assertEqual(func_metrics.lines_of_code, 20)
        self.assertEqual(func_metrics.parameters, 3)
        self.assertEqual(func_metrics.nesting_depth, 2)
        self.assertEqual(func_metrics.variables, 5)
        self.assertEqual(func_metrics.magic_numbers, 1)
        self.assertEqual(func_metrics.maintainability_index, 75.0)
    
    def test_class_metrics_creation(self):
        """Тест создания метрик класса"""
        class_metrics = ClassMetrics(
            name="TestClass",
            line_number=15,
            methods=5,
            attributes=3,
            inheritance_depth=1,
            complexity=8,
            lines_of_code=50
        )
        
        self.assertEqual(class_metrics.name, "TestClass")
        self.assertEqual(class_metrics.line_number, 15)
        self.assertEqual(class_metrics.methods, 5)
        self.assertEqual(class_metrics.attributes, 3)
        self.assertEqual(class_metrics.inheritance_depth, 1)
        self.assertEqual(class_metrics.complexity, 8)
        self.assertEqual(class_metrics.lines_of_code, 50)


if __name__ == "__main__":
    unittest.main()
