#!/usr/bin/env python3
"""
Упрощенный пример использования анализатора сложности кода
Без зависимости от psutil
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Импортируем только анализатор сложности
from core.complexity_analyzer import ComplexityAnalyzer


def print_file_report(report):
    """Выводит отчет о сложности файла"""
    print(f"\n{'='*60}")
    print(f"ФАЙЛ: {report.file_path}")
    print(f"ОЦЕНКА: {report.grade}")
    print(f"{'='*60}")
    
    # Основные метрики
    print(f"Строки кода: {report.metrics.lines_of_code}")
    print(f"Строки комментариев: {report.metrics.lines_of_comments}")
    print(f"Пустые строки: {report.metrics.blank_lines}")
    print(f"Всего строк: {report.metrics.total_lines}")
    print()
    
    # Метрики сложности
    print(f"Цикломатическая сложность: {report.metrics.cyclomatic_complexity}")
    print(f"Количество функций: {report.metrics.function_count}")
    print(f"Количество классов: {report.metrics.class_count}")
    print(f"Максимальная глубина вложенности: {report.metrics.max_nesting_depth}")
    print(f"Средняя глубина вложенности: {report.metrics.average_nesting_depth:.2f}")
    print()
    
    # Дополнительные метрики
    print(f"Количество импортов: {report.metrics.import_count}")
    print(f"Количество переменных: {report.metrics.variable_count}")
    print(f"Магические числа: {report.metrics.magic_numbers}")
    print(f"Длинные строки (>79 символов): {report.metrics.long_lines}")
    print(f"Длинные функции (>50 строк): {report.metrics.long_functions}")
    print(f"Сложные функции (>10 CC): {report.metrics.complex_functions}")
    print()
    
    # Продвинутые метрики
    print(f"Индекс поддерживаемости: {report.metrics.maintainability_index:.2f}")
    print(f"Объем Холстеда: {report.metrics.halstead_volume:.2f}")
    print(f"Сложность Холстеда: {report.metrics.halstead_difficulty:.2f}")
    print(f"Усилие Холстеда: {report.metrics.halstead_effort:.2f}")
    print()
    
    # Функции
    if report.functions:
        print("ФУНКЦИИ:")
        print("-" * 40)
        for func in report.functions:
            print(f"  {func.name} (строка {func.line_number}):")
            print(f"    Сложность: {func.cyclomatic_complexity}")
            print(f"    Строк кода: {func.lines_of_code}")
            print(f"    Параметры: {func.parameters}")
            print(f"    Глубина вложенности: {func.nesting_depth}")
            print(f"    Переменные: {func.variables}")
            print(f"    Магические числа: {func.magic_numbers}")
            print(f"    Индекс поддерживаемости: {func.maintainability_index:.2f}")
            print()
    
    # Классы
    if report.classes:
        print("КЛАССЫ:")
        print("-" * 40)
        for cls in report.classes:
            print(f"  {cls.name} (строка {cls.line_number}):")
            print(f"    Методы: {cls.methods}")
            print(f"    Атрибуты: {cls.attributes}")
            print(f"    Глубина наследования: {cls.inheritance_depth}")
            print(f"    Сложность: {cls.complexity}")
            print(f"    Строк кода: {cls.lines_of_code}")
            print()
    
    # Проблемы
    if report.issues:
        print("ПРОБЛЕМЫ:")
        print("-" * 40)
        for issue in report.issues:
            print(f"  - {issue}")
        print()


def print_project_report(report):
    """Выводит отчет о сложности проекта"""
    print(f"\n{'='*80}")
    print("ОТЧЕТ О СЛОЖНОСТИ ПРОЕКТА")
    print(f"{'='*80}")
    
    # Общая статистика
    print(f"Всего файлов: {report.total_files}")
    print(f"Всего строк: {report.total_lines}")
    print(f"Средняя сложность: {report.average_complexity:.2f}")
    print()
    
    # Самые сложные файлы
    if report.most_complex_files:
        print("САМЫЕ СЛОЖНЫЕ ФАЙЛЫ:")
        print("-" * 50)
        for i, (file_path, complexity) in enumerate(report.most_complex_files[:5], 1):
            print(f"{i:2}. {file_path}: {complexity}")
        print()
    
    # Самые сложные функции
    if report.most_complex_functions:
        print("САМЫЕ СЛОЖНЫЕ ФУНКЦИИ:")
        print("-" * 50)
        for i, (func_name, complexity) in enumerate(report.most_complex_functions[:5], 1):
            print(f"{i:2}. {func_name}: {complexity}")
        print()
    
    # Распределение оценок
    if report.complexity_distribution:
        print("РАСПРЕДЕЛЕНИЕ ОЦЕНОК:")
        print("-" * 30)
        for grade, count in sorted(report.complexity_distribution.items()):
            percentage = (count / report.total_files) * 100
            print(f"{grade}: {count} файлов ({percentage:.1f}%)")
        print()
    
    # Оценки поддерживаемости
    if report.maintainability_grades:
        print("ОЦЕНКИ ПОДДЕРЖИВАЕМОСТИ:")
        print("-" * 40)
        for grade, count in report.maintainability_grades.items():
            percentage = (count / report.total_files) * 100
            print(f"{grade}: {count} файлов ({percentage:.1f}%)")
        print()
    
    # Рекомендации
    if report.recommendations:
        print("РЕКОМЕНДАЦИИ:")
        print("-" * 30)
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"{i}. {recommendation}")
        print()


def analyze_sample_file():
    """Анализирует сложность примера файла"""
    print("АНАЛИЗ ПРИМЕРА ФАЙЛА")
    print("=" * 50)
    
    # Создаем тестовый файл с разной сложностью
    test_file = Path("test_complexity.py")
    
    test_code = '''
import os
import sys
from typing import List, Dict, Any
from pathlib import Path

class ComplexCalculator:
    """Класс с высокой сложностью для демонстрации"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = {}
        self.history = []
        self.max_iterations = 1000
        self.tolerance = 0.001
    
    def calculate_complex_function(self, data: List[float], 
                                 threshold: float = 0.5,
                                 max_attempts: int = 100) -> Dict[str, Any]:
        """Функция с высокой цикломатической сложностью"""
        result = {"success": False, "data": [], "errors": []}
        
        if not data:
            result["errors"].append("Empty data")
            return result
        
        if threshold <= 0 or threshold > 1:
            result["errors"].append("Invalid threshold")
            return result
        
        if max_attempts <= 0:
            result["errors"].append("Invalid max_attempts")
            return result
        
        processed_data = []
        attempt_count = 0
        
        for value in data:
            if value < 0:
                continue
            
            if value > self.max_iterations:
                result["errors"].append(f"Value too large: {value}")
                continue
            
            processed_value = value
            iteration_count = 0
            
            while processed_value > threshold and iteration_count < max_attempts:
                if processed_value > 100:
                    processed_value = processed_value / 2
                elif processed_value > 50:
                    processed_value = processed_value * 0.8
                elif processed_value > 10:
                    processed_value = processed_value - 1
                else:
                    processed_value = processed_value * 0.9
                
                iteration_count += 1
                
                if iteration_count % 10 == 0:
                    if processed_value < threshold * 0.1:
                        break
            
            if iteration_count >= max_attempts:
                result["errors"].append(f"Max attempts reached for value {value}")
            else:
                processed_data.append(processed_value)
                attempt_count += 1
        
        if processed_data:
            result["success"] = True
            result["data"] = processed_data
            result["attempts"] = attempt_count
        
        return result
    
    def validate_data(self, data: Any) -> bool:
        """Простая функция валидации"""
        if isinstance(data, list):
            return all(isinstance(x, (int, float)) for x in data)
        return False

