"""
Пример использования анализатора зависимостей
Демонстрирует анализ requirements.txt, поиск уязвимостей, анализ лицензий и оптимизацию
"""
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.dependency_analyzer import DependencyAnalyzer, DependencyReport
from core.scan_service import ScanService


def main():
    """Главная функция примера"""
    print("🔍 АНАЛИЗ ЗАВИСИМОСТЕЙ")
    print("=" * 50)
    
    # Создание анализатора
    analyzer = DependencyAnalyzer()
    
    # Путь к requirements.txt
    requirements_path = Path("requirements.txt")
    
    if not requirements_path.exists():
        print(f"❌ Файл {requirements_path} не найден")
        print("Создаем тестовый файл requirements.txt...")
        create_test_requirements(requirements_path)
    
    try:
        # Анализ зависимостей
        print(f"📦 Анализируем {requirements_path}...")
        report = analyzer.analyze_requirements(requirements_path)
        
        # Вывод результатов
        print_results(report)
        
        # Экспорт отчетов
        export_reports(analyzer, report)
        
        # Демонстрация через ScanService
        print("\n" + "=" * 50)
        print("🔧 ДЕМОНСТРАЦИЯ ЧЕРЕЗ SCANSERVICE")
        print("=" * 50)
        
        scan_service = ScanService()
        service_report = scan_service.analyze_dependencies(requirements_path)
        
        print(f"✅ Анализ через ScanService завершен:")
        print(f"   - Всего пакетов: {service_report.total_packages}")
        print(f"   - Уязвимых: {service_report.vulnerable_packages}")
        print(f"   - Устаревших: {service_report.outdated_count}")
        
        # Экспорт через ScanService
        output_path = Path("dependency_report_service.json")
        scan_service.export_dependency_report(service_report, output_path, 'json')
        print(f"📄 Отчет экспортирован: {output_path}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе зависимостей: {e}")
        import traceback
        traceback.print_exc()


def create_test_requirements(requirements_path: Path) -> None:
    """Создает тестовый файл requirements.txt"""
    test_requirements = """# Тестовые зависимости для демонстрации
requests>=2.25.0
numpy==1.21.0
pandas>=1.3.0
matplotlib>=3.4.0
PySide6>=6.0.0
# Дублирующаяся зависимость для демонстрации
requests>=2.28.0
"""
    
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write(test_requirements)
    
    print(f"✅ Создан тестовый файл {requirements_path}")


def print_results(report: DependencyReport) -> None:
    """Выводит результаты анализа"""
    print(f"\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("-" * 30)
    print(f"Всего пакетов: {report.total_packages}")
    print(f"Уязвимых пакетов: {report.vulnerable_packages}")
    print(f"Устаревших пакетов: {report.outdated_count}")
    print(f"Конфликтов лицензий: {report.license_conflicts}")
    print(f"Дублирующихся зависимостей: {report.duplicates_count}")
    
    # Детали по пакетам
    if report.packages:
        print(f"\n📦 ПАКЕТЫ:")
        print("-" * 20)
        for package in report.packages:
            status = []
            if package.is_outdated:
                status.append("🟡 Устарел")
            if any(v.package_name == package.name for v in report.vulnerabilities):
                status.append("🔴 Уязвим")
            
            status_str = " | ".join(status) if status else "✅ OK"
            print(f"  {package.name} {package.version} - {status_str}")
    
    # Уязвимости
    if report.vulnerabilities:
        print(f"\n🔴 УЯЗВИМОСТИ:")
        print("-" * 20)
        for vuln in report.vulnerabilities:
            print(f"  {vuln.package_name} ({vuln.severity}): {vuln.description}")
    
    # Дубликаты
    if report.duplicate_dependencies:
        print(f"\n🔄 ДУБЛИРУЮЩИЕСЯ ЗАВИСИМОСТИ:")
        print("-" * 30)
        for dup in report.duplicate_dependencies:
            print(f"  {dup.package_name}:")
            print(f"    Версии: {', '.join(dup.versions)}")
            print(f"    Файлы: {', '.join(dup.locations)}")
            print(f"    Рекомендация: {dup.recommendation}")
    
    # Рекомендации
    if report.recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print("-" * 20)
        for rec in report.recommendations:
            print(f"  {rec}")


def export_reports(analyzer: DependencyAnalyzer, report: DependencyReport) -> None:
    """Экспортирует отчеты в различных форматах"""
    print(f"\n📄 ЭКСПОРТ ОТЧЕТОВ")
    print("-" * 20)
    
    formats = ['json', 'csv', 'txt']
    
    for fmt in formats:
        output_path = Path(f"dependency_report.{fmt}")
        try:
            analyzer.export_report(report, output_path, fmt)
            print(f"  ✅ {fmt.upper()}: {output_path}")
        except Exception as e:
            print(f"  ❌ {fmt.upper()}: {e}")


if __name__ == "__main__":
    main()
