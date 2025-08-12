# Руководство по безопасности - Python Import Parser

## Обзор

Модуль безопасности обеспечивает комплексную защиту приложения от различных угроз при сканировании Python файлов. Реализованы механизмы валидации, санитизации и мониторинга ресурсов.

## Архитектура безопасности

### Основные компоненты

1. **SecurityConfig** - Конфигурация параметров безопасности
2. **SecurityValidator** - Валидатор файлов и содержимого
3. **SecurityManager** - Менеджер безопасности (фасад)

### Принципы безопасности

- **Defense in Depth** - Многоуровневая защита
- **Fail Secure** - Отказ в безопасном состоянии
- **Principle of Least Privilege** - Минимальные привилегии
- **Input Validation** - Валидация всех входных данных

## Конфигурация безопасности

### Параметры файлов

```python
max_file_size: int = 50 * 1024 * 1024  # 50MB
max_files_per_scan: int = 10000
max_total_size: int = 1024 * 1024 * 1024  # 1GB
```

### Параметры содержимого

```python
max_line_length: int = 10000
max_imports_per_file: int = 1000
max_ast_nodes: int = 100000
```

### Параметры путей

```python
max_path_length: int = 4096
allowed_extensions: Set[str] = {'.py', '.pyw', '.pyx', '.pxd'}
blocked_patterns: Set[str] = {'__pycache__', '.git', 'venv', ...}
safe_directories: Set[str] = set()
```

### Параметры ресурсов

```python
max_scan_duration: int = 3600  # 1 час
max_memory_usage: int = 1024 * 1024 * 1024  # 1GB
max_threads: int = 8
```

### Параметры валидации

```python
check_for_malicious_patterns: bool = True
validate_imports: bool = True
sanitize_content: bool = True
```

## Валидация путей

### Защита от Path Traversal

Система обнаруживает и блокирует попытки path traversal:

```python
# Блокируемые паттерны
'..', '../', '..\\', '..%2f', '..%5c',
'%2e%2e', '%2e%2e%2f', '%2e%2e%5c'
```

### Валидация расширений

Разрешены только безопасные расширения Python файлов:
- `.py` - Стандартные Python файлы
- `.pyw` - Python файлы для Windows
- `.pyx` - Cython файлы
- `.pxd` - Cython заголовочные файлы

### Блокировка директорий

Автоматически блокируются системные и временные директории:
- `__pycache__` - Кэш Python
- `.git`, `.svn`, `.hg` - Системы контроля версий
- `venv`, `.venv`, `env` - Виртуальные окружения
- `node_modules` - Зависимости Node.js
- `build`, `dist` - Директории сборки
- `.pytest_cache`, `.coverage` - Кэш тестов
- `.tox`, `.mypy_cache` - Инструменты разработки

## Валидация содержимого

### Обнаружение злонамеренных паттернов

Система проверяет наличие опасных конструкций:

```python
# Блокируемые паттерны
r'eval\s*\('           # Выполнение кода
r'exec\s*\('           # Выполнение кода
r'__import__\s*\('     # Динамический импорт
r'compile\s*\('        # Компиляция кода
r'input\s*\('          # Ввод пользователя
r'raw_input\s*\('      # Ввод пользователя (Python 2)
r'os\.system\s*\('     # Системные команды
r'subprocess\..*\('    # Подпроцессы
r'open\s*\(.*[\'"]w[\'"]'  # Запись файлов
r'file\s*\(.*[\'"]w[\'"]'  # Запись файлов (Python 2)
```

### Валидация импортов

Проверка подозрительных модулей:

```python
suspicious_imports = {
    'pickle', 'marshal', 'shelve', 'dill', 'cloudpickle',  # Сериализация
    'subprocess', 'os', 'sys', 'ctypes', 'mmap',           # Системные
    'socket', 'urllib', 'requests', 'ftplib', 'smtplib',   # Сеть
    'telnetlib', 'poplib', 'imaplib', 'nntplib'           # Протоколы
}
```

### Валидация имен импортов

- Проверка на валидный Python идентификатор
- Проверка на зарезервированные слова
- Ограничение длины имени (100 символов)

## Санитизация содержимого

### Очистка от опасных символов

```python
# Удаление null-байтов
content = content.replace('\x00', '')

# Удаление управляющих символов
content = ''.join(char for char in content 
                if char.isprintable() or char in '\t\n\r')

# Нормализация окончаний строк
content = content.replace('\r\n', '\n').replace('\r', '\n')

# Удаление лишних пробелов
lines = [line.rstrip() for line in lines]
```

## Мониторинг ресурсов

### Ограничения времени

- Максимальное время сканирования: 1 час
- Отслеживание времени выполнения

### Ограничения памяти

- Максимальное использование памяти: 1GB
- Мониторинг через psutil (опционально)

### Ограничения файлов

- Максимальный размер файла: 50MB
- Максимальное количество файлов: 10,000
- Общий размер всех файлов: 1GB

