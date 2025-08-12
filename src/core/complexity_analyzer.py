import ast
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ComplexityMetrics:
    """Метрики сложности кода"""
    lines_of_code: int = 0
    lines_of_comments: int = 0
    blank_lines: int = 0
    total_lines: int = 0
    cyclomatic_complexity: int = 0
    function_count: int = 0
    class_count: int = 0
    max_nesting_depth: int = 0
    average_nesting_depth: float = 0.0
    import_count: int = 0
    variable_count: int = 0
    magic_numbers: int = 0
    long_lines: int = 0
    long_functions: int = 0
    complex_functions: int = 0
    maintainability_index: float = 0.0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    issues: List[str] = field(default_factory=list)


@dataclass
class FunctionMetrics:
    """Метрики отдельной функции"""
    name: str
    line_number: int
    cyclomatic_complexity: int
    lines_of_code: int
    parameters: int
    nesting_depth: int
    variables: int
    magic_numbers: int
    maintainability_index: float


@dataclass
class ClassMetrics:
    """Метрики отдельного класса"""
    name: str
    line_number: int
    methods: int
    attributes: int
    inheritance_depth: int
    complexity: int
    lines_of_code: int


@dataclass
class FileComplexityReport:
    """Отчет о сложности файла"""
    file_path: Path
    metrics: ComplexityMetrics
    functions: List[FunctionMetrics]
    classes: List[ClassMetrics]
    issues: List[str]
    grade: str  # A, B, C, D, F


@dataclass
class ProjectComplexityReport:
    """Отчет о сложности проекта"""
    total_files: int
    total_lines: int
    average_complexity: float
    most_complex_files: List[Tuple[str, float]]
    most_complex_functions: List[Tuple[str, float]]
    complexity_distribution: Dict[str, int]
    maintainability_grades: Dict[str, int]
    recommendations: List[str]


