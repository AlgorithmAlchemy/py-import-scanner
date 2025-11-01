[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt%206-blueviolet)](https://pypi.org/project/PySide6/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8+-orange)](https://matplotlib.org/stable/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-critical)]()

#

<div align="center">
  <a href="README.md" style="text-decoration: none;">
    <button style="background: linear-gradient(45deg, #2196F3, #1976D2); color: white; padding: 12px 24px; text-align: center; display: inline-block; font-size: 16px; margin: 8px 4px; cursor: pointer; border: none; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: all 0.3s ease;">
      <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Flag_of_Russia.svg/32px-Flag_of_Russia.svg.png" alt="Russian" style="vertical-align: middle; padding-right: 8px;" />
      📖 Русский README
    </button>
  </a>
</div>

# py-import-scanner

## Description

**py-import-scanner** is a tool designed to scan Python scripts for imported libraries. It allows you to analyze your code and identify all the imported libraries while excluding standard libraries like `os`, `sys`, and others.

The program provides functionality for visualizing the data in the form of histograms and pie charts, showing the count of different imported libraries and their usage in the project. This allows developers to see which libraries they actively use and improve dependency management.

**Program provides**:
<img src="data/ezgif.com-animated-gif-maker.gif" style="width: 80%;" />

## Operating principle
<img src="https://github.com/user-attachments/assets/2a8bd464-d3ed-41d0-88bc-ce51682ba76e" style="width: 50%;" />

## Features

- Scans Python scripts in the specified directory.
- Excludes standard libraries and packages listed in `.gitignore`.
- Generates statistics on imports.
- Displays histograms and pie charts using `matplotlib`.
- Option to copy statistics to the clipboard.
-  **Multi-language support**: English and Russian interface localization.

## Installation

1. **Clone the repository:**

   In the command line or PowerShell, run:

   ```bash
   git clone https://github.com/AlgorithmAlchemy/py-import-scanner.git
   cd py-import-scanner
   ```

2. **Install dependencies:**

   Make sure you have Python 3.7 or higher, and then install all the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

**Run the program:**

   To run the program, simply execute the file:

   ```bash
   python main.py
   ```

   This will open the graphical interface where you can select a directory to scan. Choose a directory, and the program will begin processing the files.

**Graphical Interface:**

   The program uses the `PySide6` library for the modern graphical interface. You will be able to see:
   - Buttons to select the folder
   - Statistics on the imports
   - A histogram and pie chart displaying the frequency of library usage
   -  Language selection option for interface localization

**Interface Features:**

   - The **"Select Folder"** button allows you to choose the folder for scanning
   - The **"Histogram"** and **"Pie Chart"** buttons display the statistics visualization
   - The statistics can be copied to the clipboard for further use
   - Language switcher for English and Russian interface

## Project Structure

- **main.py** — main script to run the program
- **gui/** — directory containing GUI components
  - **main_window.py** — main window interface
  - **stats_window.py** — statistics window
  - **chart_windows.py** — chart visualization windows
- **utils.py** — utility functions
- **requirements.txt** — dependencies file for the project
- **README.md** — Russian documentation
- **README_en.md** — English documentation
- **data/** — directory for resources (icons, images, etc.)

## Notes

- This project uses libraries for visualization, such as `matplotlib` and `pyperclip`
- The GUI is built with PySide6 for modern cross-platform compatibility
- If you encounter errors or issues with dependencies, you can install them manually using:

  ```bash
  pip install matplotlib pyperclip colorama PySide6
  ```

## License

This project is licensed under the MIT License. For more details, see the `LICENSE` file.
