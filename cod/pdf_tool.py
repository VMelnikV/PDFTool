from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap

from tabs.convert_tab import ConvertTab
from tabs.merge_tab import MergeTab
from tabs.split_tab import SplitTab
from tabs.forms_tab import FormsTab
from tabs.compress_tab import CompressTab

class PDFTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tool - Універсальний редактор PDF")
        self.setMinimumSize(800, 600)
        
        # Встановлюємо іконку
        #self.setWindowIcon(QIcon("pdf_icon.png"))
        
        # Центральний віджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Головний layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Створюємо вкладки
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        
        # Додаємо вкладки
        self.convert_tab = ConvertTab()
        self.merge_tab = MergeTab()
        self.split_tab = SplitTab()
        self.forms_tab = FormsTab()
        self.compress_tab = CompressTab()
        
        self.tabs.addTab(self.convert_tab, "🖼️ Конвертація")
        self.tabs.addTab(self.merge_tab, "📄 Об'єднання")
        self.tabs.addTab(self.split_tab, "✂️ Розділення")
        self.tabs.addTab(self.forms_tab, "✍️ Форми")
        self.tabs.addTab(self.compress_tab, "📦 Стиснення")
        
        layout.addWidget(self.tabs)
        
        # Статусна стрічка
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готово до роботи", 5000)
        
        # Підключаємо сигнали для статусу
        self.connect_status_signals()
    
    def connect_status_signals(self):
        """Підключаємо сигнали для оновлення статусу"""
        # Кожна вкладка має сигнал для оновлення статусу
        for tab in [self.convert_tab, self.merge_tab, self.split_tab, 
                   self.forms_tab, self.compress_tab]:
            if hasattr(tab, 'status_signal'):
                tab.status_signal.connect(self.update_status)
    
    def update_status(self, message):
        """Оновлює статусну стрічку"""
        self.statusBar.showMessage(message, 5000)
