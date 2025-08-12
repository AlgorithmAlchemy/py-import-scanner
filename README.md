[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt%206-blueviolet)](https://pypi.org/project/PySide6/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8+-orange)](https://matplotlib.org/stable/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-critical)]()
## 🔄 Последнее обновление — v2.3.0

> 📅 Дата релиза: 2025-01-27

- 🌍 **Новая функция**: Английская локализация в графическом интерфейсе
- ⚡ Ультра-быстрая оптимизация производительности
- 📈 Графики по времени создания проектов
- 🚀 Технические оптимизации
- 📊 Улучшения интерфейса, модернизация на PySide6
- 🔧 Архитектурные улучшения
- 📊 Улучшенная визуализация данных
- ➡ Посмотреть полный [Changelog](CHANGELOG.md)


#

<div align="center">
  <a href="README_en.md" style="text-decoration: none;">
    <button style="background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 12px 24px; text-align: center; display: inline-block; font-size: 16px; margin: 8px 4px; cursor: pointer; border: none; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: all 0.3s ease;">
      <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Flag_of_England.svg/32px-Flag_of_England.svg.png" alt="English" style="vertical-align: middle; padding-right: 8px;" />
      📖 English README
    </button>
  </a>
</div>

**Program provides**:
<img src="data/ezgif.com-animated-gif-maker.gif" style="width: 80%;" />


# py-import-scanner

## Описание

**py-import-scanner** — это инструмент для сканирования Python-скриптов на предмет импортируемых библиотек. Он позволяет анализировать код и выявлять все использованные импорты, исключая стандартные библиотеки, такие как `os`, `sys` и другие.

Программа предоставляет функциональность для визуализации данных в виде гистограмм и круговых диаграмм, отображая количество различных импортируемых библиотек и их использование в проекте. Это позволяет разработчикам увидеть, какие библиотеки они активно используют, а также улучшить управление зависимостями.

## Принцип работы
<img src="https://github.com/user-attachments/assets/2a8bd464-d3ed-41d0-88bc-ce51682ba76e" style="width: 50%;" />

## Функциональность

- Сканирует Python-скрипты в указанной директории.
- Игнорирует стандартные библиотеки и пакеты, перечисленные в `.gitignore`.
- Генерирует статистику по импортам.
- Отображает гистограммы и круговые диаграммы с использованием `matplotlib`.
- Возможность копировать статистику в буфер обмена.
- 🌍 **Многоязычная поддержка**: Английская и русская локализация интерфейса.

## Установка

1. **Клонируйте репозиторий:**

   В командной строке или PowerShell выполните:

   ```bash
   git clone https://github.com/AlgorithmAlchemy/py-import-scanner.git
   cd py-import-scanner
   ```

2. **Установите зависимости:**

   Убедитесь, что у вас установлен Python 3.7 или выше, затем установите все зависимости:

   ```bash
   pip install -r requirements.txt
   ```

## Использование

**Запуск программы:**

   Для запуска программы просто выполните файл:

   ```bash
   python main.py
   ```

   Это откроет графический интерфейс, где вы сможете выбрать директорию для сканирования. Выберите директорию, и программа начнёт обработку файлов.


## Примечания

- Этот проект использует библиотеки для визуализации, такие как `matplotlib` и `pyperclip`.
- В случае ошибок или проблем с зависимостями попробуйте установить их вручную с помощью команды:

  ```bash
  pip install matplotlib pyperclip colorama
  ```

