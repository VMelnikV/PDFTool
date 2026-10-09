"""PySide6-вікно перевірки залежностей.

Єдиний UI для трьох сценаріїв:
  * стартова перевірка (з launcher.py, до головного вікна)
  * меню «Довідка → Перевірити залежності»
  * шестерінка «Перевірити зараз»

Особливості:
  * Усі тексти локалізовано через translator.tr / translator.trf
  * Критичні перевірки — жирним шрифтом
  * Бейджі [критично] / [опційно] з кольорами
  * Під FAIL/WARN — розгорнута інструкція з кнопкою «Копіювати» (без sudo)
  * Прогрес-бар під час повторної перевірки
  * Фонові перевірки через QThread (UI не блокується)
  * Модальний QDialog — працює і до, і після QApplication

Виправлення v4:
  * прибрано WA_DeleteOnClose — він видаляв C++ QDialog до читання result
  * не використовуємо dialog.result() після exec() — довіряємо self.result
  * _do_accept / _do_reject захищено try/except RuntimeError
  * result скидається в EXIT на початку run() — хрестик = вихід
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from common.i18n.translator import translator

from ..env import EnvInfo, detect_env
from ..instructions import SUDO_NOTE, has_sudo, strip_sudo
from ..report import CheckReport, run_all_checks
from ..style import (
    COLOR_BADGE_CRITICAL,
    COLOR_BADGE_OPTIONAL,
    COLOR_TEXT,
    STATUS_COLORS,
    STATUS_ICONS,
    format_message,
    row_badge,
)
from .base import DependencyWindowBase, DialogResult


# ─────────────────────────────────────────────────────────────
# Іконка
# ─────────────────────────────────────────────────────────────

def _find_icon_path() -> str | None:
    """Шукає pdf_icon.png у стандартних місцях."""
    candidates: list[Path] = []

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "pdf_icon.png")
        candidates.append(
            Path(sys._MEIPASS) / "common" / "resources" / "icons" / "pdf_icon.png"
        )

    if getattr(sys, "frozen", False):
        base = Path(os.path.dirname(sys.executable))
        candidates.append(base / "pdf_icon.png")
        candidates.append(
            base / ".." / "share" / "icons" / "hicolor" / "256x256"
            / "apps" / "pdf-tool.png"
        )

    here = Path(__file__).resolve()
    candidates.append(
        here.parent.parent.parent / "resources" / "icons" / "pdf_icon.png"
    )

    for c in candidates:
        try:
            if c.exists():
                return str(c)
        except OSError:
            continue
    return None


# ─────────────────────────────────────────────────────────────
# Фоновий потік перевірок
# ─────────────────────────────────────────────────────────────

class _CheckerThread(QThread):
    """Виконує run_all_checks у фоні. parent=None (не QObject-батько)."""

    progress = Signal(int, int)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, env: EnvInfo, parent=None) -> None:
        super().__init__(parent)
        self.env = env

    def run(self) -> None:
        try:
            def cb(current: int, total: int, _result) -> None:
                self.progress.emit(current, total)

            report = run_all_checks(self.env, progress_cb=cb)
            self.finished_ok.emit(report)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────
# Рядок однієї перевірки
# ─────────────────────────────────────────────────────────────

class _RowWidget(QWidget):
    """Рядок перевірки: іконка | текст | бейдж (+ інструкція для FAIL/WARN)."""

    def __init__(self, result, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.result = result
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)

        font = QFont()
        font.setPointSize(10)
        font.setBold(self.result.critical)

        icon = QLabel(STATUS_ICONS.get(self.result.status, "?"))
        icon.setFont(font)
        icon.setFixedWidth(20)
        color = STATUS_COLORS.get(self.result.status, COLOR_TEXT)
        icon.setStyleSheet(f"color: {color};")
        row.addWidget(icon, 0, Qt.AlignTop)

        msg = QLabel(format_message(self.result))
        msg.setFont(font)
        msg.setWordWrap(True)
        msg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        msg.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        row.addWidget(msg, 1)

        badge_color = (
            COLOR_BADGE_CRITICAL if self.result.critical
            else COLOR_BADGE_OPTIONAL
        )
        badge = QLabel(f"[{row_badge(self.result)}]")
        badge_font = QFont()
        badge_font.setPointSize(9)
        badge_font.setBold(True)
        badge.setFont(badge_font)
        badge.setStyleSheet(f"color: {badge_color};")
        badge.setAlignment(Qt.AlignRight | Qt.AlignTop)
        row.addWidget(badge, 0, Qt.AlignTop)

        outer.addLayout(row)

        if self.result.needs_attention and self.result.install_instructions:
            outer.addWidget(self._make_instructions())

    def _make_instructions(self) -> QWidget:
        box = QFrame()
        box.setFrameShape(QFrame.NoFrame)
        box.setStyleSheet(
            "QFrame { background: #f7f7f7; border-radius: 4px; }"
        )

        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(self.result.install_instructions)
        text.setFont(QFont("Monospace", 9))
        text.setLineWrapMode(QTextEdit.NoWrap)
        text.setStyleSheet(
            "QTextEdit { background: #ffffff; border: 1px solid #e0e0e0; "
            "border-radius: 3px; padding: 4px; }"
        )
        text.setMinimumHeight(80)
        text.setMaximumHeight(280)
        layout.addWidget(text)

        btns = QHBoxLayout()
        btns.setSpacing(6)

        self.btn_copy = QPushButton(translator.tr("btn_copy", "deps_ui"))
        self.btn_copy.setAutoDefault(False)
        self.btn_copy.clicked.connect(self._on_copy)
        btns.addWidget(self.btn_copy)

        if self.result.docs_url:
            btn_docs = QPushButton(translator.tr("btn_docs", "deps_ui"))
            btn_docs.setAutoDefault(False)
            btn_docs.clicked.connect(self._on_docs)
            btns.addWidget(btn_docs)

        btns.addStretch(1)
        layout.addLayout(btns)

        if has_sudo(self.result.install_instructions):
            note = QLabel(SUDO_NOTE)
            note.setWordWrap(True)
            note_font = QFont()
            note_font.setPointSize(9)
            note.setFont(note_font)
            note.setStyleSheet("color: #777777;")
            layout.addWidget(note)

        return box

    def _on_copy(self) -> None:
        safe = strip_sudo(self.result.install_instructions)
        QGuiApplication.clipboard().setText(safe)

        old_text = self.btn_copy.text()
        self.btn_copy.setText(translator.tr("btn_copied", "deps_ui"))
        self.btn_copy.setEnabled(False)
        QTimer.singleShot(
            1500,
            lambda: (
                self.btn_copy.setText(old_text),
                self.btn_copy.setEnabled(True),
            ),
        )

    def _on_docs(self) -> None:
        if self.result.docs_url:
            QDesktopServices.openUrl(QUrl(self.result.docs_url))


# ─────────────────────────────────────────────────────────────
# Головне вікно
# ─────────────────────────────────────────────────────────────

class QtDependencyWindow(DependencyWindowBase):
    """PySide6-вікно перевірки залежностей.

    Модальний QDialog — працює як при старті (до головного вікна),
    так і з меню / шестерінки в уже запущеному застосунку.
    """

    def __init__(self, report: CheckReport) -> None:
        super().__init__(report)
        self.result: DialogResult = DialogResult.EXIT
        self._thread: Optional[_CheckerThread] = None
        self._dialog: Optional[QDialog] = None
        self._closing: bool = False

    # ── Публічний запуск ────────────────────────────────────

    def run(self) -> DialogResult:
        """Показує вікно модально і повертає результат."""
        self._closing = False
        self.result = DialogResult.EXIT

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            app.setApplicationName("PDF Tool")

        dialog = QDialog()
        self._dialog = dialog
        dialog.setWindowTitle(translator.tr("window_title", "deps_ui"))
        dialog.resize(900, 680)
        dialog.setMinimumSize(640, 420)
        dialog.setModal(True)
        # НЕ ставимо WA_DeleteOnClose — він видаляє C++ об'єкт
        # до того, як ми дочитаємо result().

        icon_path = _find_icon_path()
        if icon_path:
            dialog.setWindowIcon(QIcon(icon_path))

        self._build_dialog(dialog)

        dialog.exec()

        if self.result == DialogResult.CONTINUE and not self.report.all_critical_ok:
            return DialogResult.EXIT
        return self.result

    # ── Побудова ─────────────────────────────────────────────

    def _build_dialog(self, dialog: QDialog) -> None:
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header = QVBoxLayout()
        header.setSpacing(2)

        title = QLabel(translator.tr("header_title", "deps_ui"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        self.env_label = QLabel(self._env_text())
        env_font = QFont()
        env_font.setPointSize(9)
        self.env_label.setFont(env_font)
        self.env_label.setStyleSheet("color: #555555;")
        self.env_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header.addWidget(self.env_label)

        layout.addLayout(header)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 4, 0, 4)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch(1)
        scroll.setWidget(self.list_host)

        layout.addWidget(scroll, 1)

        self.summary_label = QLabel("")
        sum_font = QFont()
        sum_font.setPointSize(10)
        sum_font.setBold(True)
        self.summary_label.setFont(sum_font)
        layout.addWidget(self.summary_label)

        btns = QHBoxLayout()
        btns.setSpacing(8)

        self.btn_recheck = QPushButton(translator.tr("btn_recheck", "deps_ui"))
        self.btn_recheck.setAutoDefault(False)
        self.btn_recheck.clicked.connect(self._on_recheck)
        btns.addWidget(self.btn_recheck)

        btns.addStretch(1)

        self.btn_exit = QPushButton(translator.tr("btn_exit", "deps_ui"))
        self.btn_exit.setAutoDefault(False)
        self.btn_exit.clicked.connect(self._on_exit)
        btns.addWidget(self.btn_exit)

        self.btn_continue = QPushButton(translator.tr("btn_continue", "deps_ui"))
        self.btn_continue.setAutoDefault(False)
        self.btn_continue.clicked.connect(self._on_continue)
        btns.addWidget(self.btn_continue)

        layout.addLayout(btns)

        self._render_results()
        self._update_summary()

    # ── Допоміжне ────────────────────────────────────────────

    def _env_text(self) -> str:
        if not self.report.env:
            return ""
        env = self.report.env
        return translator.trf(
            "env_line", "deps_ui",
            kind=env.display_name,
            python=env.python,
            distro=env.distro,
        )

    def _render_results(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        for i, result in enumerate(self.report.results):
            row = _RowWidget(result, parent=self.list_host)
            self.list_layout.insertWidget(i, row)

    def _update_summary(self) -> None:
        c = self.report.counts()
        parts = [f"OK: {c['ok']}"]
        if c["warn"]:
            parts.append(f"попереджень: {c['warn']}")
        if c["fail"]:
            parts.append(f"помилок: {c['fail']}")
        if c["critical_fail"]:
            parts.append(f"критичних: {c['critical_fail']}")
        self.summary_label.setText("   |   ".join(parts))
        self.btn_continue.setEnabled(self.report.all_critical_ok)

    # ── Дії ──────────────────────────────────────────────────

    def _on_recheck(self) -> None:
        if self._thread and self._thread.isRunning():
            return

        if self._thread is not None:
            try:
                self._thread.wait(50)
            except Exception:
                pass

        self.btn_recheck.setEnabled(False)
        self.btn_continue.setEnabled(False)
        self.progress.setValue(0)

        try:
            env = detect_env()
            self._thread = _CheckerThread(env, parent=None)
            self._thread.progress.connect(self._on_progress)
            self._thread.finished_ok.connect(self._on_finished)
            self._thread.failed.connect(self._on_failed)
            self._thread.start()
        except Exception as exc:  # noqa: BLE001
            self.btn_recheck.setEnabled(True)
            self.btn_continue.setEnabled(self.report.all_critical_ok)
            self.summary_label.setText(
                translator.trf(
                    "status_error_start", "deps_ui",
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    def _on_progress(self, current: int, total: int) -> None:
        if total:
            self.progress.setValue(int(current / total * 100))

    def _on_finished(self, report: CheckReport) -> None:
        self.report = report
        self.env_label.setText(self._env_text())
        self._render_results()
        self._update_summary()
        self.btn_recheck.setEnabled(True)
        self.progress.setValue(100)

    def _on_failed(self, message: str) -> None:
        self.btn_recheck.setEnabled(True)
        self.btn_continue.setEnabled(self.report.all_critical_ok)
        self.progress.setValue(0)
        self.summary_label.setText(
            translator.trf("status_error_check", "deps_ui", error=message)
        )

    def _on_continue(self) -> None:
        if self._closing:
            return
        if not self.report.all_critical_ok:
            return
        self._closing = True
        self.result = DialogResult.CONTINUE
        QTimer.singleShot(0, self._do_accept)

    def _on_exit(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.result = DialogResult.EXIT
        QTimer.singleShot(0, self._do_reject)

    def _do_accept(self) -> None:
        try:
            if self._dialog is not None and self._dialog.isVisible():
                self._dialog.accept()
        except RuntimeError:
            pass

    def _do_reject(self) -> None:
        try:
            if self._dialog is not None and self._dialog.isVisible():
                self._dialog.reject()
        except RuntimeError:
            pass


# ─────────────────────────────────────────────────────────────
# Демо-запуск: python -m common.deps.ui.qt_window
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    env = detect_env()
    report = run_all_checks(env)

    window = QtDependencyWindow(report)
    result = window.run()

    print(f"DialogResult: {result.value}")
    sys.exit(0 if result == DialogResult.CONTINUE else 1)
