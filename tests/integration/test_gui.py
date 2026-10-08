#!/usr/bin/env python3
# Інтеграційні тести GUI

import unittest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.app.pdf_tool import PDFTool

class TestPDFToolGUI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        self.window = PDFTool()
        self.window.show()
    
    def test_window_title(self):
        self.assertIn('PDF', self.window.windowTitle())
    
    def test_tabs_count(self):
        tab_widget = self.window.findChild(QTabWidget)
        self.assertEqual(tab_widget.count(), 5)  # 5 вкладок

if __name__ == '__main__':
    unittest.main()
