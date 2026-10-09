"""UI-шар для вікна перевірки залежностей.

Три реалізації з єдиним контрактом:
  * cli_report.py — CLI (аварійний fallback)
  * qt_window.py  — PySide6 (основний GUI)

Вибір — через launcher.pick_ui().

Увага: launcher НЕ імпортується тут, щоб уникнути RuntimeWarning
при `python -m common.deps.ui.launcher`. Імпортуйте явно:
    from common.deps.ui.launcher import pick_ui, run_window
"""

from .base import DependencyWindowBase, DialogResult

__all__ = ["DependencyWindowBase", "DialogResult"]
