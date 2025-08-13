"""
Интегрированные примеры использования - перенесены в core
"""
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .project_analyzer_core import IntegratedProjectAnalyzer
from .configuration import Configuration
from .logging_config import get_logger


class CoreExamples:
    """Интегрированные примеры использования"""
    
    def __init__(self):
        self.config = Configuration()
        self.logger = get_logger("CoreExamples")
        self.analyzer = IntegratedProjectAnalyzer(self.config)
    
    def run_dependency_analysis_example(self, project_path: Path) -> Dict[str, Any]:
        """Пример анализа зависимостей"""
        print("🔍 ЗАПУСК ПРИМЕРА: Анализ зависимостей")
        print("=" * 50)
        
        try:
            # Запускаем анализ
            result = self.analyzer.analyze_project(project_path, self._progress_callback)
            
            # Выводим результаты
            print("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА ЗАВИСИМОСТЕЙ:")
            print("-" * 40)
            
            stats = result['project_stats']
            print(f"📁 Всего файлов: {stats['total_files']}")
            print(f"📦 Всего импортов: {stats['total_imports']}")
            print(f"🔧 Уникальных библиотек: {stats['unique_libraries']}")
            print(f"⏱️ Время анализа: {stats['scan_duration']:.2f}с")
            
            # Топ библиотек
            print("\n🏆 ТОП-10 БИБЛИОТЕК:")
            print("-" * 30)
            for i, lib in enumerate(result['top_libraries'][:10], 1):
                print(f"{i:2d}. {lib['name']:20s} - {lib['count']:4d} ({lib['percentage']:5.1f}%)")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при анализе зависимостей: {e}")
            return {}
    
    def run_complexity_analysis_example(self, project_path: Path) -> Dict[str, Any]:
        """Пример анализа сложности"""
        print("📊 ЗАПУСК ПРИМЕРА: Анализ сложности кода")
        print("=" * 50)
        
        try:
            # Запускаем анализ
            result = self.analyzer.analyze_project(project_path, self._progress_callback)
            
            # Выводим результаты
            print("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА СЛОЖНОСТИ:")
            print("-" * 40)
            
            stats = result['project_stats']
            print(f"📁 Всего файлов: {stats['total_files']}")
            print(f"📊 Средняя сложность: {stats['average_complexity']:.2f}")
            print(f"⏱️ Время анализа: {stats['scan_duration']:.2f}с")
            
            # Распределение сложности
            complexity_dist = result['complexity_distribution']
            print("\n📈 РАСПРЕДЕЛЕНИЕ СЛОЖНОСТИ:")
            print("-" * 30)
            print(f"Очень низкая (0-5): {complexity_dist['very_low']}")
            print(f"Низкая (6-10): {complexity_dist['low']}")
            print(f"Средняя (11-20): {complexity_dist['medium']}")
            print(f"Высокая (21-30): {complexity_dist['high']}")
            print(f"Очень высокая (30+): {complexity_dist['very_high']}")
            
            # Самые сложные файлы
            files_analysis = result['files_analysis']
            sorted_files = sorted(files_analysis, key=lambda x: x['complexity'], reverse=True)
            
            print("\n🔥 САМЫЕ СЛОЖНЫЕ ФАЙЛЫ:")
            print("-" * 30)
            for i, file_analysis in enumerate(sorted_files[:5], 1):
                print(f"{i}. {file_analysis['path']} - {file_analysis['complexity']:.1f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при анализе сложности: {e}")
            return {}
    
    def run_quality_analysis_example(self, project_path: Path) -> Dict[str, Any]:
        """Пример анализа качества"""
        print("✨ ЗАПУСК ПРИМЕРА: Анализ качества кода")
        print("=" * 50)
        
        try:
            # Запускаем анализ
            result = self.analyzer.analyze_project(project_path, self._progress_callback)
            
            # Выводим результаты
            print("\n✨ РЕЗУЛЬТАТЫ АНАЛИЗА КАЧЕСТВА:")
            print("-" * 40)
            
            stats = result['project_stats']
            print(f"📁 Всего файлов: {stats['total_files']}")
            print(f"✨ Среднее качество: {stats['quality_score']:.2f}")
            print(f"⏱️ Время анализа: {stats['scan_duration']:.2f}с")
            
            # Распределение качества
            quality_dist = result['quality_distribution']
            print("\n📊 РАСПРЕДЕЛЕНИЕ КАЧЕСТВА:")
            print("-" * 30)
            print(f"Отличное (90-100): {quality_dist['excellent']}")
            print(f"Хорошее (70-89): {quality_dist['good']}")
            print(f"Удовлетворительное (50-69): {quality_dist['fair']}")
            print(f"Плохое (30-49): {quality_dist['poor']}")
            print(f"Очень плохое (0-29): {quality_dist['very_poor']}")
            
            # Файлы с проблемами
            files_analysis = result['files_analysis']
            problematic_files = [f for f in files_analysis if f['quality_score'] < 50]
            
            if problematic_files:
                print(f"\n⚠️ ФАЙЛЫ С ПРОБЛЕМАМИ (качество < 50):")
                print("-" * 40)
                for i, file_analysis in enumerate(problematic_files[:10], 1):
                    print(f"{i}. {file_analysis['path']} - {file_analysis['quality_score']:.1f}")
                    if file_analysis['issues']:
                        for issue in file_analysis['issues'][:3]:  # Показываем первые 3 проблемы
                            print(f"   - {issue}")
            else:
                print("\n✅ Проблемных файлов не найдено!")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при анализе качества: {e}")
            return {}
    
    def run_architecture_analysis_example(self, project_path: Path) -> Dict[str, Any]:
        """Пример анализа архитектуры"""
        print("🏗️ ЗАПУСК ПРИМЕРА: Анализ архитектуры проекта")
        print("=" * 50)
        
        try:
            # Запускаем анализ
            result = self.analyzer.analyze_project(project_path, self._progress_callback)
            
            # Выводим результаты
            print("\n🏗️ РЕЗУЛЬТАТЫ АНАЛИЗА АРХИТЕКТУРЫ:")
            print("-" * 40)
            
            stats = result['project_stats']
            print(f"📁 Всего файлов: {stats['total_files']}")
            print(f"📝 Всего строк: {stats['total_lines']}")
            print(f"⏱️ Время анализа: {stats['scan_duration']:.2f}с")
            
            # Данные архитектуры
            architecture_data = result.get('architecture_data', {})
            if architecture_data:
                print("\n🏗️ СТРУКТУРА ПРОЕКТА:")
                print("-" * 30)
                for key, value in architecture_data.items():
                    print(f"{key}: {value}")
            else:
                print("\n⚠️ Данные архитектуры недоступны")
            
            # Зависимости
            dependency_graph = result.get('dependency_graph', {})
            if dependency_graph:
                print("\n🔗 ЗАВИСИМОСТИ МОДУЛЕЙ:")
                print("-" * 30)
                for module, dependencies in list(dependency_graph.items())[:10]:  # Показываем первые 10
                    print(f"📦 {module}:")
                    for dep in dependencies[:5]:  # Показываем первые 5 зависимостей
                        print(f"  └── {dep}")
                    if len(dependencies) > 5:
                        print(f"  └── ... и еще {len(dependencies) - 5}")
            else:
                print("\n⚠️ Данные зависимостей недоступны")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при анализе архитектуры: {e}")
            return {}
    
    def run_comprehensive_analysis_example(self, project_path: Path) -> Dict[str, Any]:
        """Пример комплексного анализа"""
        print("🚀 ЗАПУСК ПРИМЕРА: Комплексный анализ проекта")
        print("=" * 50)
        
        try:
            # Запускаем анализ
            result = self.analyzer.analyze_project(project_path, self._progress_callback)
            
            # Выводим результаты
            print("\n📊 КОМПЛЕКСНЫЙ ОТЧЕТ:")
            print("=" * 50)
            
            stats = result['project_stats']
            print(f"📁 Всего файлов: {stats['total_files']}")
            print(f"📝 Всего строк: {stats['total_lines']}")
            print(f"📦 Всего импортов: {stats['total_imports']}")
            print(f"🔧 Уникальных библиотек: {stats['unique_libraries']}")
            print(f"📊 Средняя сложность: {stats['average_complexity']:.2f}")
            print(f"✨ Среднее качество: {stats['quality_score']:.2f}")
            print(f"⏱️ Время анализа: {stats['scan_duration']:.2f}с")
            
            # Топ библиотек
            print("\n🏆 ТОП-10 БИБЛИОТЕК:")
            print("-" * 30)
            for i, lib in enumerate(result['top_libraries'][:10], 1):
                print(f"{i:2d}. {lib['name']:20s} - {lib['count']:4d} ({lib['percentage']:5.1f}%)")
            
            # Распределение качества
            quality_dist = result['quality_distribution']
            print("\n✨ РАСПРЕДЕЛЕНИЕ КАЧЕСТВА:")
            print("-" * 30)
            print(f"Отличное (90-100): {quality_dist['excellent']}")
            print(f"Хорошее (70-89): {quality_dist['good']}")
            print(f"Удовлетворительное (50-69): {quality_dist['fair']}")
            print(f"Плохое (30-49): {quality_dist['poor']}")
            print(f"Очень плохое (0-29): {quality_dist['very_poor']}")
            
            # Распределение сложности
            complexity_dist = result['complexity_distribution']
            print("\n📊 РАСПРЕДЕЛЕНИЕ СЛОЖНОСТИ:")
            print("-" * 30)
            print(f"Очень низкая (0-5): {complexity_dist['very_low']}")
            print(f"Низкая (6-10): {complexity_dist['low']}")
            print(f"Средняя (11-20): {complexity_dist['medium']}")
            print(f"Высокая (21-30): {complexity_dist['high']}")
            print(f"Очень высокая (30+): {complexity_dist['very_high']}")
            
            # Рекомендации
            print("\n💡 РЕКОМЕНДАЦИИ:")
            print("-" * 30)
            
            if quality_dist['poor'] + quality_dist['very_poor'] > 0:
                print("⚠️ Обнаружены файлы с низким качеством кода")
                print("   Рекомендуется провести рефакторинг")
            
            if complexity_dist['high'] + complexity_dist['very_high'] > 0:
                print("⚠️ Обнаружены файлы с высокой сложностью")
                print("   Рекомендуется упростить логику")
            
            if stats['unique_libraries'] > 50:
                print("⚠️ Большое количество зависимостей")
                print("   Рекомендуется провести аудит зависимостей")
            
            if stats['average_complexity'] > 15:
                print("⚠️ Высокая средняя сложность проекта")
                print("   Рекомендуется упростить архитектуру")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при комплексном анализе: {e}")
            return {}
    
    def _progress_callback(self, message: str):
        """Обратный вызов для прогресса"""
        print(f"📝 {message}")
    
    def export_example_report(self, result: Dict[str, Any], output_path: Path, format: str = 'json'):
        """Экспорт отчета примера"""
        try:
            self.analyzer.analysis_result = result
            self.analyzer.export_report(output_path, format)
            print(f"✅ Отчет сохранен в {output_path}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении отчета: {e}")


