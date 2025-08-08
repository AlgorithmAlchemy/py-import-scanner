## 🔄 Последнее обновление — v2.2.0

> 📅 Дата релиза: 2025-08-08

- ⚡ Ультра-быстрая оптимизация производительности:📈 Графики по времени создания проектов
- 🚀 Технические оптимизации
- 📊 Улучшения интерфейса, модернизация на PySide6
- 🔧 Архитектурные улучшения
- 📊 Улучшенная визуализация данных
- ➡ Посмотреть полный [Changelog](CHANGELOG.md)


#


<a href="https://github.com/AlgorithmAlchemy/py-import-scanner/blob/main/README_en.md" style="text-decoration: none;">
    <button style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border: none;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Flag_of_England.svg/32px-Flag_of_England.svg.png" alt="English" style="vertical-align: middle; padding-right: 8px;" />
         ENG READMY
    </button>
</a>

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

## Установка

1. **Клонируйте репозиторий:**

   В командной строке или PowerShell выполните:

   ```bash
   git clone https://github.com/AlgorithmAlchemy/py-import-scanner.git
   cd py-import-scanner
   ```

2. **Установите зависимости:**

   Убедитесь, что у вас установлен Python 3.10 или выше, затем установите все зависимости:

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

