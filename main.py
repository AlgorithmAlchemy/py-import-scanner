"""
Обновленный главный файл с модульной архитектурой
"""
import sys
import os
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    """Главная функция приложения"""
    print("🚀 Python Import Parser (рефакторинг v2.4.0)")
    print("=" * 50)
    
    try:
        # Проверяем доступность основных модулей#
        print("📦 Проверка доступности модулей...")
        
        # Пробуем импортировать основные компоненты
        try:
            from core.architecture_analyzer import ArchitectureAnalyzer
            print("✅ ArchitectureAnalyzer - доступен")
        except ImportError as e:
            print(f"⚠️ ArchitectureAnalyzer - недоступен: {e}")
        
        try:
            from core.dependency_analyzer import DependencyAnalyzer
            print("✅ DependencyAnalyzer - доступен")
        except ImportError as e:
            print(f"⚠️ DependencyAnalyzer - недоступен: {e}")
        
        try:
            from core.complexity_analyzer import ComplexityAnalyzer
            print("✅ ComplexityAnalyzer - доступен")
        except ImportError as e:
            print(f"⚠️ ComplexityAnalyzer - недоступен: {e}")
        
        try:
            from core.code_quality_analyzer import CodeQualityAnalyzer
            print("✅ CodeQualityAnalyzer - доступен")
        except ImportError as e:
            print(f"⚠️ CodeQualityAnalyzer - недоступен: {e}")
        
        # Проверяем GUI компоненты
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QTranslator, QLocale
            print("✅ PySide6 GUI - доступен")
            
            # Пробуем запустить GUI
            try:
                from core.scan_service import ScanService
                from core.logging_config import get_logger
                from gui.main_window import MainWindow
                
                print("🎨 Запуск GUI приложения...")
                
                # Создание приложения
                app = QApplication(sys.argv)
                app.setApplicationName("Python Import Parser")
                app.setApplicationVersion("2.4.0")
                app.setOrganizationName("AlgorithmAlchemy")
                
                # Создание сервиса сканирования
                scan_service = ScanService()
                
                # Создание и отображение главного окна
                window = MainWindow(scan_service)
                window.show()
                
                print("✅ GUI приложение запущено успешно")
                
                # Запуск главного цикла
                return app.exec()
                
            except ImportError as e:
                print(f"⚠️ ScanService или GUI компоненты недоступны: {e}")
                print("💡 Для полной функциональности установите psutil: pip install psutil")
                
        except ImportError as e:
            print(f"⚠️ PySide6 недоступен: {e}")
            print("💡 Для GUI установите PySide6: pip install PySide6")
        
        # Демонстрация доступных функций
        print("\n🔧 ДОСТУПНЫЕ ФУНКЦИИ:")
        print("-" * 30)
        
        # Интегрированный анализатор
        try:
            from src.core.project_analyzer_core import IntegratedProjectAnalyzer
            from src.core.examples_core import CoreExamples
            print("🚀 Интегрированный анализатор - доступен")
            print("   Команда: python -m src.core.examples_core <тип> <путь>")
            print("   Типы: dependency, complexity, quality, architecture, comprehensive")
        except ImportError as e:
            print(f"🚀 Интегрированный анализатор - недоступен: {e}")
        
        # Анализ архитектуры
        try:
            analyzer = ArchitectureAnalyzer()
            print("🏗️ Анализ архитектуры - доступен")
        except:
            print("🏗️ Анализ архитектуры - недоступен")
        
        # Анализ зависимостей
        try:
            analyzer = DependencyAnalyzer()
            print("📦 Анализ зависимостей - доступен")
        except:
            print("📦 Анализ зависимостей - недоступен")
        
        # Анализ сложности
        try:
            analyzer = ComplexityAnalyzer()
            print("📊 Анализ сложности - доступен")
        except:
            print("📊 Анализ сложности - недоступен")
        
        # Анализ качества
        try:
            analyzer = CodeQualityAnalyzer()
            print("✨ Анализ качества - доступен")
        except:
            print("✨ Анализ качества - недоступен")
        
        print("\n📚 ДОКУМЕНТАЦИЯ:")
        print("-" * 20)
        print("📄 DEPENDENCY_ANALYSIS_REPORT.md - Анализ зависимостей")
        print("🏗️ ARCHITECTURE_ANALYSIS_REPORT.md - Анализ архитектуры")
        print("📊 QUALITY_ANALYSIS_REPORT.md - Анализ качества")
        print("🎯 FINAL_COMPLETION_REPORT.md - Итоговый отчет")
        
        print("\n✅ Система готова к использованию!")
        return 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Приложение прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
