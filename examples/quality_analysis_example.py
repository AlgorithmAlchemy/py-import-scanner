#!/usr/bin/env python3
"""
Пример использования анализатора качества кода
Демонстрирует анализ PEP8, цикломатической сложности, когнитивной сложности и дублирования кода
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.code_quality_analyzer import CodeQualityAnalyzer
from core.scan_service import ScanService
from core.configuration import Configuration


def print_file_quality_report(report):
    """Выводит отчет о качестве файла"""
    print(f"\n{'='*80}")
    print(f"ОТЧЕТ О КАЧЕСТВЕ КОДА: {report.file_path.name}")
    print(f"{'='*80}")
    print(f"Общий балл: {report.overall_score:.1f}/100")
    print(f"Количество проблем: {report.issues_count}")
    
    # PEP8 нарушения
    if report.pep8_violations:
        print(f"\n🔴 PEP8 НАРУШЕНИЯ ({len(report.pep8_violations)}):")
        for violation in report.pep8_violations[:5]:  # Показываем первые 5
            print(f"  Строка {violation.line_number}: {violation.message} ({violation.code})")
        if len(report.pep8_violations) > 5:
            print(f"  ... и еще {len(report.pep8_violations) - 5} нарушений")
    
    # Качество функций
    if report.functions_quality:
        print(f"\n📊 КАЧЕСТВО ФУНКЦИЙ ({len(report.functions_quality)}):")
        for func in report.functions_quality:
            print(f"  {func.name} (строка {func.line_number}):")
            print(f"    Цикломатическая сложность: {func.cyclomatic_complexity}")
            print(f"    Когнитивная сложность: {func.cognitive_complexity}")
            print(f"    Строк кода: {func.lines_of_code}")
            print(f"    Параметров: {func.parameters_count}")
            print(f"    Глубина вложенности: {func.nesting_depth}")
            if func.issues:
                print(f"    ⚠️ Проблемы: {', '.join(func.issues)}")
    
    # Когнитивная сложность
    complex_functions = [c for c in report.cognitive_complexity if c.complexity > 10]
    if complex_functions:
        print(f"\n🧠 ВЫСОКАЯ КОГНИТИВНАЯ СЛОЖНОСТЬ:")
        for func in complex_functions:
            print(f"  {func.function_name}: {func.complexity} (факторы: {', '.join(func.factors)})")
    
    # Дублирование кода
    if report.code_duplications:
        print(f"\n🔄 ДУБЛИРОВАНИЕ КОДА:")
        for dup in report.code_duplications[:3]:  # Показываем первые 3
            print(f"  {dup.occurrences} вхождений (строки: {dup.lines})")
            print(f"    Схожесть: {dup.similarity:.2f}")
            print(f"    Содержимое: {dup.content[:100]}...")
    
    # Рекомендации
    if report.recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for rec in report.recommendations:
            print(f"  • {rec}")


def print_project_quality_report(report):
    """Выводит отчет о качестве проекта"""
    print(f"\n{'='*80}")
    print(f"ОТЧЕТ О КАЧЕСТВЕ ПРОЕКТА")
    print(f"{'='*80}")
    print(f"Всего файлов: {report.total_files}")
    print(f"Общее количество проблем: {report.total_issues}")
    print(f"Средний балл: {report.average_score:.1f}/100")
    
    # Худшие файлы
    if report.worst_files:
        print(f"\n🔴 ХУДШИЕ ФАЙЛЫ:")
        for file in report.worst_files:
            print(f"  • {file}")
    
    # Лучшие файлы
    if report.best_files:
        print(f"\n✅ ЛУЧШИЕ ФАЙЛЫ:")
        for file in report.best_files:
            print(f"  • {file}")
    
    # Самые сложные функции
    if report.most_complex_functions:
        print(f"\n🧠 САМЫЕ СЛОЖНЫЕ ФУНКЦИИ:")
        for func in report.most_complex_functions[:5]:
            print(f"  • {func}")
    
    # Дублирования
    if report.duplicate_blocks:
        print(f"\n🔄 ДУБЛИРОВАНИЯ КОДА:")
        for dup in report.duplicate_blocks[:5]:
            print(f"  • {dup}")
    
    # Рекомендации
    if report.recommendations:
        print(f"\n💡 ОБЩИЕ РЕКОМЕНДАЦИИ:")
        for rec in report.recommendations:
            print(f"  • {rec}")


def create_test_file_with_issues():
    """Создает тестовый файл с различными проблемами качества"""
    test_file = Path("test_quality_issues.py")
    
    content = '''#!/usr/bin/env python3
"""
Тестовый файл с проблемами качества кода
"""

import os,sys  # PEP8: E401 - multiple imports on one line
from pathlib import Path

# PEP8: E501 - line too long
def very_long_function_name_with_many_parameters(param1,param2,param3,param4,param5,param6,param7,param8,param9,param10):
    """Функция с множеством параметров и высокой сложностью"""
    result = 0
    if param1 > 0:
        if param2 > 10:
            if param3 > 100:
                if param4 > 1000:
                    if param5 > 10000:
                        if param6 > 100000:
                            if param7 > 1000000:
                                if param8 > 10000000:
                                    if param9 > 100000000:
                                        if param10 > 1000000000:
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
    
    # Дублированный код
    for i in range(10):
        if i % 2 == 0:
            print(f"Even: {i}")
        else:
            print(f"Odd: {i}")
    
    # Еще один дублированный блок
    for i in range(10):
        if i % 2 == 0:
            print(f"Even: {i}")
        else:
            print(f"Odd: {i}")
    
    return result

def another_complex_function(x, y, z):
    """Еще одна сложная функция"""
    try:
        if x > 0 and y > 0 and z > 0:
            if x + y > z:
                if x + z > y:
                    if y + z > x:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    except Exception:
        return False

class ComplexClass:
    def __init__(self):
        self.value = 42
    
    def complex_method(self, data):
        """Сложный метод с множественными условиями"""
        result = []
        for item in data:
            if isinstance(item, str):
                if len(item) > 10:
                    if item.startswith('test'):
                        if item.endswith('ing'):
                            result.append(item.upper())
                        else:
                            result.append(item.lower())
                    else:
                        result.append(item)
                else:
                    result.append(item[:5])
            elif isinstance(item, int):
                if item > 100:
                    if item % 2 == 0:
                        result.append(item * 2)
                    else:
                        result.append(item // 2)
                else:
                    result.append(item)
            else:
                result.append(str(item))
        return result

# PEP8: W291 - trailing whitespace
def function_with_trailing_whitespace():    
    return "This line has trailing spaces"    

# PEP8: E111 - indentation not multiple of 4
def function_with_bad_indentation():
   return "This has bad indentation"

if __name__ == "__main__":
    # PEP8: E701 - multiple statements on one line
    x = 1; y = 2; z = 3
    
    # PEP8: E711 - comparison to None
    if x == None:
        print("x is None")
    
    # PEP8: E722 - bare except
    try:
        result = 1 / 0
    except:
        print("Error occurred")
    
    print("Test completed")
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return test_file


def analyze_sample_file():
    """Анализирует созданный тестовый файл"""
    print("🔍 АНАЛИЗ ТЕСТОВОГО ФАЙЛА С ПРОБЛЕМАМИ")
    print("="*60)
    
    # Создание тестового файла
    test_file = create_test_file_with_issues()
    print(f"✅ Создан тестовый файл: {test_file}")
    
    # Анализ качества
    analyzer = CodeQualityAnalyzer()
    report = analyzer.analyze_file(test_file)
    
    # Вывод результатов
    print_file_quality_report(report)
    
    # Удаление тестового файла
    test_file.unlink()
    print(f"\n🗑️ Тестовый файл удален")


def analyze_current_project():
    """Анализирует текущий проект"""
    print("\n🔍 АНАЛИЗ КАЧЕСТВА ТЕКУЩЕГО ПРОЕКТА")
    print("="*60)
    
    try:
        # Создание сервиса
        config = Configuration()
        service = ScanService(config)
        
        # Анализ качества проекта
        project_dir = Path(__file__).parent.parent
        report = service.analyze_project_quality(project_dir)
        
        # Вывод результатов
        print_project_quality_report(report)
        
    except Exception as e:
        print(f"❌ Ошибка анализа проекта: {e}")


def analyze_specific_files():
    """Анализирует конкретные файлы"""
    print("\n🔍 АНАЛИЗ КОНКРЕТНЫХ ФАЙЛОВ")
    print("="*60)
    
    analyzer = CodeQualityAnalyzer()
    
    # Список файлов для анализа
    files_to_analyze = [
        "src/core/scan_service.py",
        "src/core/complexity_analyzer.py",
        "src/core/code_quality_analyzer.py"
    ]
    
    for file_path in files_to_analyze:
        path = Path(file_path)
        if path.exists():
            print(f"\n📄 Анализ файла: {file_path}")
            try:
                report = analyzer.analyze_file(path)
                print(f"  Балл: {report.overall_score:.1f}/100")
                print(f"  Проблем: {report.issues_count}")
                print(f"  Функций: {len(report.functions_quality)}")
                print(f"  PEP8 нарушений: {len(report.pep8_violations)}")
                print(f"  Дублирований: {len(report.code_duplications)}")
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
        else:
            print(f"  ⚠️ Файл не найден: {file_path}")


def main():
    """Главная функция"""
    print("🧪 АНАЛИЗАТОР КАЧЕСТВА КОДА")
    print("="*60)
    print("Демонстрация возможностей анализа качества кода:")
    print("• PEP8 проверки")
    print("• Цикломатическая сложность")
    print("• Когнитивная сложность")
    print("• Дублирование кода")
    print("• Общие рекомендации")
    
    # Анализ тестового файла
    analyze_sample_file()
    
    # Анализ конкретных файлов
    analyze_specific_files()
    
    # Анализ текущего проекта
    analyze_current_project()
    
    print(f"\n{'='*60}")
    print("✅ Анализ качества кода завершен!")
    print("\n💡 Используйте эти результаты для улучшения качества кода")


if __name__ == "__main__":
    main()
