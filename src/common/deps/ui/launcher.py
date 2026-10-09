"""Вибір UI та запуск вікна перевірки.

Каскад (зверху вниз, перший доступний):
  1. PySide6  →  qt_window.QtDependencyWindow
  2. CLI      →  cli_report.CliDependencyWindow

Примусовий вибір — параметром force: "qt" | "cli".
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

from .base import DependencyWindowBase, DialogResult

if TYPE_CHECKING:
    from ..report import CheckReport


UiKind = str  # "qt" | "cli"


# ─────────────────────────────────────────────────────────────
# Перевірка доступності
# ─────────────────────────────────────────────────────────────

def has_pyside6() -> bool:
    """Чи можна імпортувати PySide6."""
    return importlib.util.find_spec("PySide6") is not None


def has_display() -> bool:
    """Чи є DISPLAY / WAYLAND_DISPLAY (для GUI на Linux)."""
    import os

    return bool(
        os.environ.get("DISPLAY")
        or os.environ.get("WAYLAND_DISPLAY")
        or os.environ.get("QT_QPA_PLATFORM")  # offscreen для CI
    )


# ─────────────────────────────────────────────────────────────
# Вибір UI
# ─────────────────────────────────────────────────────────────

def pick_ui(force: UiKind | None = None) -> UiKind:
    """Повертає 'qt' | 'cli'."""
    if force is not None:
        _validate_forced_ui(force)
        return force

    # 1. PySide6 (якщо є дисплей)
    if has_pyside6() and has_display():
        return "qt"

    # 2. CLI
    return "cli"


def _validate_forced_ui(kind: UiKind) -> None:
    """Перевіряє, що примусовий UI доступний."""
    if kind == "qt":
        if not has_pyside6():
            raise ValueError(
                "PySide6 не встановлено. Використайте --ui=cli."
            )
        if not has_display():
            raise ValueError(
                "Немає DISPLAY/WAYLAND_DISPLAY. Використайте --ui=cli."
            )
    elif kind == "cli":
        return
    else:
        raise ValueError(f"Невідомий UI: {kind!r}")


# ─────────────────────────────────────────────────────────────
# Створення вікна
# ─────────────────────────────────────────────────────────────

def _make_qt_window(report: "CheckReport") -> DependencyWindowBase:
    try:
        from .qt_window import QtDependencyWindow
    except ImportError as e:
        raise RuntimeError(
            f"Не вдалось завантажити PySide6-вікно: {e}"
        ) from e
    return QtDependencyWindow(report)


def _make_cli_window(report: "CheckReport", **kwargs) -> DependencyWindowBase:
    from .cli_report import CliDependencyWindow
    return CliDependencyWindow(report, **kwargs)


def make_window(
    report: "CheckReport",
    *,
    force: UiKind | None = None,
    **kwargs,
) -> DependencyWindowBase:
    kind = pick_ui(force)

    if kind == "qt":
        return _make_qt_window(report)
    return _make_cli_window(report, **kwargs)


# ─────────────────────────────────────────────────────────────
# Головна функція
# ─────────────────────────────────────────────────────────────

def run_window(
    report: "CheckReport",
    *,
    force: UiKind | None = None,
    **kwargs,
) -> DialogResult:
    window = make_window(report, force=force, **kwargs)
    return window.run()
