"""
Обновленный главный файл с модульной архитектурой
"""
import sys
import os
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale

from core.scan_service import ScanService
from gui.main_window import MainWindow


def main():
    """Главная функция приложения"""
    print("🚀 Запуск Python Import Parser (рефакторинг v1.0)")
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("Python Import Parser")
    app.setApplicationVersion("2.4.0")
    app.setOrganizationName("AlgorithmAlchemy")
    
    # Настройка переводчика
    translator = QTranslator()
    locale = QLocale.system().name()
    
    # Попытка загрузить перевод
    if translator.load(f"translations/import_parser_{locale}", "."):
        app.installTranslator(translator)
        print(f"✅ Загружен перевод для локали: {locale}")
    else:
        print(f"⚠️ Перевод для локали {locale} не найден, используется английский")
    
    # Создание сервиса сканирования
    scan_service = ScanService()
    
    # Создание и отображение главного окна
    window = MainWindow(scan_service)
    window.show()
    
    print("✅ Приложение запущено успешно")
    
    # Запуск главного цикла
    return app.exec()


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