def main():
    """Главная функция для запуска примеров"""
    if len(sys.argv) < 3:
        print("Использование: python examples_core.py <тип_анализа> <путь_к_проекту>")
        print("\nДоступные типы анализа:")
        print("  dependency  - Анализ зависимостей")
        print("  complexity  - Анализ сложности")
        print("  quality     - Анализ качества")
        print("  architecture - Анализ архитектуры")
        print("  comprehensive - Комплексный анализ")
        return
    
    analysis_type = sys.argv[1]
    project_path = Path(sys.argv[2])
    
    if not project_path.exists():
        print(f"❌ Путь не существует: {project_path}")
        return
    
    examples = CoreExamples()
    
    # Выполняем анализ в зависимости от типа
    if analysis_type == "dependency":
        result = examples.run_dependency_analysis_example(project_path)
    elif analysis_type == "complexity":
        result = examples.run_complexity_analysis_example(project_path)
    elif analysis_type == "quality":
        result = examples.run_quality_analysis_example(project_path)
    elif analysis_type == "architecture":
        result = examples.run_architecture_analysis_example(project_path)
    elif analysis_type == "comprehensive":
        result = examples.run_comprehensive_analysis_example(project_path)
    else:
        print(f"❌ Неизвестный тип анализа: {analysis_type}")
        return
    
    # Экспортируем отчет
    if result:
        output_path = Path(f"analysis_report_{analysis_type}_{int(time.time())}.json")
        examples.export_example_report(result, output_path, 'json')


if __name__ == "__main__":
    main()
