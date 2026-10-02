# main.py
import sys
import os

# Якщо запущено як PyInstaller onefile
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pdf_tool import PDFTool

def main():
    app = QApplication(sys.argv)
    
    # Іконка
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'pdf_icon.png')
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, '..', 'common', 'resources', 'icons', 'pdf_icon.png')
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = PDFTool()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
