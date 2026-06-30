#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pdf_tool import PDFTool

def main():
    app = QApplication(sys.argv)
    
    # Встановлюємо іконку для всього застосунку
    app.setWindowIcon(QIcon("pdf_icon.png"))
    
    window = PDFTool()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
