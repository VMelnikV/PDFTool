"""Вкладка налаштувань ⚙️ (шестерінка).

Розташована після «Все в одному».
Містить:
  * Вибір мови інтерфейсу (uk / en / інші з translations/)
  * Кнопку «Перевірити залежності зараз» — відкриває QtDependencyWindow
  * Кнопку «Оновити залежності» — відкриває UpdateDialog
  * Чекбокс «Перевіряти при старті»
  * Інформацію про версію + теку логів + кнопку «Відкрити теку логів»

Усі тексти локалізовано через translator.tr / translator.trf.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from common.deps.config import Config
from common.i18n.translator import translator
from common.version import __version__

APP_VERSION = __version__


class SettingsTab(QWidget):
    """Вкладка налаштувань."""

    status_signal = Signal(str)  # сумісність з іншими вкладками

    def __init__(self, main_window=None) -> None:
        super().__init__()
        self.main_window = main_window
        self.config = Config()

        # Тримає посилання на відкриті діалоги, щоб Python GC
        # не зібрав їх під час роботи QDialog.
        self._last_dep_window: Optional[object] = None
        self._last_update_dialog: Optional[object] = None

        # Стан
        self._lang_combo: QComboBox | None = None
        self._cb_startup: QCheckBox | None = None

        self._build_ui()
        self.retranslate_ui()

    # ── Побудова ────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        host = QWidget()
        scroll.setWidget(host)

        layout = QVBoxLayout(host)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Мова
        self.gb_lang = QGroupBox()
        lang_layout = QVBoxLayout(self.gb_lang)

        lang_row = QHBoxLayout()
        self.lbl_lang = QLabel()
        lang_row.addWidget(self.lbl_lang)

        self._lang_combo = QComboBox()
        self._populate_languages()
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self._lang_combo, 1)
        lang_layout.addLayout(lang_row)

        self.lbl_lang_hint = QLabel()
        self.lbl_lang_hint.setStyleSheet("color: #777;")
        lang_layout.addWidget(self.lbl_lang_hint)

        layout.addWidget(self.gb_lang)

        # ── Залежності
        self.gb_deps = QGroupBox()
        deps_layout = QVBoxLayout(self.gb_deps)

        self.lbl_deps = QLabel()
        self.lbl_deps.setWordWrap(True)
        deps_layout.addWidget(self.lbl_deps)

        btns = QHBoxLayout()

        self.btn_check = QPushButton()
        self.btn_check.clicked.connect(self._on_check_now)
        btns.addWidget(self.btn_check)

        self.btn_update = QPushButton()
        self.btn_update.clicked.connect(self._on_update)
        btns.addWidget(self.btn_update)

        btns.addStretch(1)
        deps_layout.addLayout(btns)

        self._cb_startup = QCheckBox()
        self._cb_startup.setChecked(self.config.get_check_on_startup())
        self._cb_startup.toggled.connect(self._on_startup_toggled)
        deps_layout.addWidget(self._cb_startup)

        self.lbl_startup_hint = QLabel()
        self.lbl_startup_hint.setStyleSheet("color: #777;")
        deps_layout.addWidget(self.lbl_startup_hint)

        layout.addWidget(self.gb_deps)

        # ── Про програму
        self.gb_about = QGroupBox()
        about_layout = QVBoxLayout(self.gb_about)

        version_row = QHBoxLayout()
        self.lbl_version = QLabel()
        version_row.addWidget(self.lbl_version)
        self.lbl_version_value = QLabel(APP_VERSION)
        self.lbl_version_value.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        version_row.addWidget(self.lbl_version_value, 1)
        about_layout.addLayout(version_row)

        logs_row = QHBoxLayout()
        self.lbl_logs = QLabel()
        logs_row.addWidget(self.lbl_logs)
        logs_path = self._logs_dir()
        self.lbl_logs_value = QLabel(str(logs_path))
        self.lbl_logs_value.setStyleSheet("color: #555;")
        self.lbl_logs_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        logs_row.addWidget(self.lbl_logs_value, 1)

        self.btn_open_logs = QPushButton()
        self.btn_open_logs.clicked.connect(self._on_open_logs)
        logs_row.addWidget(self.btn_open_logs)
        about_layout.addLayout(logs_row)

        layout.addWidget(self.gb_about)

        layout.addStretch(1)

    # ── Мови ────────────────────────────────────────────────

    def _populate_languages(self) -> None:
        """Заповнює QComboBox доступними мовами."""
        if self._lang_combo is None:
            return
        self._lang_combo.blockSignals(True)
        self._lang_combo.clear()

        langs = translator.get_available_languages()
        if not langs:
            langs = ["en"]

        for lang in langs:
            display = translator.get_language_display_name(lang)
            self._lang_combo.addItem(f"{display} ({lang})", lang)

        current = translator.get_language()
        idx = self._lang_combo.findData(current)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)

        self._lang_combo.blockSignals(False)

    def _on_language_changed(self, _idx: int) -> None:
        """Змінює мову застосунку через main_window."""
        if self._lang_combo is None:
            return
        lang = self._lang_combo.currentData()
        if not lang or lang == translator.get_language():
            return

        if translator.set_language(lang):
            self.config.set_language(lang)

            # Перемалювати весь інтерфейс (включно з вкладками)
            if self.main_window and hasattr(self.main_window, "change_language"):
                self.main_window.change_language(lang)

            # Перемалювати саму шестерінку
            self.retranslate_ui()

            display = translator.get_language_display_name(lang)
            self.status_signal.emit(
                f"{translator.tr('label_language', 'settings')}: {display}"
            )

    # ── Залежності ──────────────────────────────────────────

    def _on_check_now(self) -> None:
        """Відкриває QtDependencyWindow модально.

        Зберігаємо посилання self._last_dep_window, щоб Python GC
        не зібрав вікно під час виконання (важливо для QTimer усередині).
        """
        try:
            from common.deps.env import detect_env
            from common.deps.report import run_all_checks
            from common.deps.ui.qt_window import QtDependencyWindow

            env = detect_env()
            report = run_all_checks(env)
            window = QtDependencyWindow(report)

            self._last_dep_window = window
            window.run()
        except RuntimeError as exc:
            QMessageBox.warning(
                self,
                translator.tr("msg_check_window_crashed_title", "deps_ui"),
                translator.trf(
                    "msg_check_window_crashed", "deps_ui",
                    error=str(exc),
                ),
            )
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
            self._last_dep_window = None

    def _on_update(self) -> None:
        """Відкриває діалог оновлення залежностей."""
        try:
            from common.deps.ui.update_dialog import UpdateDialog

            dialog = UpdateDialog(parent=self)
            self._last_update_dialog = dialog
            dialog.exec()
        except RuntimeError as exc:
            QMessageBox.warning(
                self,
                translator.tr("msg_update_crashed_title", "update"),
                translator.trf(
                    "msg_update_crashed", "update",
                    error=str(exc),
                ),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                translator.tr("msg_update_error_title", "update"),
                translator.trf(
                    "msg_update_error", "update",
                    error=f"{type(exc).__name__}: {exc}",
                ),
            )
        finally:
            self._last_update_dialog = None

    def _on_startup_toggled(self, checked: bool) -> None:
        self.config.set_check_on_startup(checked)

    # ── Логи ────────────────────────────────────────────────

    def _logs_dir(self) -> Path:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return Path(base) / "pdf_tool" / "logs"

    def _on_open_logs(self) -> None:
        path = self._logs_dir()
        try:
            path.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(
                self,
                translator.tr("logs", "messages"),
                f"{translator.tr('btn_open_logs', 'settings')}:\n{exc}",
            )

    # ── Переклад ────────────────────────────────────────────

    def retranslate_ui(self) -> None:
        """Оновлює всі тексти після зміни мови."""
        tr = translator.tr

        # Мова
        self.gb_lang.setTitle(tr("section_language", "settings"))
        self.lbl_lang.setText(tr("label_language", "settings"))
        self.lbl_lang_hint.setText(tr("hint_language", "settings"))

        # Залежності
        self.gb_deps.setTitle(tr("section_dependencies", "settings"))
        self.lbl_deps.setText(tr("label_dependencies", "settings"))
        self.btn_check.setText(tr("btn_check_now", "settings"))
        self.btn_update.setText(tr("btn_update", "settings"))
        self._cb_startup.setText(tr("cb_check_on_startup", "settings"))
        self.lbl_startup_hint.setText(
            tr("hint_check_on_startup", "settings")
        )

        # Про програму
        self.gb_about.setTitle(tr("section_about", "settings"))
        self.lbl_version.setText(tr("label_version", "settings"))
        self.lbl_logs.setText(tr("label_logs", "settings"))
        self.btn_open_logs.setText(tr("btn_open_logs", "settings"))

        # Оновити список мов (на випадок нових завантажених)
        self._populate_languages()
