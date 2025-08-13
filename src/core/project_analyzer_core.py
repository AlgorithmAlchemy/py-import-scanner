"""
Интегрированный анализатор проектов - объединяет все функции анализа
"""
import os
import ast
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict

from .logging_config import get_logger
from .import_parser import ImportParser
from .dependency_analyzer import DependencyAnalyzer
from .complexity_analyzer import ComplexityAnalyzer
from .code_quality_analyzer import CodeQualityAnalyzer
from .architecture_analyzer import ArchitectureAnalyzer


@dataclass
class ProjectStats:
    """Статистика проекта"""
    total_files: int = 0
    total_lines: int = 0
    total_imports: int = 0
    unique_libraries: int = 0
    average_complexity: float = 0.0
    quality_score: float = 0.0
    architecture_score: float = 0.0
    scan_duration: float = 0.0


@dataclass
class LibraryInfo:
    """Информация о библиотеке"""
    name: str
    count: int
    percentage: float
    files: List[str]
    first_occurrence: str


@dataclass
class FileAnalysis:
    """Анализ файла"""
    path: str
    lines: int
    imports: List[str]
    complexity: float
    quality_score: float
    issues: List[str]


class IntegratedProjectAnalyzer:
    """Интегрированный анализатор проектов"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger("IntegratedProjectAnalyzer")
        
        # Инициализация компонентов
        self.import_parser = ImportParser(config)
        self.dependency_analyzer = DependencyAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.quality_analyzer = CodeQualityAnalyzer()
        self.architecture_analyzer = ArchitectureAnalyzer()
        
        # Результаты анализа
        self.project_stats = ProjectStats()
        self.libraries_info: Dict[str, LibraryInfo] = {}
        self.files_analysis: List[FileAnalysis] = []
        self.dependency_graph: Dict[str, List[str]] = {}
        self.architecture_data: Dict[str, Any] = {}
        
    def analyze_project(self, project_path: Path, progress_callback=None) -> Dict[str, Any]:
        """
        Полный анализ проекта
        
        Args:
            project_path: Путь к проекту
            progress_callback: Функция обратного вызова для прогресса
            
        Returns:
            Словарь с результатами анализа
        """
        start_time = time.time()
        self.logger.info(f"Начало полного анализа проекта: {project_path}")
        
        if progress_callback:
            progress_callback("🔍 Начинаю анализ проекта...")
        
        try:
            # 1. Поиск Python файлов
            python_files = self._find_python_files(project_path)
            self.project_stats.total_files = len(python_files)
            
            if progress_callback:
                progress_callback(f"📁 Найдено {len(python_files)} Python файлов")
            
            # 2. Анализ импортов
            if progress_callback:
                progress_callback("📦 Анализ импортов...")
            
            imports_data = self._analyze_imports(python_files, progress_callback)
            
            # 3. Анализ сложности
            if progress_callback:
                progress_callback("📊 Анализ сложности кода...")
            
            complexity_data = self._analyze_complexity(python_files, progress_callback)
            
            # 4. Анализ качества
            if progress_callback:
                progress_callback("✨ Анализ качества кода...")
            
            quality_data = self._analyze_quality(python_files, progress_callback)
            
            # 5. Анализ архитектуры
            if progress_callback:
                progress_callback("🏗️ Анализ архитектуры...")
            
            architecture_data = self._analyze_architecture(project_path, progress_callback)
            
            # 6. Анализ зависимостей
            if progress_callback:
                progress_callback("🔗 Анализ зависимостей...")
            
            dependency_data = self._analyze_dependencies(project_path, progress_callback)
            
            # 7. Сборка итоговой статистики
            if progress_callback:
                progress_callback("📈 Сборка статистики...")
            
            self._build_final_stats(imports_data, complexity_data, quality_data)
            
            # 8. Расчет времени
            self.project_stats.scan_duration = time.time() - start_time
            
            if progress_callback:
                progress_callback("✅ Анализ завершен!")
            
            # Возвращаем полный отчет
            return self._generate_comprehensive_report()
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе проекта: {e}")
            if progress_callback:
                progress_callback(f"❌ Ошибка: {e}")
            raise
    
    def _find_python_files(self, project_path: Path) -> List[Path]:
        """Поиск всех Python файлов в проекте"""
        python_files = []
        excluded_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'node_modules'}
        
        for root, dirs, files in os.walk(project_path):
            # Исключаем ненужные директории
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _analyze_imports(self, python_files: List[Path], progress_callback=None) -> Dict[str, Any]:
        """Анализ импортов во всех файлах"""
        all_imports = []
        file_imports = {}
        
        for i, file_path in enumerate(python_files):
            if progress_callback and i % 10 == 0:
                progress_callback(f"📦 Анализ импортов: {i+1}/{len(python_files)}")
            
            try:
                imports = self.import_parser.parse_imports(
                    file_path.read_text(encoding='utf-8', errors='ignore'),
                    file_path
                )
                all_imports.extend(imports)
                file_imports[str(file_path)] = imports
            except Exception as e:
                self.logger.warning(f"Ошибка при анализе импортов в {file_path}: {e}")
        
        # Подсчет статистики
        import_counter = Counter(all_imports)
        total_imports = len(all_imports)
        unique_libraries = len(import_counter)
        
        # Создание информации о библиотеках
        for lib_name, count in import_counter.most_common():
            percentage = (count / total_imports * 100) if total_imports > 0 else 0
            files_using_lib = [f for f, imports in file_imports.items() if lib_name in imports]
            
            self.libraries_info[lib_name] = LibraryInfo(
                name=lib_name,
                count=count,
                percentage=percentage,
                files=files_using_lib,
                first_occurrence=files_using_lib[0] if files_using_lib else ""
            )
        
        return {
            'total_imports': total_imports,
            'unique_libraries': unique_libraries,
            'libraries_info': self.libraries_info,
            'file_imports': file_imports
        }
    
    def _analyze_complexity(self, python_files: List[Path], progress_callback=None) -> Dict[str, Any]:
        """Анализ сложности кода"""
        complexity_scores = []
        
        for i, file_path in enumerate(python_files):
            if progress_callback and i % 10 == 0:
                progress_callback(f"📊 Анализ сложности: {i+1}/{len(python_files)}")
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Используем правильный метод analyze_file
                complexity_report = self.complexity_analyzer.analyze_file(file_path)
                complexity = complexity_report.metrics.cyclomatic_complexity
                complexity_scores.append(complexity)
                
                # Обновляем анализ файла
                file_analysis = FileAnalysis(
                    path=str(file_path),
                    lines=len(content.splitlines()),
                    imports=[],  # Будет заполнено позже
                    complexity=complexity,
                    quality_score=0.0,  # Будет заполнено позже
                    issues=[]
                )
                self.files_analysis.append(file_analysis)
                
            except Exception as e:
                self.logger.warning(f"Ошибка при анализе сложности в {file_path}: {e}")
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        return {
            'average_complexity': avg_complexity,
            'complexity_scores': complexity_scores,
            'max_complexity': max(complexity_scores) if complexity_scores else 0,
            'min_complexity': min(complexity_scores) if complexity_scores else 0
        }
    
    def _analyze_quality(self, python_files: List[Path], progress_callback=None) -> Dict[str, Any]:
        """Анализ качества кода"""
        quality_scores = []
        
        for i, file_path in enumerate(python_files):
            if progress_callback and i % 10 == 0:
                progress_callback(f"✨ Анализ качества: {i+1}/{len(python_files)}")
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Используем правильный метод analyze_file
                quality_report = self.quality_analyzer.analyze_file(file_path)
                quality_score = quality_report.overall_score
                quality_scores.append(quality_score)
                
                # Обновляем анализ файла
                for file_analysis in self.files_analysis:
                    if file_analysis.path == str(file_path):
                        file_analysis.quality_score = quality_score
                        file_analysis.issues = quality_report.issues if hasattr(quality_report, 'issues') else []
                        break
                
            except Exception as e:
                self.logger.warning(f"Ошибка при анализе качества в {file_path}: {e}")
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'average_quality': avg_quality,
            'quality_scores': quality_scores,
            'quality_distribution': self._calculate_quality_distribution(quality_scores)
        }
    
    def _analyze_architecture(self, project_path: Path, progress_callback=None) -> Dict[str, Any]:
        """Анализ архитектуры проекта"""
        if progress_callback:
            progress_callback("🏗️ Анализ архитектуры проекта...")
        
        try:
            architecture_result = self.architecture_analyzer.analyze_project(project_path)
            # Преобразуем результат в словарь
            self.architecture_data = {
                'modules': len(architecture_result.modules) if hasattr(architecture_result, 'modules') else 0,
                'dependencies': len(architecture_result.dependencies) if hasattr(architecture_result, 'dependencies') else 0,
                'patterns': architecture_result.patterns if hasattr(architecture_result, 'patterns') else [],
                'recommendations': architecture_result.recommendations if hasattr(architecture_result, 'recommendations') else []
            }
            return self.architecture_data
        except Exception as e:
            self.logger.error(f"Ошибка при анализе архитектуры: {e}")
            return {}
    
    def _analyze_dependencies(self, project_path: Path, progress_callback=None) -> Dict[str, Any]:
        """Анализ зависимостей проекта"""
        if progress_callback:
            progress_callback("🔗 Анализ зависимостей...")
        
        try:
            # Создаем простой граф зависимостей на основе импортов
            dependency_graph = {}
            
            # Анализируем импорты в каждом файле
            for file_analysis in self.files_analysis:
                file_path = Path(file_analysis.path)
                module_name = file_path.stem
                
                # Получаем импорты для этого файла
                try:
                    imports = self.import_parser.parse_imports(
                        file_path.read_text(encoding='utf-8', errors='ignore'),
                        file_path
                    )
                    dependency_graph[module_name] = list(set(imports))
                except Exception as e:
                    self.logger.warning(f"Ошибка при анализе зависимостей в {file_path}: {e}")
                    dependency_graph[module_name] = []
            
            self.dependency_graph = dependency_graph
            
            return {
                'dependency_graph': dependency_graph,
                'total_modules': len(dependency_graph),
                'total_dependencies': sum(len(deps) for deps in dependency_graph.values())
            }
        except Exception as e:
            self.logger.error(f"Ошибка при анализе зависимостей: {e}")
            return {}
    
    def _build_final_stats(self, imports_data, complexity_data, quality_data):
        """Сборка итоговой статистики"""
        self.project_stats.total_imports = imports_data['total_imports']
        self.project_stats.unique_libraries = imports_data['unique_libraries']
        self.project_stats.average_complexity = complexity_data['average_complexity']
        self.project_stats.quality_score = quality_data['average_quality']
        
        # Подсчет общего количества строк
        total_lines = sum(file_analysis.lines for file_analysis in self.files_analysis)
        self.project_stats.total_lines = total_lines
    
    def _calculate_quality_distribution(self, quality_scores: List[float]) -> Dict[str, int]:
        """Расчет распределения качества"""
        distribution = {
            'excellent': 0,  # 90-100
            'good': 0,       # 70-89
            'fair': 0,       # 50-69
            'poor': 0,       # 30-49
            'very_poor': 0   # 0-29
        }
        
        for score in quality_scores:
            if score >= 90:
                distribution['excellent'] += 1
            elif score >= 70:
                distribution['good'] += 1
            elif score >= 50:
                distribution['fair'] += 1
            elif score >= 30:
                distribution['poor'] += 1
            else:
                distribution['very_poor'] += 1
        
        return distribution
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Генерация комплексного отчета"""
        return {
            'project_stats': asdict(self.project_stats),
            'libraries_info': {name: asdict(info) for name, info in self.libraries_info.items()},
            'files_analysis': [asdict(analysis) for analysis in self.files_analysis],
            'dependency_graph': self.dependency_graph,
            'architecture_data': self.architecture_data,
            'top_libraries': self._get_top_libraries(10),
            'quality_distribution': self._calculate_quality_distribution(
                [f.quality_score for f in self.files_analysis]
            ),
            'complexity_distribution': self._calculate_complexity_distribution(),
            'scan_timestamp': time.time()
        }
    
    def _get_top_libraries(self, count: int = 10) -> List[Dict[str, Any]]:
        """Получение топ библиотек"""
        sorted_libraries = sorted(
            self.libraries_info.values(),
            key=lambda x: x.count,
            reverse=True
        )
        
        return [asdict(lib) for lib in sorted_libraries[:count]]
    
    def _calculate_complexity_distribution(self) -> Dict[str, int]:
        """Расчет распределения сложности"""
        distribution = {
            'very_low': 0,   # 0-5
            'low': 0,        # 6-10
            'medium': 0,     # 11-20
            'high': 0,       # 21-30
            'very_high': 0   # 30+
        }
        
        for file_analysis in self.files_analysis:
            complexity = file_analysis.complexity
            if complexity <= 5:
                distribution['very_low'] += 1
            elif complexity <= 10:
                distribution['low'] += 1
            elif complexity <= 20:
                distribution['medium'] += 1
            elif complexity <= 30:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1
        
        return distribution
    
    def export_report(self, output_path: Path, format: str = 'json') -> None:
        """Экспорт отчета в файл"""
        report = self._generate_comprehensive_report()
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'txt':
            self._export_text_report(output_path, report)
        
        self.logger.info(f"Отчет экспортирован в {output_path}")
    
    def _export_text_report(self, output_path: Path, report: Dict[str, Any]) -> None:
        """Экспорт отчета в текстовом формате"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ОТЧЕТ ОБ АНАЛИЗЕ ПРОЕКТА\n")
            f.write("=" * 60 + "\n\n")
            
            # Общая статистика
            stats = report['project_stats']
            f.write("📊 ОБЩАЯ СТАТИСТИКА:\n")
            f.write(f"   Всего файлов: {stats['total_files']}\n")
            f.write(f"   Всего строк: {stats['total_lines']}\n")
            f.write(f"   Всего импортов: {stats['total_imports']}\n")
            f.write(f"   Уникальных библиотек: {stats['unique_libraries']}\n")
            f.write(f"   Средняя сложность: {stats['average_complexity']:.2f}\n")
            f.write(f"   Среднее качество: {stats['quality_score']:.2f}\n")
            f.write(f"   Время анализа: {stats['scan_duration']:.2f}с\n\n")
            
            # Топ библиотек
            f.write("🏆 ТОП-10 БИБЛИОТЕК:\n")
            for i, lib in enumerate(report['top_libraries'], 1):
                f.write(f"   {i:2d}. {lib['name']:20s} - {lib['count']:4d} ({lib['percentage']:5.1f}%)\n")
            f.write("\n")
            
            # Распределение качества
            f.write("✨ РАСПРЕДЕЛЕНИЕ КАЧЕСТВА:\n")
            quality_dist = report['quality_distribution']
            f.write(f"   Отличное (90-100): {quality_dist['excellent']}\n")
            f.write(f"   Хорошее (70-89): {quality_dist['good']}\n")
            f.write(f"   Удовлетворительное (50-69): {quality_dist['fair']}\n")
            f.write(f"   Плохое (30-49): {quality_dist['poor']}\n")
            f.write(f"   Очень плохое (0-29): {quality_dist['very_poor']}\n\n")
            
            # Распределение сложности
            f.write("📊 РАСПРЕДЕЛЕНИЕ СЛОЖНОСТИ:\n")
            complexity_dist = report['complexity_distribution']
            f.write(f"   Очень низкая (0-5): {complexity_dist['very_low']}\n")
            f.write(f"   Низкая (6-10): {complexity_dist['low']}\n")
            f.write(f"   Средняя (11-20): {complexity_dist['medium']}\n")
            f.write(f"   Высокая (21-30): {complexity_dist['high']}\n")
            f.write(f"   Очень высокая (30+): {complexity_dist['very_high']}\n\n")
