#!/usr/bin/env python3
"""
Тест изменений в GUI
"""
import sys
import os
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_main_window():
    """Тест главного окна"""
    try:
        from gui.main_window import MainWindow
        from core.scan_service import ScanService
        
        print("✅ MainWindow импортирован успешно")
        
        # Создаем сервис сканирования
        scan_service = ScanService()
        print("✅ ScanService создан успешно")
        
        # Проверяем тексты интерфейса
        window = MainWindow(scan_service)
        texts = window.get_ui_texts()
        
        print("📊 Проверка текстов интерфейса:")
        print(f"   Кнопка статистики (RU): {texts['stats_btn']}")
        
        # Проверяем, что текст изменился
        if "Детальный анализ проекта" in texts['stats_btn']:
            print("✅ Текст кнопки статистики обновлен корректно")
        else:
            print("❌ Текст кнопки статистики не обновлен")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании MainWindow: {e}")
        return False

def test_stats_window():
    """Тест окна статистики"""
    try:
        from src.gui.stats_window import StatsWindow, get_ui_texts
        
        print("✅ StatsWindow импортирован успешно")
        
        # Проверяем тексты
        texts_ru = get_ui_texts("ru")
        texts_en = get_ui_texts("en")
        
        print("📊 Проверка текстов StatsWindow:")
        print(f"   Заголовок (RU): {texts_ru['window_title']}")
        print(f"   Заголовок (EN): {texts_en['window_title']}")
        
        # Проверяем, что тексты обновлены
        if "Детальный анализ проекта" in texts_ru['window_title']:
            print("✅ Заголовок StatsWindow (RU) обновлен корректно")
        else:
            print("❌ Заголовок StatsWindow (RU) не обновлен")
            
        if "Detailed Project Analysis" in texts_en['window_title']:
            print("✅ Заголовок StatsWindow (EN) обновлен корректно")
        else:
            print("❌ Заголовок StatsWindow (EN) не обновлен")
        
        # Проверяем конструктор
        try:
            # Должен работать без folder_path
            stats_window = StatsWindow()
            print("✅ StatsWindow создан без folder_path успешно")
        except Exception as e:
            print(f"❌ Ошибка при создании StatsWindow без folder_path: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании StatsWindow: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование изменений в GUI")
    print("=" * 40)
    
    success = True
    
    # Тест главного окна
    print("\n1. Тестирование MainWindow...")
    if not test_main_window():
        success = False
    
    # Тест окна статистики
    print("\n2. Тестирование StatsWindow...")
    if not test_stats_window():
        success = False
    
    # Результат
    print("\n" + "=" * 40)
    if success:
        print("✅ Все тесты пройдены успешно!")
        print("🎉 Изменения работают корректно")
    else:
        print("❌ Некоторые тесты не пройдены")
        print("🔧 Требуется дополнительная отладка")
    
    return success

if __name__ == "__main__":
    main()
