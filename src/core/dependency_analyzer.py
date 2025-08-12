"""
Модуль анализа зависимостей
Включает поиск уязвимостей, анализ лицензий, проверку устаревших пакетов и оптимизацию requirements
"""
import subprocess
import json
import re
import requests
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from packaging import version
from packaging.requirements import Requirement
import logging

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PackageInfo:
    """Информация о пакете"""
    name: str
    version: str
    license: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    is_outdated: bool = False
    latest_version: Optional[str] = None
    update_recommendation: Optional[str] = None


@dataclass
class Vulnerability:
    """Информация об уязвимости"""
    package_name: str
    version: str
    vulnerability_id: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    cve_id: Optional[str] = None
    affected_versions: str = ""
    fixed_versions: str = ""


@dataclass
class LicenseInfo:
    """Информация о лицензии"""
    package_name: str
    license_type: str
    license_text: Optional[str] = None
    is_compatible: bool = True
    compatibility_notes: List[str] = field(default_factory=list)


@dataclass
class DuplicateDependency:
    """Дублирующаяся зависимость"""
    package_name: str
    versions: List[str]
    locations: List[str]  # файлы где найдены
    recommendation: str


@dataclass
class DependencyReport:
    """Отчет об анализе зависимостей"""
    packages: List[PackageInfo] = field(default_factory=list)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    license_issues: List[LicenseInfo] = field(default_factory=list)
    outdated_packages: List[PackageInfo] = field(default_factory=list)
    duplicate_dependencies: List[DuplicateDependency] = field(default_factory=list)
    total_packages: int = 0
    vulnerable_packages: int = 0
    outdated_count: int = 0
    license_conflicts: int = 0
    duplicates_count: int = 0
    recommendations: List[str] = field(default_factory=list)


