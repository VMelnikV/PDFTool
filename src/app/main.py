#!/usr/bin/env python3
"""Точка входу PDF Tool.

Створює (або переюзує) QApplication, встановлює іконку і показує головне вікно.

Якщо QApplication вже існує (наприклад, його створило вікно перевірки
залежностей при старті) — використовуємо його, а не створюємо нове.
Це критично: у одного процесу може бути тільки один QApplication.
"""

import sys
import os

# PyInstaller onefile
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)

# Шлях до поточної папки (src/app)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Шлях до src для common
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pdf_tool import PDFTool


def get_icon_path():
    """Повертає шлях до іконки"""
    # 1. PyInstaller onefile
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, 'pdf_icon.png')
        if os.path.exists(path):
            return path

    # 2. AppImage
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        path = os.path.join(base_path, 'pdf_icon.png')
        if os.path.exists(path):
            return path
        path = os.path.join(
            base_path, '..', 'share', 'icons', 'hicolor',
            '256x256', 'apps', 'pdf-tool.png',
        )
        if os.path.exists(path):
            return path

    # 3. Запуск з коду
    path = os.path.join(
        src_dir, 'common', 'resources', 'icons', 'pdf_icon.png'
    )
    if os.path.exists(path):
        return path

    return None


def main():
    """Головна функція запуску програми"""
    # Ключове: переюзуємо існуючий QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("PDF Tool")

    # Іконка для всього застосунку
    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    window = PDFTool()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
