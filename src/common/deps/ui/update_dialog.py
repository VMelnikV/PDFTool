"""Діалог оновлення залежностей.

Показує список пакетів зі станами:
  * актуально
  * доступне оновлення X → Y
  * не встановлено

Користувач обирає чекбоксами, що оновлювати, і натискає «Оновити вибрані».
Оновлення виконується у фоні (QThread) з прогрес-баром.
Помилки показуються з альтернативними варіантами.

Усі тексти локалізовано через translator.tr / translator.trf.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from common.i18n.translator import translator

from ..env import EnvInfo, detect_env
from ..updater import UpdateInfo, UpdateResult, check_updates, run_updates


# Список пакетів, які перевіряємо. Відповідає requirements/base.txt
DEFAULT_PACKAGES: list[tuple[str, str]] = [
    ("PySide6", "PySide6"),
    ("Pillow", "PIL"),
    ("pypdf", "pypdf"),
    ("PyPDFForm", "PyPDFForm"),
    ("pdf2image", "pdf2image"),
]


# ─────────────────────────────────────────────────────────────
# Фонові потоки
# ─────────────────────────────────────────────────────────────

class _CheckThread(QThread):
    """Перевіряє оновлення через PyPI у фоні."""

    finished_ok = Signal(object)   # list[UpdateInfo]
    failed = Signal(str)

    def __init__(self, packages: list[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.packages = packages

    def run(self) -> None:
        try:
            items = check_updates(self.packages)
            self.finished_ok.emit(items)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class _UpdateThread(QThread):
    """Запускає pip install -U для обраних пакетів."""

    progress = Signal(int, int, str)   # current, total, name
    finished_ok = Signal(object)       # UpdateResult
    failed = Signal(str)

    def __init__(
        self,
        items: list[UpdateInfo],
        env: EnvInfo,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.items = items
        self.env = env

    def run(self) -> None:
        try:
            def cb(current: int, total: int, name: str) -> None:
                self.progress.emit(current, total, name)

            result = run_updates(self.items, self.env, progress_cb=cb)
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────
# Рядок пакета
# ─────────────────────────────────────────────────────────────

class _PackageRow(QWidget):
    """Один рядок: чекбокс | назва | версія | статус."""

    def __init__(self, info: UpdateInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.info = info

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self.cb = QCheckBox()
        self.cb.setChecked(info.selected and info.needs_action)
        self.cb.setEnabled(info.needs_action)
        self.cb.toggled.connect(self._on_toggled)
        layout.addWidget(self.cb)

        name = QLabel(info.pip_name)
        name_font = QFont()
        name_font.setBold(info.needs_action)
        name.setFont(name_font)
        name.setMinimumWidth(140)
        layout.addWidget(name)

        version = QLabel(self._version_label())
        version.setStyleSheet(
            "color: #2e7d32;" if not info.needs_action else "color: #c62828;"
        )
        layout.addWidget(version, 1)

        if info.check_failed:
            warn = QLabel(f"⚠ {info.check_failed}")
            warn.setStyleSheet("color: #f9a825;")
            layout.addWidget(warn, 1)

    def _version_label(self) -> str:
        """Локалізований рядок версії для показу.

        - не встановлено  → "не встановлено"
        - X → Y          → "X  →  Y"
        - X (актуально)  → "X (актуально)"
        - невідомо       → "?"
        """
        info = self.info
        if not info.installed:
            return translator.tr("version_not_installed", "update")
        if info.current and info.latest and info.outdated:
            return f"{info.current}  →  {info.latest}"
        if info.current:
            actual = translator.tr("version_actual", "update")
            return f"{info.current} ({actual})"
        return translator.tr("version_unknown", "update")

    def _on_toggled(self, checked: bool) -> None:
        self.info.selected = checked


# ─────────────────────────────────────────────────────────────
# Головний діалог
# ─────────────────────────────────────────────────────────────

class UpdateDialog(QDialog):
    """Діалог оновлення залежностей.

    Фази:
      1. Перевірка PyPI (у фоні).
      2. Показ списку з чекбоксами.
      3. Запуск pip install -U (у фоні, з прогрес-баром).
      4. Показ підсумку (успішні + помилки з альтернативами).
    """

    def __init__(self, env: EnvInfo | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(translator.tr("dialog_title", "update"))
        self.resize(760, 560)

        self.env = env or detect_env()
        self._items: list[UpdateInfo] = []
        self._rows: list[_PackageRow] = []
        self._check_thread: Optional[_CheckThread] = None
        self._update_thread: Optional[_UpdateThread] = None
        self._closing = False

        self._build_ui()
        self._start_check()

    # ── UI ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Заголовок
        title = QLabel(translator.tr("header_title", "update"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Статус
        self.status_label = QLabel(translator.tr("status_checking", "update"))
        self.status_label.setStyleSheet("color: #555;")
        layout.addWidget(self.status_label)

        # Прогрес-бар
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)

        # Список
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 4, 0, 4)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch(1)
        scroll.setWidget(self.list_host)

        layout.addWidget(scroll, 1)

        # Помилки (приховано до моменту помилки)
        self.error_box = QTextEdit()
        self.error_box.setReadOnly(True)
        self.error_box.setFont(QFont("Monospace", 9))
        self.error_box.setStyleSheet(
            "QTextEdit { background: #fff3f3; border: 1px solid #e0b0b0; "
            "border-radius: 3px; padding: 6px; }"
        )
        self.error_box.setMinimumHeight(120)
        self.error_box.setMaximumHeight(220)
        self.error_box.setVisible(False)
        layout.addWidget(self.error_box)

        # Кнопки
        btns = QHBoxLayout()
        btns.setSpacing(8)

        self.btn_refresh = QPushButton(translator.tr("btn_refresh", "update"))
        self.btn_refresh.clicked.connect(self._start_check)
        btns.addWidget(self.btn_refresh)

        btns.addStretch(1)

        self.btn_close = QPushButton(translator.tr("btn_close", "update"))
        self.btn_close.setAutoDefault(False)
        self.btn_close.clicked.connect(self._on_close)
        btns.addWidget(self.btn_close)

        self.btn_update = QPushButton(translator.tr("btn_update", "update"))
        self.btn_update.setAutoDefault(False)
        self.btn_update.clicked.connect(self._start_update)
        self.btn_update.setEnabled(False)
        btns.addWidget(self.btn_update)

        layout.addLayout(btns)

    # ── Перевірка ───────────────────────────────────────────

    def _start_check(self) -> None:
        if self._check_thread and self._check_thread.isRunning():
            return

        self._clear_list()
        self.status_label.setText(translator.tr("status_checking", "update"))
        self.progress.setValue(0)
        self.btn_update.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.error_box.setVisible(False)

        self._check_thread = _CheckThread(DEFAULT_PACKAGES, parent=None)
        self._check_thread.finished_ok.connect(self._on_check_finished)
        self._check_thread.failed.connect(self._on_check_failed)
        self._check_thread.start()

    def _on_check_finished(self, items: list[UpdateInfo]) -> None:
        self._items = items
        self._render_items(items)
        self.btn_refresh.setEnabled(True)

        n_action = sum(1 for it in items if it.needs_action)
        if n_action:
            self.status_label.setText(
                translator.trf("status_has_actions", "update", count=n_action)
            )
            self.btn_update.setEnabled(True)
        else:
            self.status_label.setText(translator.tr("status_all_ok", "update"))

        self.progress.setValue(100)

    def _on_check_failed(self, message: str) -> None:
        self.status_label.setText(
            translator.trf("status_error_check", "update", error=message)
        )
        self.btn_refresh.setEnabled(True)
        self.progress.setValue(0)

    def _clear_list(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._rows.clear()

    def _render_items(self, items: list[UpdateInfo]) -> None:
        self._clear_list()
        for i, info in enumerate(items):
            row = _PackageRow(info, parent=self.list_host)
            self.list_layout.insertWidget(i, row)
            self._rows.append(row)

    # ── Оновлення ───────────────────────────────────────────

    def _start_update(self) -> None:
        if self._update_thread and self._update_thread.isRunning():
            return

        selected = [it for it in self._items if it.selected and it.needs_action]
        if not selected:
            QMessageBox.information(
                self,
                translator.tr("msg_no_selection_title", "update"),
                translator.tr("msg_no_selection", "update"),
            )
            return

        self.btn_update.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.progress.setValue(0)
        self.error_box.setVisible(False)

        self._update_thread = _UpdateThread(selected, self.env, parent=None)
        self._update_thread.progress.connect(self._on_update_progress)
        self._update_thread.finished_ok.connect(self._on_update_finished)
        self._update_thread.failed.connect(self._on_update_failed)
        self._update_thread.start()

    def _on_update_progress(self, current: int, total: int, name: str) -> None:
        if total:
            self.progress.setValue(int(current / total * 100))
        self.status_label.setText(
            translator.trf(
                "status_updating", "update",
                name=name, current=current, total=total,
            )
        )

    def _on_update_finished(self, result: UpdateResult) -> None:
        self.btn_close.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.progress.setValue(100)

        installed = ", ".join(result.installed) or "—"
        updated = ", ".join(result.updated) or "—"
        failed = len(result.failed)

        if result.installed or result.updated or result.failed:
            self.status_label.setText(
                translator.trf(
                    "status_done", "update",
                    installed=installed, updated=updated, failed=failed,
                )
            )
        else:
            self.status_label.setText(
                translator.tr("status_nothing", "update")
            )

        if result.failed:
            self.error_box.setVisible(True)
            lines: list[str] = []
            for name, err in result.failed.items():
                lines.append(f"❌ {name}:")
                lines.append(err)
                lines.append("")
            self.error_box.setPlainText("\n".join(lines))

        if result.any_success:
            QMessageBox.information(
                self,
                translator.tr("msg_restart_needed_title", "update"),
                translator.tr("msg_restart_needed", "update"),
            )
            self.btn_update.setEnabled(True)

    def _on_update_failed(self, message: str) -> None:
        self.status_label.setText(
            translator.trf("status_error_update", "update", error=message)
        )
        self.btn_close.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.btn_update.setEnabled(True)
        self.progress.setValue(0)

    # ── Закриття ────────────────────────────────────────────

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True

        if (self._update_thread and self._update_thread.isRunning()) or (
            self._check_thread and self._check_thread.isRunning()
        ):
            res = QMessageBox.question(
                self,
                translator.tr("msg_confirm_close_title", "update"),
                translator.tr("msg_confirm_close", "update"),
            )
            if res != QMessageBox.Yes:
                self._closing = False
                return

        self.reject()


# ─────────────────────────────────────────────────────────────
# Демо-запуск: python -m common.deps.ui.update_dialog
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    dialog = UpdateDialog()
    dialog.exec()