class DependencyAnalyzer:
    """Анализатор зависимостей"""

    def __init__(self) -> None:
        self.logger = get_logger("DependencyAnalyzer")
        self.compatible_licenses = {
            'MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 
            'ISC', 'Unlicense', 'CC0-1.0', 'WTFPL'
        }
        self.restrictive_licenses = {
            'GPL-2.0', 'GPL-3.0', 'AGPL-3.0', 'LGPL-2.1', 'LGPL-3.0'
        }

    def analyze_requirements(self, requirements_path: Path) -> DependencyReport:
        """
        Анализирует файл requirements.txt
        """
        self.logger.info(f"Анализ зависимостей: {requirements_path}")
        
        if not requirements_path.exists():
            raise FileNotFoundError(f"Файл {requirements_path} не найден")
        
        report = DependencyReport()
        
        try:
            # Парсинг requirements
            packages = self._parse_requirements(requirements_path)
            report.packages = packages
            report.total_packages = len(packages)
            
            # Анализ уязвимостей
            self.logger.info("Проверка уязвимостей")
            vulnerabilities = self._check_vulnerabilities(packages)
            report.vulnerabilities = vulnerabilities
            report.vulnerable_packages = len(set(v.package_name for v in vulnerabilities))
            
            # Анализ лицензий
            self.logger.info("Анализ лицензий")
            license_issues = self._analyze_licenses(packages)
            report.license_issues = license_issues
            report.license_conflicts = len([l for l in license_issues if not l.is_compatible])
            
            # Проверка устаревших пакетов
            self.logger.info("Проверка устаревших пакетов")
            outdated = self._check_outdated_packages(packages)
            report.outdated_packages = outdated
            report.outdated_count = len(outdated)
            
            # Поиск дублирующихся зависимостей
            self.logger.info("Поиск дублирующихся зависимостей")
            duplicates = self._find_duplicate_dependencies(requirements_path)
            report.duplicate_dependencies = duplicates
            report.duplicates_count = len(duplicates)
            
            # Генерация рекомендаций
            report.recommendations = self._generate_recommendations(report)
            
            self.logger.info(f"Анализ зависимостей завершен: {report.total_packages} пакетов, "
                           f"{report.vulnerable_packages} уязвимых, {report.outdated_count} устаревших")
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе зависимостей: {e}")
            raise
        
        return report

    def _parse_requirements(self, requirements_path: Path) -> List[PackageInfo]:
        """Парсит файл requirements.txt"""
        packages = []
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                try:
                    # Парсинг строки requirements
                    req = Requirement(line)
                    package_info = PackageInfo(
                        name=req.name,
                        version=str(req.specifier) if req.specifier else "latest"
                    )
                    packages.append(package_info)
                    
                except Exception as e:
                    self.logger.warning(f"Ошибка парсинга строки {line_num}: {line}",
                                      extra_data={"error": str(e)})
        
        return packages

    def _check_vulnerabilities(self, packages: List[PackageInfo]) -> List[Vulnerability]:
        """Проверяет уязвимости в пакетах"""
        vulnerabilities = []
        
        for package in packages:
            try:
                # Попытка использовать safety (если установлен)
                vulns = self._check_with_safety(package.name, package.version)
                if vulns:
                    vulnerabilities.extend(vulns)
                else:
                    # Fallback: проверка через PyPI API
                    vulns = self._check_with_pypi(package.name, package.version)
                    if vulns:
                        vulnerabilities.extend(vulns)
                        
            except Exception as e:
                self.logger.warning(f"Ошибка проверки уязвимостей для {package.name}: {e}")
        
        return vulnerabilities

    def _check_with_safety(self, package_name: str, version_str: str) -> List[Vulnerability]:
        """Проверка уязвимостей через safety"""
        try:
            result = subprocess.run(
                ['safety', 'check', '--json', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                vulns = []
                
                for vuln in data:
                    if vuln.get('package') == package_name:
                        vulns.append(Vulnerability(
                            package_name=package_name,
                            version=version_str,
                            vulnerability_id=vuln.get('vulnerability_id', ''),
                            severity=vuln.get('severity', 'medium'),
                            description=vuln.get('description', ''),
                            cve_id=vuln.get('cve_id'),
                            affected_versions=vuln.get('affected_versions', ''),
                            fixed_versions=vuln.get('fixed_versions', '')
                        ))
                
                return vulns
                
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        
        return []

    def _check_with_pypi(self, package_name: str, version_str: str) -> List[Vulnerability]:
        """Проверка уязвимостей через PyPI API (fallback)"""
        try:
            # Простая проверка через PyPI API
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Здесь можно добавить логику проверки уязвимостей
                # Пока возвращаем пустой список
                return []
                
        except Exception as e:
            self.logger.debug(f"Ошибка проверки через PyPI: {e}")
        
        return []

    def _analyze_licenses(self, packages: List[PackageInfo]) -> List[LicenseInfo]:
        """Анализирует лицензии пакетов"""
        license_issues = []
        
        for package in packages:
            try:
                license_info = self._get_package_license(package.name)
                if license_info:
                    package.license = license_info.license_type
                    license_issues.append(license_info)
                    
            except Exception as e:
                self.logger.warning(f"Ошибка анализа лицензии для {package.name}: {e}")
        
        return license_issues

    def _get_package_license(self, package_name: str) -> Optional[LicenseInfo]:
        """Получает информацию о лицензии пакета"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                info = data.get('info', {})
                license_type = info.get('license', 'Unknown')
                
                # Проверка совместимости
                is_compatible = self._check_license_compatibility(license_type)
                compatibility_notes = []
                
                if not is_compatible:
                    compatibility_notes.append(f"Лицензия {license_type} может быть несовместима")
                
                return LicenseInfo(
                    package_name=package_name,
                    license_type=license_type,
                    is_compatible=is_compatible,
                    compatibility_notes=compatibility_notes
                )
                
        except Exception as e:
            self.logger.debug(f"Ошибка получения лицензии для {package_name}: {e}")
        
        return None

    def _check_license_compatibility(self, license_type: str) -> bool:
        """Проверяет совместимость лицензии"""
        if not license_type or license_type.lower() == 'unknown':
            return True  # Неизвестная лицензия - считаем совместимой
        
        license_upper = license_type.upper()
        
        # Совместимые лицензии
        if any(compat in license_upper for compat in self.compatible_licenses):
            return True
        
        # Ограничительные лицензии
        if any(restrictive in license_upper for restrictive in self.restrictive_licenses):
            return False
        
        # По умолчанию считаем совместимой
        return True

    def _check_outdated_packages(self, packages: List[PackageInfo]) -> List[PackageInfo]:
        """Проверяет устаревшие пакеты"""
        outdated = []
        
        for package in packages:
            try:
                latest_version = self._get_latest_version(package.name)
                if latest_version and package.version != "latest":
                    current_ver = self._extract_version(package.version)
                    if current_ver and latest_version > current_ver:
                        package.is_outdated = True
                        package.latest_version = str(latest_version)
                        package.update_recommendation = f"Обновить до {latest_version}"
                        outdated.append(package)
                        
            except Exception as e:
                self.logger.warning(f"Ошибка проверки версии для {package.name}: {e}")
        
        return outdated

    def _get_latest_version(self, package_name: str) -> Optional[version.Version]:
        """Получает последнюю версию пакета"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                releases = data.get('releases', {})
                
                if releases:
                    # Получаем последнюю версию
                    latest_ver = max(releases.keys(), key=lambda v: version.parse(v))
                    return version.parse(latest_ver)
                    
        except Exception as e:
            self.logger.debug(f"Ошибка получения версии для {package_name}: {e}")
        
        return None

    def _extract_version(self, version_str: str) -> Optional[version.Version]:
        """Извлекает версию из строки requirements"""
        try:
            # Убираем операторы сравнения
            clean_version = re.sub(r'[<>=!~]+', '', version_str).strip()
            return version.parse(clean_version)
        except Exception:
            return None

    def _find_duplicate_dependencies(self, requirements_path: Path) -> List[DuplicateDependency]:
        """Находит дублирующиеся зависимости"""
        duplicates = []
        package_versions = {}
        
        # Сканируем все файлы requirements в проекте
        requirements_files = list(Path('.').rglob('requirements*.txt'))
        
        for req_file in requirements_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        try:
                            req = Requirement(line)
                            package_name = req.name.lower()
                            
                            if package_name not in package_versions:
                                package_versions[package_name] = {
                                    'versions': set(),
                                    'locations': []
                                }
                            
                            version_str = str(req.specifier) if req.specifier else "latest"
                            package_versions[package_name]['versions'].add(version_str)
                            package_versions[package_name]['locations'].append(str(req_file))
                            
                        except Exception:
                            continue
                            
            except Exception as e:
                self.logger.warning(f"Ошибка чтения {req_file}: {e}")
        
        # Находим дубликаты
        for package_name, info in package_versions.items():
            if len(info['versions']) > 1:
                recommendation = f"Унифицировать версии пакета {package_name}"
                duplicates.append(DuplicateDependency(
                    package_name=package_name,
                    versions=list(info['versions']),
                    locations=info['locations'],
                    recommendation=recommendation
                ))
        
        return duplicates

    def _generate_recommendations(self, report: DependencyReport) -> List[str]:
        """Генерирует рекомендации по улучшению зависимостей"""
        recommendations = []
        
        if report.vulnerable_packages > 0:
            recommendations.append(
                f"🔴 Обнаружено {report.vulnerable_packages} уязвимых пакетов. "
                "Рекомендуется обновить их до безопасных версий."
            )
        
        if report.outdated_count > 0:
            recommendations.append(
                f"🟡 Найдено {report.outdated_count} устаревших пакетов. "
                "Рассмотрите возможность обновления для получения новых функций и исправлений."
            )
        
        if report.license_conflicts > 0:
            recommendations.append(
                f"⚠️ Обнаружено {report.license_conflicts} конфликтов лицензий. "
                "Проверьте совместимость лицензий в вашем проекте."
            )
        
        if report.duplicates_count > 0:
            recommendations.append(
                f"🔄 Найдено {report.duplicates_count} дублирующихся зависимостей. "
                "Унифицируйте версии пакетов в разных файлах requirements."
            )
        
        if not recommendations:
            recommendations.append("✅ Зависимости в хорошем состоянии!")
        
        return recommendations

    def export_report(self, report: DependencyReport, output_path: Path, format: str = 'json') -> None:
        """Экспортирует отчет в различных форматах"""
        try:
            if format.lower() == 'json':
                self._export_json(report, output_path)
            elif format.lower() == 'csv':
                self._export_csv(report, output_path)
            elif format.lower() == 'txt':
                self._export_txt(report, output_path)
            else:
                raise ValueError(f"Неподдерживаемый формат: {format}")
                
            self.logger.info(f"Отчет экспортирован в {output_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта отчета ({format}): {e}")
            raise

    def _export_json(self, report: DependencyReport, output_path: Path) -> None:
        """Экспорт в JSON"""
        data = {
            'summary': {
                'total_packages': report.total_packages,
                'vulnerable_packages': report.vulnerable_packages,
                'outdated_count': report.outdated_count,
                'license_conflicts': report.license_conflicts,
                'duplicates_count': report.duplicates_count
            },
            'packages': [
                {
                    'name': p.name,
                    'version': p.version,
                    'license': p.license,
                    'is_outdated': p.is_outdated,
                    'latest_version': p.latest_version
                } for p in report.packages
            ],
            'vulnerabilities': [
                {
                    'package_name': v.package_name,
                    'severity': v.severity,
                    'description': v.description,
                    'cve_id': v.cve_id
                } for v in report.vulnerabilities
            ],
            'recommendations': report.recommendations
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, report: DependencyReport, output_path: Path) -> None:
        """Экспорт в CSV"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Заголовки
            writer.writerow(['Package', 'Version', 'License', 'Outdated', 'Latest Version', 'Vulnerabilities'])
            
            # Данные
            for package in report.packages:
                vulns = [v for v in report.vulnerabilities if v.package_name == package.name]
                vuln_count = len(vulns)
                
                writer.writerow([
                    package.name,
                    package.version,
                    package.license or 'Unknown',
                    'Yes' if package.is_outdated else 'No',
                    package.latest_version or 'N/A',
                    vuln_count
                ])

    def _export_txt(self, report: DependencyReport, output_path: Path) -> None:
        """Экспорт в TXT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ ОБ АНАЛИЗЕ ЗАВИСИМОСТЕЙ\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Всего пакетов: {report.total_packages}\n")
            f.write(f"Уязвимых пакетов: {report.vulnerable_packages}\n")
            f.write(f"Устаревших пакетов: {report.outdated_count}\n")
            f.write(f"Конфликтов лицензий: {report.license_conflicts}\n")
            f.write(f"Дублирующихся зависимостей: {report.duplicates_count}\n\n")
            
            if report.vulnerabilities:
                f.write("УЯЗВИМОСТИ:\n")
                f.write("-" * 20 + "\n")
                for vuln in report.vulnerabilities:
                    f.write(f"• {vuln.package_name} ({vuln.severity}): {vuln.description}\n")
                f.write("\n")
            
            if report.recommendations:
                f.write("РЕКОМЕНДАЦИИ:\n")
                f.write("-" * 20 + "\n")
                for rec in report.recommendations:
                    f.write(f"• {rec}\n")
