"""Головне вікно PDF Tool.

Містить QTabWidget з 7 вкладками:
  1. Convert
  2. Merge
  3. Split
  4. Forms
  5. Compress
  6. AllInOne
  7. Settings (⚙️)

А також меню «Довідка → Перевірити залежності», яке відкриває
QtDependencyWindow модально.
"""

import os
import sys

# PyInstaller onefile
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)

# Шлях до src для common
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from common.i18n.translator import translator

from common.version import __version__

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction, QKeySequence

from tabs.convert_tab import ConvertTab
from tabs.merge_tab import MergeTab
from tabs.split_tab import SplitTab
from tabs.forms_tab import FormsTab
from tabs.compress_tab import CompressTab
from tabs.all_in_one_tab import AllInOneTab
from tabs.settings_tab import SettingsTab


class PDFTool(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(translator.tr('app_title', 'common'))
        self.setMinimumSize(800, 600)

        self._set_window_icon()
        self._setup_menu_bar()

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
        self.settings_tab = SettingsTab(self)

        self.tabs.addTab(self.convert_tab, translator.tr('tab_convert', 'tabs'))
        self.tabs.addTab(self.merge_tab, translator.tr('tab_merge', 'tabs'))
        self.tabs.addTab(self.split_tab, translator.tr('tab_split', 'tabs'))
        self.tabs.addTab(self.forms_tab, translator.tr('tab_forms', 'tabs'))
        self.tabs.addTab(self.compress_tab, translator.tr('tab_compress', 'tabs'))
        self.tabs.addTab(self.all_in_one_tab, translator.tr('tab_all_in_one', 'tabs'))
        self.tabs.addTab(self.settings_tab, translator.tr('tab_settings', 'tabs'))

        layout.addWidget(self.tabs)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(translator.tr('status_ready'), 5000)

        self.connect_status_signals()

    # ────────────────────────────────────────────────────────
    # Меню
    # ────────────────────────────────────────────────────────

    def _setup_menu_bar(self) -> None:
        """Створює меню «Довідка → Перевірити залежності»."""
        menubar = self.menuBar()

        help_menu = menubar.addMenu(translator.tr('menu_help', 'ui'))

        self.action_check_deps = QAction(
            translator.tr('menu_check_dependencies', 'ui'), self
        )
        self.action_check_deps.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.action_check_deps.triggered.connect(self._on_check_dependencies)
        help_menu.addAction(self.action_check_deps)

        help_menu.addSeparator()

        self.action_about = QAction(
            translator.tr('menu_about', 'ui'), self
        )
        self.action_about.triggered.connect(self._on_about)
        help_menu.addAction(self.action_about)

    def _on_check_dependencies(self) -> None:
        """Відкриває вікно перевірки залежностей (модально)."""
        try:
            from common.deps.env import detect_env
            from common.deps.report import run_all_checks
            from common.deps.ui.qt_window import QtDependencyWindow

            env = detect_env()
            report = run_all_checks(env)
            window = QtDependencyWindow(report)

            # Тримаємо посилання, щоб GC не зібрав
            self._dep_window = window
            window.run()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                translator.tr("msg_check_window_error_title", "deps_ui"),
                translator.trf(
                    "msg_check_window_error", "deps_ui",
                    error=f"{type(exc).__name__}: {exc}",
                ),
            )
        finally:
            self._dep_window = None

    def _on_about(self) -> None:
        """Про програму."""
        text = translator.tr('about_text', 'dialogs')
        version_label = translator.tr('label_version', 'settings')
        text = f"{text}\n\n{version_label} {__version__}"
        QMessageBox.about(
            self,
            translator.tr('about_title', 'dialogs'),
            text,
        )

    # ────────────────────────────────────────────────────────
    # Іконка / сигнали / мова
    # ────────────────────────────────────────────────────────

    def _set_window_icon(self):
        """Встановлює іконку вікна"""
        possible_paths = []

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            possible_paths.append(os.path.join(sys._MEIPASS, 'pdf_icon.png'))
            possible_paths.append(os.path.join(
                sys._MEIPASS, 'resources', 'icons', 'pdf_icon.png'
            ))
            possible_paths.append(os.path.join(
                sys._MEIPASS, 'common', 'resources', 'icons', 'pdf_icon.png'
            ))

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            possible_paths.append(os.path.join(base_path, 'pdf_icon.png'))
            possible_paths.append(os.path.join(
                base_path, '..', 'share', 'icons', 'hicolor',
                '256x256', 'apps', 'pdf-tool.png',
            ))

        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.append(os.path.join(
            current_dir, '..', 'common', 'resources', 'icons', 'pdf_icon.png'
        ))
        possible_paths.append(os.path.join(current_dir, 'pdf_icon.png'))

        for path in possible_paths:
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                return

    def connect_status_signals(self):
        """Підключаємо сигнали для оновлення статусу"""
        for tab in [
            self.convert_tab, self.merge_tab, self.split_tab,
            self.forms_tab, self.compress_tab, self.all_in_one_tab,
            self.settings_tab,
        ]:
            if hasattr(tab, 'status_signal'):
                tab.status_signal.connect(self.update_status)

    def update_status(self, message):
        """Оновлює статусну стрічку"""
        self.statusBar.showMessage(message, 5000)

    def change_language(self, locale):
        """Змінює мову інтерфейсу"""
        if translator.set_language(locale):
            self.setWindowTitle(translator.tr('app_title', 'common'))

            # Меню
            self.action_check_deps.setText(
                translator.tr('menu_check_dependencies', 'ui')
            )
            self.action_about.setText(
                translator.tr('menu_about', 'ui')
            )

            # Вкладки
            self.tabs.setTabText(0, translator.tr('tab_convert', 'tabs'))
            self.tabs.setTabText(1, translator.tr('tab_merge', 'tabs'))
            self.tabs.setTabText(2, translator.tr('tab_split', 'tabs'))
            self.tabs.setTabText(3, translator.tr('tab_forms', 'tabs'))
            self.tabs.setTabText(4, translator.tr('tab_compress', 'tabs'))
            self.tabs.setTabText(5, translator.tr('tab_all_in_one', 'tabs'))
            self.tabs.setTabText(6, translator.tr('tab_settings', 'tabs'))

            self.statusBar.showMessage(
                translator.tr('status_ready'), 5000
            )

            for tab in [
                self.convert_tab, self.merge_tab, self.split_tab,
                self.forms_tab, self.compress_tab, self.all_in_one_tab,
                self.settings_tab,
            ]:
                if hasattr(tab, 'retranslate_ui'):
                    tab.retranslate_ui()

            return True
        return False
