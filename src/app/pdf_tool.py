# pdf_tool.py
import os
import sys

# Якщо запущено як PyInstaller onefile — додаємо _MEIPASS
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)

# Додаємо шлях до src для common
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from common.i18n.translator import translator

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from tabs.convert_tab import ConvertTab
from tabs.merge_tab import MergeTab
from tabs.split_tab import SplitTab
from tabs.forms_tab import FormsTab
from tabs.compress_tab import CompressTab
from tabs.all_in_one_tab import AllInOneTab


class PDFTool(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(translator.tr('app_title', 'common'))
        self.setMinimumSize(800, 600)
        
        self._set_window_icon()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        
        self.convert_tab = ConvertTab()
        self.merge_tab = MergeTab()
        self.split_tab = SplitTab()
        self.forms_tab = FormsTab()
        self.compress_tab = CompressTab()
        self.all_in_one_tab = AllInOneTab()
        
        self.tabs.addTab(self.convert_tab, translator.tr('tab_convert', 'tabs'))
        self.tabs.addTab(self.merge_tab, translator.tr('tab_merge', 'tabs'))
        self.tabs.addTab(self.split_tab, translator.tr('tab_split', 'tabs'))
        self.tabs.addTab(self.forms_tab, translator.tr('tab_forms', 'tabs'))
        self.tabs.addTab(self.compress_tab, translator.tr('tab_compress', 'tabs'))
        self.tabs.addTab(self.all_in_one_tab, translator.tr('tab_all_in_one', 'tabs'))
        
        layout.addWidget(self.tabs)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(translator.tr('status_ready'), 5000)
        
        self.connect_status_signals()
    
    def _set_window_icon(self):
        """Встановлює іконку вікна"""
        possible_paths = []
        
        # 1. Якщо запущено як PyInstaller onefile
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            possible_paths.append(os.path.join(sys._MEIPASS, 'pdf_icon.png'))
            possible_paths.append(os.path.join(sys._MEIPASS, 'resources', 'icons', 'pdf_icon.png'))
            possible_paths.append(os.path.join(sys._MEIPASS, 'common', 'resources', 'icons', 'pdf_icon.png'))
        
        # 2. Якщо запущено як AppImage
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            possible_paths.append(os.path.join(base_path, 'pdf_icon.png'))
            possible_paths.append(os.path.join(base_path, 'resources', 'icons', 'pdf_icon.png'))
            possible_paths.append(os.path.join(base_path, '..', 'share', 'icons', 'hicolor', '256x256', 'apps', 'pdf-tool.png'))
            possible_paths.append(os.path.join(base_path, '..', '..', 'share', 'icons', 'hicolor', '256x256', 'apps', 'pdf-tool.png'))
        
        # 3. Звичайний запуск з коду
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.append(os.path.join(current_dir, '..', 'common', 'resources', 'icons', 'pdf_icon.png'))
        possible_paths.append(os.path.join(current_dir, 'pdf_icon.png'))
        
        # Шукаємо іконку
        for path in possible_paths:
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                return
    
    def connect_status_signals(self):
        """Підключаємо сигнали для оновлення статусу"""
        for tab in [self.convert_tab, self.merge_tab, self.split_tab, 
                   self.forms_tab, self.compress_tab, self.all_in_one_tab]:
            if hasattr(tab, 'status_signal'):
                tab.status_signal.connect(self.update_status)
    
    def update_status(self, message):
        """Оновлює статусну стрічку"""
        self.statusBar.showMessage(message, 5000)
    
    def change_language(self, locale):
        """Змінює мову інтерфейсу"""
        if translator.set_language(locale):
            self.setWindowTitle(translator.tr('app_title', 'common'))
            
            self.tabs.setTabText(0, translator.tr('tab_convert', 'tabs'))
            self.tabs.setTabText(1, translator.tr('tab_merge', 'tabs'))
            self.tabs.setTabText(2, translator.tr('tab_split', 'tabs'))
            self.tabs.setTabText(3, translator.tr('tab_forms', 'tabs'))
            self.tabs.setTabText(4, translator.tr('tab_compress', 'tabs'))
            self.tabs.setTabText(5, translator.tr('tab_all_in_one', 'tabs'))
            
            self.statusBar.showMessage(translator.tr('status_ready'), 5000)
            
            for tab in [self.convert_tab, self.merge_tab, self.split_tab, 
                       self.forms_tab, self.compress_tab, self.all_in_one_tab]:
                if hasattr(tab, 'retranslate_ui'):
                    tab.retranslate_ui()
            
            return True
        return False
