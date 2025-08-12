"""
Модуль анализа качества кода
Включает проверки PEP8, цикломатической сложности, когнитивной сложности и дублирования кода
"""
import ast
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PEP8Violation:
    """Нарушение PEP8"""
    line_number: int
    column: int
    code: str
    message: str
    severity: str  # 'error', 'warning', 'convention'


@dataclass
class CognitiveComplexity:
    """Когнитивная сложность"""
    function_name: str
    line_number: int
    complexity: int
    factors: List[str]  # Факторы, увеличивающие сложность


@dataclass
class CodeDuplication:
    """Дублирование кода"""
    block_hash: str
    lines: List[int]
    content: str
    occurrences: int
    similarity: float


@dataclass
class FunctionQuality:
    """Качество функции"""
    name: str
    line_number: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    parameters_count: int
    nesting_depth: int
    issues: List[str] = field(default_factory=list)


@dataclass
class CodeQualityReport:
    """Отчет о качестве кода"""
    file_path: Path
    pep8_violations: List[PEP8Violation] = field(default_factory=list)
    functions_quality: List[FunctionQuality] = field(default_factory=list)
    cognitive_complexity: List[CognitiveComplexity] = field(default_factory=list)
    code_duplications: List[CodeDuplication] = field(default_factory=list)
    overall_score: float = 0.0
    issues_count: int = 0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ProjectQualityReport:
    """Отчет о качестве проекта"""
    files_reports: List[CodeQualityReport] = field(default_factory=list)
    total_files: int = 0
    total_issues: int = 0
    average_score: float = 0.0
    worst_files: List[str] = field(default_factory=list)
    best_files: List[str] = field(default_factory=list)
    most_complex_functions: List[str] = field(default_factory=list)
    duplicate_blocks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class CodeQualityAnalyzer:
    """Анализатор качества кода"""
    
    def __init__(self) -> None:
        self.logger = get_logger("CodeQualityAnalyzer")
        
        # PEP8 правила
        self.pep8_rules = {
            'E101': (r'^\s*\t', 'Indentation contains tabs'),
            'E111': (r'^\s{1,3}(?!\s)', 'Indentation is not a multiple of four'),
            'E112': (r'^\s{5,}(?!\s)', 'Expected an indented block'),
            'E113': (r'^\s+\S', 'Unexpected indentation'),
            'E201': (r'[^#]\s{2,}$', 'Whitespace after \'(\''),
            'E202': (r'^\s+\S', 'Whitespace before \')\''),
            'E203': (r'[^#]\s{2,}$', 'Whitespace before \':\''),
            'E211': (r'[^#]\s{2,}$', 'Whitespace before \'(\''),
            'E221': (r'[^#]\s{2,}$', 'Multiple spaces before operator'),
            'E222': (r'[^#]\s{2,}$', 'Multiple spaces after operator'),
            'E225': (r'[^#]\s{2,}$', 'Missing whitespace around operator'),
            'E226': (r'[^#]\s{2,}$', 'Missing whitespace around arithmetic operator'),
            'E227': (r'[^#]\s{2,}$', 'Missing whitespace around bitwise or shift operator'),
            'E228': (r'[^#]\s{2,}$', 'Missing whitespace around modulo operator'),
            'E231': (r'[^#]\s{2,}$', 'Missing whitespace after \',\''),
            'E241': (r'[^#]\s{2,}$', 'Multiple spaces after \',\''),
            'E242': (r'[^#]\s{2,}$', 'Tab after \',\''),
            'E251': (r'[^#]\s{2,}$', 'Unexpected spaces around keyword / parameter equals'),
            'E261': (r'[^#]\s{2,}$', 'At least two spaces before inline comment'),
            'E262': (r'[^#]\s{2,}$', 'Inline comment should start with \'# \''),
            'E265': (r'[^#]\s{2,}$', 'Block comment should start with \'# \''),
            'E266': (r'[^#]\s{2,}$', 'Too many leading \'#\' for block comment'),
            'E271': (r'[^#]\s{2,}$', 'Multiple spaces after keyword'),
            'E272': (r'[^#]\s{2,}$', 'Multiple spaces before keyword'),
            'E273': (r'[^#]\s{2,}$', 'Tab after keyword'),
            'E274': (r'[^#]\s{2,}$', 'Tab before keyword'),
            'E275': (r'[^#]\s{2,}$', 'Missing whitespace after keyword'),
            'E301': (r'[^#]\s{2,}$', 'Expected 1 blank line, found 0'),
            'E302': (r'[^#]\s{2,}$', 'Expected 2 blank lines, found 0'),
            'E303': (r'[^#]\s{2,}$', 'Too many blank lines'),
            'E304': (r'[^#]\s{2,}$', 'Blank lines found after function decorator'),
            'E305': (r'[^#]\s{2,}$', 'Expected 2 blank lines after class or function definition'),
            'E306': (r'[^#]\s{2,}$', 'Expected 1 blank line before a nested definition'),
            'E401': (r'[^#]\s{2,}$', 'Multiple imports on one line'),
            'E402': (r'[^#]\s{2,}$', 'Module level import not at top of file'),
            'E501': (r'^.{80,}$', 'Line too long (over 79 characters)'),
            'E502': (r'[^#]\s{2,}$', 'The backslash is redundant between brackets'),
            'E701': (r'[^#]\s{2,}$', 'Multiple statements on one line (colon)'),
            'E702': (r'[^#]\s{2,}$', 'Multiple statements on one line (semicolon)'),
            'E703': (r'[^#]\s{2,}$', 'Statement ends with a semicolon'),
            'E711': (r'[^#]\s{2,}$', 'Comparison to None should be \'if cond is None:\''),
            'E712': (r'[^#]\s{2,}$', 'Comparison to True should be \'if cond is True:\' or \'if cond:\''),
            'E713': (r'[^#]\s{2,}$', 'Test for membership should be \'not in\''),
            'E714': (r'[^#]\s{2,}$', 'Test for object identity should be \'is not\''),
            'E721': (r'[^#]\s{2,}$', 'Do not compare types, use \'isinstance()\''),
            'E722': (r'[^#]\s{2,}$', 'Do not use bare except, specify exception instead'),
            'E731': (r'[^#]\s{2,}$', 'Do not assign a lambda expression, use a def'),
            'E741': (r'[^#]\s{2,}$', 'Ambiguous variable name \'l\''),
            'E742': (r'[^#]\s{2,}$', 'Ambiguous function name \'l\''),
            'E743': (r'[^#]\s{2,}$', 'Ambiguous class name \'l\''),
            'E901': (r'[^#]\s{2,}$', 'SyntaxError or IndentationError'),
            'E902': (r'[^#]\s{2,}$', 'IOError (file not found, permission denied, etc.)'),
            'W191': (r'[^#]\s{2,}$', 'Indentation contains tabs'),
            'W291': (r'[^#]\s{2,}$', 'Trailing whitespace'),
            'W292': (r'[^#]\s{2,}$', 'No newline at end of file'),
            'W293': (r'[^#]\s{2,}$', 'Blank line contains whitespace'),
            'W391': (r'[^#]\s{2,}$', 'Blank line at end of file'),
            'W503': (r'[^#]\s{2,}$', 'Line break before binary operator'),
            'W504': (r'[^#]\s{2,}$', 'Line break after binary operator'),
            'W505': (r'[^#]\s{2,}$', 'doc line too long'),
            'W601': (r'[^#]\s{2,}$', '.has_key() is deprecated, use \'in\''),
            'W602': (r'[^#]\s{2,}$', 'Deprecated form of raising exception'),
            'W603': (r'[^#]\s{2,}$', '\'<>\' is deprecated, use \'!=\''),
            'W604': (r'[^#]\s{2,}$', 'backticks are deprecated, use \'repr()\''),
            'W605': (r'[^#]\s{2,}$', 'Invalid escape sequence'),
            'W606': (r'[^#]\s{2,}$', '\'async\' and \'await\' are reserved keywords starting with Python 3.7'),
        }
        
        # Факторы когнитивной сложности
        self.cognitive_factors = {
            'if': 1,
            'elif': 1,
            'else': 1,
            'for': 1,
            'while': 1,
            'try': 1,
            'except': 1,
            'finally': 1,
            'with': 1,
            'and': 1,
            'or': 1,
            'not': 1,
            'in': 1,
            'is': 1,
            'lambda': 1,
            'list_comp': 1,
            'dict_comp': 1,
            'set_comp': 1,
            'gen_expr': 1,
        }
    
    def analyze_file(self, file_path: Path) -> CodeQualityReport:
        """Анализирует качество кода в файле"""
        self.logger.info(f"Анализ качества кода файла: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Парсинг AST
            tree = ast.parse(content)
            
            # Создание отчета
            report = CodeQualityReport(file_path=file_path)
            
            # PEP8 проверки
            report.pep8_violations = self._check_pep8(lines)
            
            # Анализ функций
            report.functions_quality = self._analyze_functions_quality(tree, lines)
            
            # Когнитивная сложность
            report.cognitive_complexity = self._analyze_cognitive_complexity(tree, lines)
            
            # Дублирование кода
            report.code_duplications = self._find_code_duplications(lines)
            
            # Подсчет общего количества проблем
            report.issues_count = (
                len(report.pep8_violations) +
                len([f for f in report.functions_quality if f.issues]) +
                len([c for c in report.cognitive_complexity if c.complexity > 10]) +
                len([d for d in report.code_duplications if d.occurrences > 2])
            )
            
            # Расчет общего балла
            report.overall_score = self._calculate_quality_score(report)
            
            # Генерация рекомендаций
            report.recommendations = self._generate_recommendations(report)
            
            self.logger.info(f"Анализ завершен: {report.issues_count} проблем найдено")
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа файла {file_path}: {e}")
            return CodeQualityReport(file_path=file_path)
    
    def analyze_project(self, directory: Path) -> ProjectQualityReport:
        """Анализирует качество кода в проекте"""
        self.logger.info(f"Анализ качества кода проекта: {directory}")
        
        project_report = ProjectQualityReport()
        
        # Поиск Python файлов
        python_files = list(directory.rglob("*.py"))
        project_report.total_files = len(python_files)
        
        # Анализ каждого файла
        for file_path in python_files:
            try:
                file_report = self.analyze_file(file_path)
                project_report.files_reports.append(file_report)
            except Exception as e:
                self.logger.error(f"Ошибка анализа файла {file_path}: {e}")
        
        # Агрегация результатов
        self._aggregate_project_results(project_report)
        
        self.logger.info(f"Анализ проекта завершен: {project_report.total_issues} проблем")
        return project_report
    
    def _check_pep8(self, lines: List[str]) -> List[PEP8Violation]:
        """Проверяет соответствие PEP8"""
        violations = []
        
        for line_num, line in enumerate(lines, 1):
            # Проверка длины строки
            if len(line) > 79:
                violations.append(PEP8Violation(
                    line_number=line_num,
                    column=80,
                    code='E501',
                    message=f'Line too long ({len(line)} > 79 characters)',
                    severity='error'
                ))
            
            # Проверка отступов
            if line.strip() and not line.startswith('#'):
                indent = len(line) - len(line.lstrip())
                if indent % 4 != 0:
                    violations.append(PEP8Violation(
                        line_number=line_num,
                        column=1,
                        code='E111',
                        message='Indentation is not a multiple of four',
                        severity='error'
                    ))
            
            # Проверка табуляции
            if '\t' in line:
                violations.append(PEP8Violation(
                    line_number=line_num,
                    column=line.find('\t') + 1,
                    code='E101',
                    message='Indentation contains tabs',
                    severity='error'
                ))
            
            # Проверка пробелов в конце строки
            if line.rstrip() != line:
                violations.append(PEP8Violation(
                    line_number=line_num,
                    column=len(line.rstrip()) + 1,
                    code='W291',
                    message='Trailing whitespace',
                    severity='warning'
                ))
        
        return violations
    
    def _analyze_functions_quality(self, tree: ast.AST, lines: List[str]) -> List[FunctionQuality]:
        """Анализирует качество функций"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_quality = FunctionQuality(
                    name=node.name,
                    line_number=node.lineno,
                    cyclomatic_complexity=self._calculate_cyclomatic_complexity(node),
                    cognitive_complexity=self._calculate_cognitive_complexity(node),
                    lines_of_code=self._count_function_lines(node, lines),
                    parameters_count=len(node.args.args),
                    nesting_depth=self._calculate_nesting_depth(node)
                )
                
                # Выявление проблем
                if func_quality.cyclomatic_complexity > 10:
                    func_quality.issues.append(
                        f"High cyclomatic complexity ({func_quality.cyclomatic_complexity})"
                    )
                
                if func_quality.cognitive_complexity > 15:
                    func_quality.issues.append(
                        f"High cognitive complexity ({func_quality.cognitive_complexity})"
                    )
                
                if func_quality.lines_of_code > 50:
                    func_quality.issues.append(
                        f"Function too long ({func_quality.lines_of_code} lines)"
                    )
                
                if func_quality.parameters_count > 5:
                    func_quality.issues.append(
                        f"Too many parameters ({func_quality.parameters_count})"
                    )
                
                if func_quality.nesting_depth > 4:
                    func_quality.issues.append(
                        f"Deep nesting ({func_quality.nesting_depth} levels)"
                    )
                
                functions.append(func_quality)
        
        return functions
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Вычисляет цикломатическую сложность"""
        complexity = 1  # Базовая сложность
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Вычисляет когнитивную сложность"""
        complexity = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                complexity += 1
            elif isinstance(child, ast.While):
                complexity += 1
            elif isinstance(child, ast.For):
                complexity += 1
            elif isinstance(child, ast.AsyncFor):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                if isinstance(child.op, (ast.And, ast.Or)):
                    complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                complexity += 1
            elif isinstance(child, ast.DictComp):
                complexity += 1
            elif isinstance(child, ast.SetComp):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1
        
        return complexity
    
    def _count_function_lines(self, node: ast.AST, lines: List[str]) -> int:
        """Подсчитывает количество строк в функции"""
        if hasattr(node, 'end_lineno'):
            return node.end_lineno - node.lineno + 1
        else:
            # Приблизительный подсчет
            return 1
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Вычисляет глубину вложенности"""
        max_depth = 0
        current_depth = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(child, ast.FunctionDef):
                # Сброс глубины для вложенных функций
                current_depth = 0
        
        return max_depth
    
    def _analyze_cognitive_complexity(self, tree: ast.AST, lines: List[str]) -> List[CognitiveComplexity]:
        """Анализирует когнитивную сложность"""
        complexities = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cognitive_complexity(node)
                factors = self._identify_cognitive_factors(node)
                
                complexities.append(CognitiveComplexity(
                    function_name=node.name,
                    line_number=node.lineno,
                    complexity=complexity,
                    factors=factors
                ))
        
        return complexities
    
    def _identify_cognitive_factors(self, node: ast.AST) -> List[str]:
        """Идентифицирует факторы когнитивной сложности"""
        factors = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                factors.append('if')
            elif isinstance(child, ast.While):
                factors.append('while')
            elif isinstance(child, ast.For):
                factors.append('for')
            elif isinstance(child, ast.Try):
                factors.append('try')
            elif isinstance(child, ast.ExceptHandler):
                factors.append('except')
            elif isinstance(child, ast.With):
                factors.append('with')
            elif isinstance(child, ast.BoolOp):
                if isinstance(child.op, ast.And):
                    factors.extend(['and'] * (len(child.values) - 1))
                elif isinstance(child.op, ast.Or):
                    factors.extend(['or'] * (len(child.values) - 1))
            elif isinstance(child, ast.ListComp):
                factors.append('list_comp')
            elif isinstance(child, ast.DictComp):
                factors.append('dict_comp')
            elif isinstance(child, ast.SetComp):
                factors.append('set_comp')
            elif isinstance(child, ast.GeneratorExp):
                factors.append('gen_expr')
        
        return factors
    
    def _find_code_duplications(self, lines: List[str]) -> List[CodeDuplication]:
        """Находит дублирование кода"""
        duplications = []
        block_size = 3  # Минимальный размер блока для поиска дублирования
        
        # Создание хешей для блоков кода
        blocks = {}
        for i in range(len(lines) - block_size + 1):
            block_lines = lines[i:i + block_size]
            block_content = '\n'.join(block_lines)
            
            # Нормализация (удаление комментариев и лишних пробелов)
            normalized_content = self._normalize_code_block(block_content)
            if len(normalized_content.strip()) < 10:  # Игнорируем слишком короткие блоки
                continue
            
            block_hash = hashlib.md5(normalized_content.encode()).hexdigest()
            
            if block_hash not in blocks:
                blocks[block_hash] = {
                    'content': block_content,
                    'lines': [i + 1],
                    'normalized': normalized_content
                }
            else:
                blocks[block_hash]['lines'].append(i + 1)
        
        # Фильтрация дублирований
        for block_hash, block_data in blocks.items():
            if len(block_data['lines']) > 1:
                # Вычисление схожести
                similarity = self._calculate_similarity(block_data['normalized'])
                
                duplications.append(CodeDuplication(
                    block_hash=block_hash,
                    lines=block_data['lines'],
                    content=block_data['content'],
                    occurrences=len(block_data['lines']),
                    similarity=similarity
                ))
        
        # Сортировка по количеству вхождений
        duplications.sort(key=lambda x: x.occurrences, reverse=True)
        
        return duplications[:10]  # Возвращаем топ-10 дублирований
    
    def _normalize_code_block(self, content: str) -> str:
        """Нормализует блок кода для сравнения"""
        # Удаление комментариев
        lines = []
        for line in content.split('\n'):
            comment_pos = line.find('#')
            if comment_pos != -1:
                line = line[:comment_pos]
            lines.append(line.rstrip())
        
        # Удаление пустых строк
        lines = [line for line in lines if line.strip()]
        
        # Нормализация отступов
        normalized_lines = []
        for line in lines:
            indent = len(line) - len(line.lstrip())
            normalized_indent = ' ' * (indent // 4 * 4)
            normalized_lines.append(normalized_indent + line.lstrip())
        
        return '\n'.join(normalized_lines)
    
    def _calculate_similarity(self, content: str) -> float:
        """Вычисляет схожесть кода"""
        # Простая метрика схожести на основе длины
        return min(1.0, len(content) / 100.0)
    
    def _calculate_quality_score(self, report: CodeQualityReport) -> float:
        """Вычисляет общий балл качества"""
        max_score = 100.0
        deductions = 0.0
        
        # Штрафы за PEP8 нарушения
        for violation in report.pep8_violations:
            if violation.severity == 'error':
                deductions += 2.0
            elif violation.severity == 'warning':
                deductions += 1.0
            else:
                deductions += 0.5
        
        # Штрафы за проблемы с функциями
        for func in report.functions_quality:
            if func.cyclomatic_complexity > 10:
                deductions += 5.0
            if func.cognitive_complexity > 15:
                deductions += 3.0
            if func.lines_of_code > 50:
                deductions += 2.0
            if func.parameters_count > 5:
                deductions += 1.0
            if func.nesting_depth > 4:
                deductions += 2.0
        
        # Штрафы за дублирование
        for dup in report.code_duplications:
            if dup.occurrences > 3:
                deductions += 3.0
        
        return max(0.0, max_score - deductions)
    
    def _generate_recommendations(self, report: CodeQualityReport) -> List[str]:
        """Генерирует рекомендации по улучшению"""
        recommendations = []
        
        # PEP8 рекомендации
        pep8_errors = [v for v in report.pep8_violations if v.severity == 'error']
        if pep8_errors:
            recommendations.append(f"Fix {len(pep8_errors)} PEP8 errors")
        
        # Рекомендации по функциям
        complex_functions = [f for f in report.functions_quality if f.cyclomatic_complexity > 10]
        if complex_functions:
            recommendations.append(f"Refactor {len(complex_functions)} complex functions")
        
        long_functions = [f for f in report.functions_quality if f.lines_of_code > 50]
        if long_functions:
            recommendations.append(f"Split {len(long_functions)} long functions")
        
        # Рекомендации по дублированию
        significant_dups = [d for d in report.code_duplications if d.occurrences > 2]
        if significant_dups:
            recommendations.append(f"Extract {len(significant_dups)} duplicate code blocks")
        
        return recommendations
    
    def _aggregate_project_results(self, project_report: ProjectQualityReport) -> None:
        """Агрегирует результаты проекта"""
        # Подсчет общего количества проблем
        project_report.total_issues = sum(
            report.issues_count for report in project_report.files_reports
        )
        
        # Вычисление среднего балла
        if project_report.files_reports:
            project_report.average_score = sum(
                report.overall_score for report in project_report.files_reports
            ) / len(project_report.files_reports)
        
        # Нахождение худших и лучших файлов
        sorted_reports = sorted(
            project_report.files_reports,
            key=lambda x: x.overall_score
        )
        
        project_report.worst_files = [
            str(report.file_path.name) for report in sorted_reports[:5]
        ]
        project_report.best_files = [
            str(report.file_path.name) for report in sorted_reports[-5:]
        ]
        
        # Нахождение самых сложных функций
        all_functions = []
        for report in project_report.files_reports:
            for func in report.functions_quality:
                all_functions.append((func, report.file_path))
        
        complex_functions = sorted(
            all_functions,
            key=lambda x: x[0].cyclomatic_complexity,
            reverse=True
        )
        
        project_report.most_complex_functions = [
            f"{func.name} in {path.name} (CC: {func.cyclomatic_complexity})"
            for func, path in complex_functions[:10]
        ]
        
        # Нахождение дублирований
        all_duplications = []
        for report in project_report.files_reports:
            for dup in report.code_duplications:
                all_duplications.append((dup, report.file_path))
        
        significant_dups = sorted(
            all_duplications,
            key=lambda x: x[0].occurrences,
            reverse=True
        )
        
        project_report.duplicate_blocks = [
            f"{dup.occurrences} occurrences in {path.name}"
            for dup, path in significant_dups[:10]
        ]
        
        # Генерация общих рекомендаций
        project_report.recommendations = self._generate_project_recommendations(project_report)
    
    def _generate_project_recommendations(self, project_report: ProjectQualityReport) -> List[str]:
        """Генерирует рекомендации для проекта"""
        recommendations = []
        
        if project_report.average_score < 70:
            recommendations.append("Overall code quality needs improvement")
        
        if project_report.total_issues > 100:
            recommendations.append("High number of code quality issues detected")
        
        if len(project_report.most_complex_functions) > 5:
            recommendations.append("Multiple complex functions need refactoring")
        
        if len(project_report.duplicate_blocks) > 5:
            recommendations.append("Significant code duplication detected")
        
        if not recommendations:
            recommendations.append("Code quality is generally good")
        
        return recommendations
