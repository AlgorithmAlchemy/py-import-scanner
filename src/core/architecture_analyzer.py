"""
Модуль анализа архитектуры
Включает визуализацию графа зависимостей между модулями
"""
import ast
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import json
import logging

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ModuleInfo:
    """Информация о модуле"""
    name: str
    path: Path
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)


@dataclass
class DependencyEdge:
    """Связь между модулями"""
    source: str
    target: str
    type: str  # 'import', 'from_import', 'class_inheritance'
    line_number: int
    details: str = ""


@dataclass
class ArchitectureReport:
    """Отчет об архитектуре"""
    modules: List[ModuleInfo] = field(default_factory=list)
    dependencies: List[DependencyEdge] = field(default_factory=list)
    graph: Optional[nx.DiGraph] = None
    total_modules: int = 0
    total_dependencies: int = 0
    circular_dependencies: List[List[str]] = field(default_factory=list)
    isolated_modules: List[str] = field(default_factory=list)
    highly_coupled_modules: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ArchitectureAnalyzer:
    """Анализатор архитектуры"""

    def __init__(self) -> None:
        self.logger = get_logger("ArchitectureAnalyzer")
        self.graph = nx.DiGraph()
        self.modules_info: Dict[str, ModuleInfo] = {}

    def analyze_project(self, project_path: Path) -> ArchitectureReport:
        """
        Анализирует архитектуру проекта
        
        Args:
            project_path: Путь к корню проекта
            
        Returns:
            Отчет об архитектуре
        """
        self.logger.info(f"Анализ архитектуры проекта: {project_path}")
        
        if not project_path.exists():
            raise FileNotFoundError(f"Проект не найден: {project_path}")
        
        report = ArchitectureReport()
        
        try:
            # Поиск всех Python файлов
            python_files = self._find_python_files(project_path)
            self.logger.info(f"Найдено {len(python_files)} Python файлов")
            
            # Анализ каждого файла
            for file_path in python_files:
                module_info = self._analyze_file(file_path, project_path)
                if module_info:
                    self.modules_info[module_info.name] = module_info
                    report.modules.append(module_info)
            
            # Построение графа зависимостей
            self._build_dependency_graph(report)
            
            # Анализ архитектуры
            self._analyze_architecture_patterns(report)
            
            # Генерация рекомендаций
            report.recommendations = self._generate_recommendations(report)
            
            report.total_modules = len(report.modules)
            report.total_dependencies = len(report.dependencies)
            report.graph = self.graph
            
            self.logger.info(f"Анализ завершен: {report.total_modules} модулей, "
                           f"{report.total_dependencies} зависимостей")
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе архитектуры: {e}")
            raise
        
        return report

    def _find_python_files(self, project_path: Path) -> List[Path]:
        """Находит все Python файлы в проекте"""
        python_files = []
        
        # Исключаемые директории
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 
                       'node_modules', '.idea', '.vscode', 'build', 'dist'}
        
        for file_path in project_path.rglob('*.py'):
            # Пропускаем файлы в исключаемых директориях
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue
            
            python_files.append(file_path)
        
        return sorted(python_files)

    def _analyze_file(self, file_path: Path, project_path: Path) -> Optional[ModuleInfo]:
        """Анализирует отдельный Python файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Определение имени модуля
            module_name = self._get_module_name(file_path, project_path)
            
            module_info = ModuleInfo(
                name=module_name,
                path=file_path,
                imports=[],
                exports=[],
                classes=[],
                functions=[],
                dependencies=[],
                dependents=[]
            )
            
            # Анализ AST
            visitor = ModuleAnalyzerVisitor(module_info)
            visitor.visit(tree)
            
            return module_info
            
        except Exception as e:
            self.logger.warning(f"Ошибка анализа файла {file_path}: {e}")
            return None

    def _get_module_name(self, file_path: Path, project_path: Path) -> str:
        """Определяет имя модуля относительно корня проекта"""
        relative_path = file_path.relative_to(project_path)
        
        # Убираем расширение .py
        module_path = relative_path.with_suffix('')
        
        # Заменяем разделители на точки
        module_name = str(module_path).replace('/', '.').replace('\\', '.')
        
        return module_name

    def _build_dependency_graph(self, report: ArchitectureReport) -> None:
        """Строит граф зависимостей"""
        self.graph.clear()
        
        # Добавляем узлы (модули)
        for module_info in report.modules:
            self.graph.add_node(module_info.name, module_info=module_info)
        
        # Добавляем ребра (зависимости)
        for module_info in report.modules:
            for import_name in module_info.imports:
                # Находим целевой модуль
                target_module = self._resolve_import(import_name, module_info.name)
                if target_module and target_module in self.graph:
                    # Добавляем ребро
                    self.graph.add_edge(module_info.name, target_module)
                    
                    # Создаем запись о зависимости
                    dependency = DependencyEdge(
                        source=module_info.name,
                        target=target_module,
                        type='import',
                        line_number=0,
                        details=f"import {import_name}"
                    )
                    report.dependencies.append(dependency)
                    
                    # Обновляем списки зависимостей
                    module_info.dependencies.append(target_module)
                    if target_module in self.modules_info:
                        self.modules_info[target_module].dependents.append(module_info.name)

    def _resolve_import(self, import_name: str, current_module: str) -> Optional[str]:
        """Разрешает импорт в имя модуля"""
        # Простые случаи
        if import_name in self.modules_info:
            return import_name
        
        # Относительные импорты
        if import_name.startswith('.'):
            # Упрощенная обработка относительных импортов
            parts = current_module.split('.')
            if import_name.startswith('..'):
                # Импорт из родительского модуля
                if len(parts) > 1:
                    return '.'.join(parts[:-1])
            else:
                # Импорт из текущего пакета
                return current_module
        
        # Абсолютные импорты
        for module_name in self.modules_info:
            if module_name.endswith(import_name) or module_name.split('.')[-1] == import_name:
                return module_name
        
        return None

    def _analyze_architecture_patterns(self, report: ArchitectureReport) -> None:
        """Анализирует паттерны архитектуры"""
        
        # Поиск циклических зависимостей
        try:
            cycles = list(nx.simple_cycles(self.graph))
            report.circular_dependencies = cycles
        except Exception as e:
            self.logger.warning(f"Ошибка поиска циклов: {e}")
        
        # Поиск изолированных модулей
        isolated = []
        for node in self.graph.nodes():
            if self.graph.in_degree(node) == 0 and self.graph.out_degree(node) == 0:
                isolated.append(node)
        report.isolated_modules = isolated
        
        # Поиск сильно связанных модулей
        highly_coupled = []
        for node in self.graph.nodes():
            total_degree = self.graph.in_degree(node) + self.graph.out_degree(node)
            if total_degree > 10:  # Порог для сильно связанных модулей
                highly_coupled.append(node)
        report.highly_coupled_modules = highly_coupled

    def _generate_recommendations(self, report: ArchitectureReport) -> List[str]:
        """Генерирует рекомендации по улучшению архитектуры"""
        recommendations = []
        
        # Циклические зависимости
        if report.circular_dependencies:
            recommendations.append(
                f"🔴 Обнаружено {len(report.circular_dependencies)} циклических зависимостей. "
                "Рассмотрите рефакторинг для устранения циклов."
            )
        
        # Изолированные модули
        if report.isolated_modules:
            recommendations.append(
                f"🟡 Найдено {len(report.isolated_modules)} изолированных модулей. "
                "Проверьте, не являются ли они мертвым кодом."
            )
        
        # Сильно связанные модули
        if report.highly_coupled_modules:
            recommendations.append(
                f"🟠 Обнаружено {len(report.highly_coupled_modules)} сильно связанных модулей. "
                "Рассмотрите разделение на более мелкие компоненты."
            )
        
        # Общие рекомендации
        if not recommendations:
            recommendations.append("✅ Архитектура выглядит хорошо структурированной!")
        
        return recommendations

    def visualize_dependencies(self, report: ArchitectureReport, 
                             output_path: Path, format: str = 'png') -> None:
        """
        Визуализирует граф зависимостей
        
        Args:
            report: Отчет об архитектуре
            output_path: Путь для сохранения изображения
            format: Формат изображения (png, svg, pdf)
        """
        if not report.graph:
            raise ValueError("Граф зависимостей не построен")
        
        try:
            plt.figure(figsize=(16, 12))
            
            # Позиционирование узлов
            pos = nx.spring_layout(report.graph, k=3, iterations=50)
            
            # Рисуем узлы
            nx.draw_networkx_nodes(report.graph, pos, 
                                 node_color='lightblue', 
                                 node_size=2000,
                                 alpha=0.7)
            
            # Рисуем ребра
            nx.draw_networkx_edges(report.graph, pos, 
                                 edge_color='gray',
                                 arrows=True,
                                 arrowsize=20,
                                 alpha=0.5)
            
            # Подписи узлов
            labels = {node: node.split('.')[-1] for node in report.graph.nodes()}
            nx.draw_networkx_labels(report.graph, pos, labels, font_size=8)
            
            plt.title("Граф зависимостей модулей", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            
            # Сохранение
            plt.savefig(output_path, format=format, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Граф зависимостей сохранен: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка визуализации: {e}")
            raise

    def export_report(self, report: ArchitectureReport, 
                     output_path: Path, format: str = 'json') -> None:
        """Экспортирует отчет в различных форматах"""
        try:
            if format.lower() == 'json':
                self._export_json(report, output_path)
            elif format.lower() == 'dot':
                self._export_dot(report, output_path)
            else:
                raise ValueError(f"Неподдерживаемый формат: {format}")
                
            self.logger.info(f"Отчет экспортирован в {output_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта отчета: {e}")
            raise

    def _export_json(self, report: ArchitectureReport, output_path: Path) -> None:
        """Экспорт в JSON"""
        data = {
            'summary': {
                'total_modules': report.total_modules,
                'total_dependencies': report.total_dependencies,
                'circular_dependencies_count': len(report.circular_dependencies),
                'isolated_modules_count': len(report.isolated_modules),
                'highly_coupled_modules_count': len(report.highly_coupled_modules)
            },
            'modules': [
                {
                    'name': m.name,
                    'path': str(m.path),
                    'imports': m.imports,
                    'classes': m.classes,
                    'functions': m.functions,
                    'dependencies': m.dependencies,
                    'dependents': m.dependents
                } for m in report.modules
            ],
            'dependencies': [
                {
                    'source': d.source,
                    'target': d.target,
                    'type': d.type,
                    'line_number': d.line_number,
                    'details': d.details
                } for d in report.dependencies
            ],
            'circular_dependencies': report.circular_dependencies,
            'isolated_modules': report.isolated_modules,
            'highly_coupled_modules': report.highly_coupled_modules,
            'recommendations': report.recommendations
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_dot(self, report: ArchitectureReport, output_path: Path) -> None:
        """Экспорт в DOT формат для Graphviz"""
        if not report.graph:
            return
        
        dot_content = ["digraph Dependencies {"]
        dot_content.append("  rankdir=TB;")
        dot_content.append("  node [shape=box, style=filled, fillcolor=lightblue];")
        
        # Узлы
        for node in report.graph.nodes():
            label = node.split('.')[-1]
            dot_content.append(f'  "{node}" [label="{label}"];')
        
        # Ребра
        for edge in report.graph.edges():
            dot_content.append(f'  "{edge[0]}" -> "{edge[1]}";')
        
        dot_content.append("}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(dot_content))


class ModuleAnalyzerVisitor(ast.NodeVisitor):
    """AST visitor для анализа модуля"""
    
    def __init__(self, module_info: ModuleInfo):
        self.module_info = module_info
    
    def visit_Import(self, node: ast.Import) -> None:
        """Обрабатывает import statements"""
        for alias in node.names:
            self.module_info.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Обрабатывает from ... import statements"""
        if node.module:
            self.module_info.imports.append(node.module)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Обрабатывает определения классов"""
        self.module_info.classes.append(node.name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Обрабатывает определения функций"""
        self.module_info.functions.append(node.name)
        self.generic_visit(node)

