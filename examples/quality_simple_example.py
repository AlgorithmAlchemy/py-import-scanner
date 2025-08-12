#!/usr/bin/env python3
"""
Упрощенный пример анализа качества кода
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.code_quality_analyzer import CodeQualityAnalyzer


def print_file_quality_report(report):
    """Выводит отчет о качестве файла"""
    print(f"\n{'='*60}")
    print(f"ОТЧЕТ О КАЧЕСТВЕ: {report.file_path.name}")
    print(f"{'='*60}")
    print(f"Общий балл: {report.overall_score:.1f}/100")
    print(f"Проблем: {report.issues_count}")
    
    # PEP8 нарушения
    if report.pep8_violations:
        print(f"\n🔴 PEP8 НАРУШЕНИЯ ({len(report.pep8_violations)}):")
        for violation in report.pep8_violations[:3]:
            print(f"  Строка {violation.line_number}: {violation.message}")
    
    # Качество функций
    if report.functions_quality:
        print(f"\n📊 ФУНКЦИИ ({len(report.functions_quality)}):")
        for func in report.functions_quality:
            print(f"  {func.name}: CC={func.cyclomatic_complexity}, "
                  f"CogC={func.cognitive_complexity}, "
                  f"LOC={func.lines_of_code}")
            if func.issues:
                print(f"    ⚠️ {', '.join(func.issues)}")
    
    # Дублирование кода
    if report.code_duplications:
        print(f"\n🔄 ДУБЛИРОВАНИЯ:")
        for dup in report.code_duplications[:2]:
            print(f"  {dup.occurrences} вхождений (строки: {dup.lines})")
    
    # Рекомендации
    if report.recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for rec in report.recommendations:
            print(f"  • {rec}")


def create_test_file_with_issues():
    """Создает тестовый файл с проблемами"""
    test_file = Path("test_quality.py")
    
    content = '''#!/usr/bin/env python3
"""
Тестовый файл с проблемами качества
"""

import os,sys  # PEP8: E401
from pathlib import Path

def bad_function(param1,param2,param3,param4,param5,param6):
    """Функция с множеством параметров и высокой сложностью"""
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

def another_bad_function(x,y,z):
    """Еще одна плохая функция"""
    try:
        if x>0 and y>0 and z>0:
            if x+y>z:
                if x+z>y:
                    if y+z>x:
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

# PEP8: W291 - trailing whitespace
def function_with_whitespace():    
    return "trailing spaces"    

# PEP8: E111 - bad indentation
def function_with_bad_indent():
   return "bad indentation"

if __name__ == "__main__":
    # PEP8: E701 - multiple statements
    x=1; y=2; z=3
    
    # PEP8: E711 - comparison to None
    if x==None:
        print("x is None")
    
    # PEP8: E722 - bare except
    try:
        result = 1/0
    except:
        print("Error")
    
    print("Done")
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return test_file


def analyze_test_file():
    """Анализирует тестовый файл"""
    print("🔍 АНАЛИЗ ТЕСТОВОГО ФАЙЛА")
    print("="*50)
    
    # Создание тестового файла
    test_file = create_test_file_with_issues()
    print(f"✅ Создан файл: {test_file}")
    
    # Анализ качества
    analyzer = CodeQualityAnalyzer()
    report = analyzer.analyze_file(test_file)
    
    # Вывод результатов
    print_file_quality_report(report)
    
    # Удаление файла
    test_file.unlink()
    print(f"\n🗑️ Файл удален")


def analyze_specific_files():
    """Анализирует конкретные файлы"""
    print("\n🔍 АНАЛИЗ КОНКРЕТНЫХ ФАЙЛОВ")
    print("="*50)
    
    analyzer = CodeQualityAnalyzer()
    
    files_to_analyze = [
        "src/core/code_quality_analyzer.py",
        "src/core/complexity_analyzer.py"
    ]
    
    for file_path in files_to_analyze:
        path = Path(file_path)
        if path.exists():
            print(f"\n📄 {file_path}:")
            try:
                report = analyzer.analyze_file(path)
                print(f"  Балл: {report.overall_score:.1f}/100")
                print(f"  Проблем: {report.issues_count}")
                print(f"  Функций: {len(report.functions_quality)}")
                print(f"  PEP8: {len(report.pep8_violations)}")
                print(f"  Дублирований: {len(report.code_duplications)}")
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
        else:
            print(f"  ⚠️ Не найден: {file_path}")


def analyze_small_project():
    """Анализирует небольшой проект"""
    print("\n🔍 АНАЛИЗ НЕБОЛЬШОГО ПРОЕКТА")
    print("="*50)
    
    analyzer = CodeQualityAnalyzer()
    
    # Создаем временный проект
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Создаем несколько файлов
        files_content = [
            ("good.py", "def good(): return True"),
            ("bad.py", "def bad(x,y,z):\n    if x>0:\n        if y>0:\n            if z>0:\n                return True\n    return False"),
            ("ugly.py", "def ugly(param1,param2,param3,param4,param5,param6,param7,param8):\n    x=1+2\n    if param1>0:\n        if param2>10:\n            if param3>100:\n                return 1\n    return 0")
        ]
        
        for name, content in files_content:
            file_path = temp_path / name
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Анализ проекта
        report = analyzer.analyze_project(temp_path)
        
        print(f"Всего файлов: {report.total_files}")
        print(f"Общих проблем: {report.total_issues}")
        print(f"Средний балл: {report.average_score:.1f}/100")
        
        if report.worst_files:
            print(f"Худшие файлы: {', '.join(report.worst_files)}")
        
        if report.best_files:
            print(f"Лучшие файлы: {', '.join(report.best_files)}")
        
        if report.recommendations:
            print(f"Рекомендации: {', '.join(report.recommendations)}")
    
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Главная функция"""
    print("🧪 АНАЛИЗАТОР КАЧЕСТВА КОДА")
    print("="*50)
    print("Демонстрация возможностей:")
    print("• PEP8 проверки")
    print("• Цикломатическая сложность")
    print("• Когнитивная сложность")
    print("• Дублирование кода")
    print("• Рекомендации")
    
    # Анализ тестового файла
    analyze_test_file()
    
    # Анализ конкретных файлов
    analyze_specific_files()
    
    # Анализ небольшого проекта
    analyze_small_project()
    
    print(f"\n{'='*50}")
    print("✅ Анализ завершен!")


if __name__ == "__main__":
    main()
