# py-import-scanner

## Description

**py-import-scanner** is a tool designed to scan Python scripts for imported libraries. It allows you to analyze your code and identify all the imported libraries while excluding standard libraries like `os`, `sys`, and others.

The program provides functionality for visualizing the data in the form of histograms and pie charts, showing the count of different imported libraries and their usage in the project. This allows developers to see which libraries they actively use and improve dependency management.

## Features

- Scans Python scripts in the specified directory.
- Excludes standard libraries and packages listed in `.gitignore`.
- Generates statistics on imports.
- Displays histograms and pie charts using `matplotlib`.
- Option to copy statistics to the clipboard.

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

1. **Run the program:**

   To run the program, simply execute the file:

   ```bash
   python main.py
   ```

   This will open the graphical interface where you can select a directory to scan. Choose a directory, and the program will begin processing the files.

2. **Graphical Interface:**

   The program uses the `Tkinter` library for the graphical interface. You will be able to see:
   - Buttons to select the folder.
   - Statistics on the imports.
   - A histogram and pie chart displaying the frequency of library usage.

3. **Keyboard shortcuts:**

   - The **"Select Folder"** button allows you to choose the folder for scanning.
   - The **"Histogram"** and **"Pie Chart"** buttons display the statistics visualization.
   - The statistics can be copied to the clipboard for further use.

## Project Structure

- **main.py** — main script to run the program.
- **scanner.py** — contains the logic for scanning files.
- **requirements.txt** — dependencies file for the project.
- **README.md** — this file with documentation.
- **assets/** — directory for possible resources (icons, images, etc.).

## Notes

- This project uses libraries for visualization, such as `matplotlib` and `pyperclip`.
- If you encounter errors or issues with dependencies, you can install them manually using:

  ```bash
  pip install matplotlib pyperclip colorama
  ```

## License

This project is licensed under the MIT License. For more details, see the `LICENSE` file.