def simple_function():
    """Простая функция для сравнения"""
    return "Hello, World!"

def medium_complexity_function(items: List[str]) -> List[str]:
    """Функция средней сложности"""
    result = []
    
    for item in items:
        if item.startswith("test"):
            result.append(item.upper())
        elif item.endswith(".py"):
            result.append(item.lower())
        else:
            result.append(item)
    
    return result

# Глобальные переменные
GLOBAL_CONFIG = {"debug": True, "timeout": 30}
DEFAULT_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

if __name__ == "__main__":
    calculator = ComplexCalculator(GLOBAL_CONFIG)
    result = calculator.calculate_complex_function(DEFAULT_VALUES)
    print(result)
'''
    
    # Записываем тестовый файл
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    try:
        # Анализируем файл
        analyzer = ComplexityAnalyzer()
        report = analyzer.analyze_file(test_file)
        print_file_report(report)
        
    finally:
        # Удаляем тестовый файл
        test_file.unlink(missing_ok=True)


def analyze_specific_files():
    """Анализирует сложность конкретных файлов"""
    print("АНАЛИЗ КОНКРЕТНЫХ ФАЙЛОВ")
    print("=" * 50)
    
    project_dir = Path(__file__).parent.parent
    files_to_analyze = [
        "src/core/complexity_analyzer.py",
        "examples/complexity_simple_example.py"
    ]
    
    analyzer = ComplexityAnalyzer()
    
    for file_path_str in files_to_analyze:
        file_path = project_dir / file_path_str
        if file_path.exists():
            print(f"\nАнализируем: {file_path_str}")
            try:
                report = analyzer.analyze_file(file_path)
                print(f"Оценка: {report.grade}, Сложность: {report.metrics.cyclomatic_complexity}")
                print(f"Функций: {report.metrics.function_count}, Классов: {report.metrics.class_count}")
                print(f"Поддерживаемость: {report.metrics.maintainability_index:.2f}")
            except Exception as e:
                print(f"Ошибка: {e}")
        else:
            print(f"Файл не найден: {file_path_str}")


def analyze_small_project():
    """Анализирует сложность небольшого проекта"""
    print("АНАЛИЗ НЕБОЛЬШОГО ПРОЕКТА")
    print("=" * 50)
    
    # Создаем временную директорию с несколькими файлами
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Создаем несколько файлов разной сложности
        files_content = [
            ("simple.py", "def simple(): return 42"),
            ("medium.py", """
def medium():
    if True:
        return 1
    else:
        return 2
"""),
            ("complex.py", """
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
            file_path = temp_path / name
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Анализируем проект
        analyzer = ComplexityAnalyzer()
        report = analyzer.analyze_project(temp_path)
        print_project_report(report)
        
    finally:
        # Удаляем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Основная функция"""
    print("АНАЛИЗАТОР СЛОЖНОСТИ КОДА")
    print("=" * 60)
    
    try:
        # Анализ примера файла
        analyze_sample_file()
        
        # Анализ конкретных файлов
        analyze_specific_files()
        
        # Анализ небольшого проекта
        analyze_small_project()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
