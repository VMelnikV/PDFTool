#!/usr/bin/env python3
# Інтеграційні тести GUI для PDF Tool

import sys
import unittest

from PySide6.QtWidgets import QApplication, QTabWidget

from src.app.pdf_tool import PDFTool


class TestPDFToolGUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = PDFTool()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def test_window_title(self):
        """Заголовок вікна непорожній і містить назву застосунку."""
        title = self.window.windowTitle()
        self.assertTrue(title and title.strip(), "Заголовок вікна порожній")
        self.assertIn("PDF Tool", title)

    def test_tabs_count(self):
        """У вікні є QTabWidget із 6 вкладками (Convert, Merge, Split,
        Forms, Compress, All-in-One)."""
        tab_widget = self.window.findChild(QTabWidget)
        self.assertIsNotNone(tab_widget, "QTabWidget не знайдено у вікні")
        self.assertEqual(
            tab_widget.count(),
            6,
            f"Очікувалось 6 вкладок, отримано {tab_widget.count()}: "
            f"{[tab_widget.tabText(i) for i in range(tab_widget.count())]}",
        )

    def test_tabs_have_titles(self):
        """Кожна вкладка має непорожній заголовок."""
        tab_widget = self.window.findChild(QTabWidget)
        self.assertIsNotNone(tab_widget)
        for i in range(tab_widget.count()):
            title = tab_widget.tabText(i)
            self.assertTrue(
                title and title.strip(),
                f"Вкладка #{i} має порожній заголовок",
            )


if __name__ == '__main__':
    unittest.main()