class ComplexityAnalyzer:
    """Анализатор сложности кода"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._complexity_thresholds = {
            'cyclomatic': 10,
            'lines_per_function': 50,
            'nesting_depth': 4,
            'maintainability': 65
        }
        
    def analyze_file(self, file_path: Path) -> FileComplexityReport:
        """Анализирует сложность одного файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Базовые метрики строк
            lines = content.split('\n')
            metrics = self._calculate_basic_metrics(lines)
            
            # AST анализ
            try:
                tree = ast.parse(content, filename=str(file_path))
                self._analyze_ast(tree, metrics)
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {file_path}: {e}")
                metrics.issues.append(f"Syntax error: {e}")
            
            # Дополнительные метрики
            self._calculate_advanced_metrics(content, metrics)
            
            # Анализ функций и классов
            functions = self._extract_function_metrics(tree, content)
            classes = self._extract_class_metrics(tree, content)
            
            # Определение оценки
            grade = self._calculate_grade(metrics)
            
            return FileComplexityReport(
                file_path=file_path,
                metrics=metrics,
                functions=functions,
                classes=classes,
                issues=metrics.issues,
                grade=grade
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return FileComplexityReport(
                file_path=file_path,
                metrics=ComplexityMetrics(),
                functions=[],
                classes=[],
                issues=[f"Analysis error: {e}"],
                grade="F"
            )
    
    def analyze_project(self, directory: Path) -> ProjectComplexityReport:
        """Анализирует сложность всего проекта"""
        python_files = list(directory.rglob("*.py"))
        file_reports = []
        
        for file_path in python_files:
            report = self.analyze_file(file_path)
            file_reports.append(report)
        
        return self._create_project_report(file_reports)
    
    def _calculate_basic_metrics(self, lines: List[str]) -> ComplexityMetrics:
        """Вычисляет базовые метрики строк"""
        metrics = ComplexityMetrics()
        metrics.total_lines = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith('#'):
                metrics.lines_of_comments += 1
            else:
                metrics.lines_of_code += 1
                
            # Длинные строки
            if len(line) > 79:
                metrics.long_lines += 1
                
        return metrics
    
    def _analyze_ast(self, tree: ast.AST, metrics: ComplexityMetrics) -> None:
        """Анализирует AST для вычисления метрик"""
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        metrics.cyclomatic_complexity = visitor.complexity
        metrics.function_count = visitor.function_count
        metrics.class_count = visitor.class_count
        metrics.max_nesting_depth = visitor.max_nesting_depth
        metrics.average_nesting_depth = visitor.average_nesting_depth
        metrics.import_count = visitor.import_count
        metrics.variable_count = visitor.variable_count
        metrics.magic_numbers = visitor.magic_numbers
        
        # Длинные функции
        metrics.long_functions = sum(1 for func in visitor.functions 
                                   if func['lines'] > self._complexity_thresholds['lines_per_function'])
        
        # Сложные функции
        metrics.complex_functions = sum(1 for func in visitor.functions 
                                      if func['complexity'] > self._complexity_thresholds['cyclomatic'])
    
    def _calculate_advanced_metrics(self, content: str, metrics: ComplexityMetrics) -> None:
        """Вычисляет продвинутые метрики"""
        # Индекс поддерживаемости
        metrics.maintainability_index = self._calculate_maintainability_index(metrics)
        
        # Метрики Холстеда
        halstead = self._calculate_halstead_metrics(content)
        metrics.halstead_volume = halstead['volume']
        metrics.halstead_difficulty = halstead['difficulty']
        metrics.halstead_effort = halstead['effort']
    
    def _calculate_maintainability_index(self, metrics: ComplexityMetrics) -> float:
        """Вычисляет индекс поддерживаемости"""
        if metrics.lines_of_code == 0:
            return 100.0
            
        # Формула MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        hv = max(metrics.halstead_volume, 1)
        loc = max(metrics.lines_of_code, 1)
        
        mi = 171 - 5.2 * math.log(hv) - 0.23 * metrics.cyclomatic_complexity - 16.2 * math.log(loc)
        return max(0, min(100, mi))
    
    def _calculate_halstead_metrics(self, content: str) -> Dict[str, float]:
        """Вычисляет метрики Холстеда"""
        # Упрощенная реализация
        operators = ['+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', 
                    'and', 'or', 'not', 'if', 'else', 'for', 'while', 'def', 'class']
        
        operands = []
        operator_count = 0
        
        # Простой подсчет операторов и операндов
        for op in operators:
            operator_count += content.count(op)
        
        # Подсчет уникальных операторов и операндов
        unique_operators = len(set(op for op in operators if op in content))
        unique_operands = len(set(word for word in content.split() 
                                if word.isidentifier() and word not in operators))
        
        n1 = unique_operators
        n2 = unique_operands
        N1 = operator_count
        N2 = len(content.split()) - operator_count
        
        if n1 == 0 or n2 == 0:
            return {'volume': 0, 'difficulty': 0, 'effort': 0}
        
        volume = (N1 + N2) * math.log2(n1 + n2)
        difficulty = (n1 * N2) / (2 * n2) if n2 > 0 else 0
        effort = volume * difficulty
        
        return {
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort
        }
    
    def _extract_function_metrics(self, tree: ast.AST, content: str) -> List[FunctionMetrics]:
        """Извлекает метрики функций"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_visitor = FunctionVisitor()
                func_visitor.visit(node)
                
                # Подсчет строк функции
                lines = content.split('\n')
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                func_lines = len(lines[start_line:end_line])
                
                # Индекс поддерживаемости для функции
                mi = self._calculate_function_maintainability(func_visitor.complexity, func_lines)
                
                functions.append(FunctionMetrics(
                    name=node.name,
                    line_number=node.lineno,
                    cyclomatic_complexity=func_visitor.complexity,
                    lines_of_code=func_lines,
                    parameters=len(node.args.args),
                    nesting_depth=func_visitor.max_nesting,
                    variables=func_visitor.variables,
                    magic_numbers=func_visitor.magic_numbers,
                    maintainability_index=mi
                ))
        
        return functions
    
    def _extract_class_metrics(self, tree: ast.AST, content: str) -> List[ClassMetrics]:
        """Извлекает метрики классов"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_visitor = ClassVisitor()
                class_visitor.visit(node)
                
                # Подсчет строк класса
                lines = content.split('\n')
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                class_lines = len(lines[start_line:end_line])
                
                classes.append(ClassMetrics(
                    name=node.name,
                    line_number=node.lineno,
                    methods=class_visitor.methods,
                    attributes=class_visitor.attributes,
                    inheritance_depth=len(node.bases),
                    complexity=class_visitor.complexity,
                    lines_of_code=class_lines
                ))
        
        return classes
    
    def _calculate_function_maintainability(self, complexity: int, lines: int) -> float:
        """Вычисляет индекс поддерживаемости для функции"""
        if lines == 0:
            return 100.0
        
        # Упрощенная формула для функций
        mi = 100 - complexity * 2 - lines * 0.5
        return max(0, min(100, mi))
    
    def _calculate_grade(self, metrics: ComplexityMetrics) -> str:
        """Вычисляет оценку сложности"""
        score = 0
        
        # Цикломатическая сложность
        if metrics.cyclomatic_complexity <= 5:
            score += 25
        elif metrics.cyclomatic_complexity <= 10:
            score += 15
        elif metrics.cyclomatic_complexity <= 15:
            score += 5
        
        # Индекс поддерживаемости
        if metrics.maintainability_index >= 85:
            score += 25
        elif metrics.maintainability_index >= 65:
            score += 15
        elif metrics.maintainability_index >= 50:
            score += 5
        
        # Глубина вложенности
        if metrics.max_nesting_depth <= 3:
            score += 25
        elif metrics.max_nesting_depth <= 5:
            score += 15
        elif metrics.max_nesting_depth <= 7:
            score += 5
        
        # Размер функций
        if metrics.long_functions == 0:
            score += 25
        elif metrics.long_functions <= 2:
            score += 15
        elif metrics.long_functions <= 5:
            score += 5
        
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _create_project_report(self, file_reports: List[FileComplexityReport]) -> ProjectComplexityReport:
        """Создает отчет по проекту"""
        total_files = len(file_reports)
        total_lines = sum(r.metrics.total_lines for r in file_reports)
        average_complexity = sum(r.metrics.cyclomatic_complexity for r in file_reports) / total_files if total_files > 0 else 0
        
        # Самые сложные файлы
        file_complexities = [(str(r.file_path), r.metrics.cyclomatic_complexity) 
                            for r in file_reports]
        most_complex_files = sorted(file_complexities, key=lambda x: x[1], reverse=True)[:10]
        
        # Самые сложные функции
        all_functions = []
        for report in file_reports:
            for func in report.functions:
                all_functions.append((f"{report.file_path.name}:{func.name}", func.cyclomatic_complexity))
        most_complex_functions = sorted(all_functions, key=lambda x: x[1], reverse=True)[:10]
        
        # Распределение сложности
        complexity_distribution = Counter()
        for report in file_reports:
            grade = report.grade
            complexity_distribution[grade] += 1
        
        # Распределение оценок поддерживаемости
        maintainability_grades = Counter()
        for report in file_reports:
            if report.metrics.maintainability_index >= 85:
                maintainability_grades["Excellent"] += 1
            elif report.metrics.maintainability_index >= 65:
                maintainability_grades["Good"] += 1
            elif report.metrics.maintainability_index >= 50:
                maintainability_grades["Fair"] += 1
            else:
                maintainability_grades["Poor"] += 1
        
        # Рекомендации
        recommendations = self._generate_recommendations(file_reports)
        
        return ProjectComplexityReport(
            total_files=total_files,
            total_lines=total_lines,
            average_complexity=average_complexity,
            most_complex_files=most_complex_files,
            most_complex_functions=most_complex_functions,
            complexity_distribution=dict(complexity_distribution),
            maintainability_grades=dict(maintainability_grades),
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, file_reports: List[FileComplexityReport]) -> List[str]:
        """Генерирует рекомендации по улучшению"""
        recommendations = []
        
        # Анализ проблем
        high_complexity_files = [r for r in file_reports if r.metrics.cyclomatic_complexity > 15]
        low_maintainability_files = [r for r in file_reports if r.metrics.maintainability_index < 50]
        long_functions = sum(r.metrics.long_functions for r in file_reports)
        deep_nesting = [r for r in file_reports if r.metrics.max_nesting_depth > 5]
        
        if high_complexity_files:
            recommendations.append(f"Refactor {len(high_complexity_files)} files with high cyclomatic complexity")
        
        if low_maintainability_files:
            recommendations.append(f"Improve maintainability of {len(low_maintainability_files)} files")
        
        if long_functions > 0:
            recommendations.append(f"Break down {long_functions} long functions into smaller ones")
        
        if deep_nesting:
            recommendations.append(f"Reduce nesting depth in {len(deep_nesting)} files")
        
        if not recommendations:
            recommendations.append("Code quality is good! Keep up the good work.")
        
        return recommendations


class ComplexityVisitor(ast.NodeVisitor):
    """Посетитель AST для анализа сложности"""
    
    def __init__(self):
        self.complexity = 1  # Базовая сложность
        self.function_count = 0
        self.class_count = 0
        self.max_nesting_depth = 0
        self.current_nesting = 0
        self.nesting_depths = []
        self.import_count = 0
        self.variable_count = 0
        self.magic_numbers = 0
        self.functions = []
    
    def visit(self, node):
        """Переопределяем visit для отслеживания вложенности"""
        self.current_nesting += 1
        self.max_nesting_depth = max(self.max_nesting_depth, self.current_nesting)
        self.nesting_depths.append(self.current_nesting)
        
        super().visit(node)
        
        self.current_nesting -= 1
    
    def visit_FunctionDef(self, node):
        """Посещение функции"""
        self.function_count += 1
        self.complexity += 1  # Базовая сложность функции
        
        # Подсчет строк функции
        if hasattr(node, 'end_lineno'):
            lines = node.end_lineno - node.lineno + 1
        else:
            lines = 1
        
        self.functions.append({
            'name': node.name,
            'lines': lines,
            'complexity': 1
        })
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Посещение асинхронной функции"""
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node):
        """Посещение класса"""
        self.class_count += 1
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Посещение условного оператора"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        """Посещение цикла while"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        """Посещение цикла for"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        """Посещение обработчика исключений"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        """Посещение контекстного менеджера"""
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Посещение импорта"""
        self.import_count += len(node.names)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Посещение импорта from"""
        self.import_count += 1
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Посещение присваивания"""
        self.variable_count += len(node.targets)
        self.generic_visit(node)
    
    def visit_Num(self, node):
        """Посещение числа"""
        # Простая эвристика для магических чисел
        if isinstance(node.n, (int, float)) and abs(node.n) > 10:
            self.magic_numbers += 1
        self.generic_visit(node)
    
    @property
    def average_nesting_depth(self) -> float:
        """Средняя глубина вложенности"""
        if not self.nesting_depths:
            return 0.0
        return sum(self.nesting_depths) / len(self.nesting_depths)


class FunctionVisitor(ast.NodeVisitor):
    """Посетитель для анализа функций"""
    
    def __init__(self):
        self.complexity = 1
        self.variables = 0
        self.magic_numbers = 0
        self.max_nesting = 0
        self.current_nesting = 0
    
    def visit(self, node):
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        super().visit(node)
        self.current_nesting -= 1
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        self.variables += len(node.targets)
        self.generic_visit(node)
    
    def visit_Num(self, node):
        if isinstance(node.n, (int, float)) and abs(node.n) > 10:
            self.magic_numbers += 1
        self.generic_visit(node)


class ClassVisitor(ast.NodeVisitor):
    """Посетитель для анализа классов"""
    
    def __init__(self):
        self.methods = 0
        self.attributes = 0
        self.complexity = 1
    
    def visit_FunctionDef(self, node):
        self.methods += 1
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.methods += 1
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        # Простая эвристика для атрибутов класса
        if isinstance(node.targets[0], ast.Attribute):
            self.attributes += 1
        self.generic_visit(node)
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