## Интеграция с приложением

### ScanService

```python
# Инициализация безопасности
security_config_dict = self.config.get_security_config()
security_config = SecurityConfig(**security_config_dict)
self.security_manager = SecurityManager(security_config)

# Валидация запроса на сканирование
is_valid, message = self.security_manager.validate_scan_request(directory)
if not is_valid:
    raise ValueError(f"Ошибка валидации безопасности: {message}")
```

### FileScanner

```python
# Валидация файла
is_valid, message = self.security_manager.validate_file(file_path)
if not is_valid:
    return []

# Валидация и санитизация содержимого
is_valid, message, sanitized_content = self.security_manager.validate_and_sanitize_content(content, file_path)
if not is_valid:
    return []

# Валидация импортов
is_valid, message = self.security_manager.validate_imports(imports, file_path)
if not is_valid:
    return []
```

### ImportParser

```python
# Проверка лимитов AST
if len(content) > self.security_manager.config.max_ast_nodes:
    return []

# Ограничение количества узлов AST
node_count = 0
for node in ast.walk(tree):
    node_count += 1
    if node_count > self.security_manager.config.max_ast_nodes:
        break
```

## Логирование безопасности

### Уровни логирования

- **INFO** - Начало сканирования, успешная валидация
- **WARNING** - Подозрительные паттерны, превышение лимитов
- **ERROR** - Ошибки валидации, блокировка файлов

### Контекстная информация

```python
self.logger.warning("Обнаружен подозрительный паттерн", 
                  extra_data={
                      "file": str(file_path),
                      "pattern": pattern.pattern
                  })
```

## Отчеты о безопасности

### Структура отчета

```python
{
    "files_processed": 0,
    "total_size_processed": 0,
    "scan_duration": 0.0,
    "file_hashes_count": 0,
    "security_config": {
        "max_file_size": 52428800,
        "max_files_per_scan": 10000,
        "max_total_size": 1073741824,
        "check_for_malicious_patterns": True,
        "validate_imports": True,
        "sanitize_content": True
    }
}
```

## Хеширование файлов

### MD5 хеши

- Кэширование хешей для производительности
- Проверка целостности файлов
- Отслеживание изменений

```python
file_hash = self.manager.get_file_hash(file_path)
```

## Настройка конфигурации

### Через config.json

```json
{
  "security": {
    "max_file_size": 10485760,
    "max_files_per_scan": 5000,
    "max_total_size": 536870912,
    "check_for_malicious_patterns": true,
    "validate_imports": true,
    "sanitize_content": true,
    "allowed_extensions": [".py", ".pyw"],
    "blocked_patterns": ["__pycache__", ".git"],
    "safe_directories": ["/safe/path"]
  }
}
```

### Программно

```python
config.update_security_config("max_file_size", 1024 * 1024)
config.update_security_config("check_for_malicious_patterns", False)
```

## Тестирование безопасности

### Запуск тестов

```bash
python -m pytest tests/test_security.py -v
```

### Покрытие тестов

- Валидация путей (path traversal, расширения, паттерны)
- Валидация размеров файлов
- Валидация содержимого (злонамеренные паттерны)
- Валидация импортов (подозрительные модули)
- Санитизация содержимого
- Мониторинг ресурсов
- Интеграционные тесты

## Рекомендации по безопасности

### Настройка для продакшена

1. **Ограничьте безопасные директории**
   ```python
   "safe_directories": ["/app/projects", "/home/user/code"]
   ```

2. **Уменьшите лимиты файлов**
   ```python
   "max_file_size": 10 * 1024 * 1024,  # 10MB
   "max_files_per_scan": 1000
   ```

3. **Включите все проверки**
   ```python
   "check_for_malicious_patterns": true,
   "validate_imports": true,
   "sanitize_content": true
   ```

4. **Мониторинг логов**
   - Регулярно проверяйте логи безопасности
   - Настройте алерты на подозрительную активность

### Мониторинг производительности

1. **Отслеживание времени сканирования**
2. **Мониторинг использования памяти**
3. **Анализ заблокированных файлов**
4. **Статистика валидации**

## Обработка ошибок

### Типы ошибок безопасности

1. **PathTraversalError** - Попытка обхода директорий
2. **MaliciousContentError** - Обнаружен злонамеренный код
3. **ResourceLimitError** - Превышены лимиты ресурсов
4. **ValidationError** - Ошибка валидации

### Стратегии обработки

- **Fail Fast** - Немедленная остановка при обнаружении угрозы
- **Logging** - Подробное логирование всех инцидентов
- **Graceful Degradation** - Продолжение работы с исключением проблемных файлов

## Заключение

Модуль безопасности обеспечивает комплексную защиту от различных угроз при сканировании Python файлов. Реализованы механизмы валидации, санитизации и мониторинга, которые можно настроить под конкретные требования безопасности.
