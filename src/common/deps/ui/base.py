"""Базовий контракт для вікон перевірки залежностей.

Тут визначено:
  * DialogResult          — результат закриття вікна
  * DependencyWindowBase  — абстрактний клас для всіх трьох UI

Конкретні реалізації (tkinter, PySide6, CLI) успадковують
DependencyWindowBase і реалізують метод run().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..report import CheckReport


class DialogResult(Enum):
    """Результат закриття вікна перевірки."""

    CONTINUE = "continue"   # продовжити запуск застосунку
    EXIT = "exit"           # вийти (критичні помилки / користувач відмовився)


class DependencyWindowBase(ABC):
    """Абстрактне вікно перевірки залежностей.

    Конкретні реалізації (tkinter, PySide6) мають:
      * показати список CheckResult з кольорами та бейджами
      * показати інструкції для FAIL/WARN
      * дозволити копіювання (без sudo)
      * повернути DialogResult з run()

    CLI-реалізація не є вікном, але дотримується того ж контракту
    для уніфікованого вибору через launcher.pick_ui().
    """

    def __init__(self, report: "CheckReport") -> None:
        self.report = report

    @abstractmethod
    def run(self) -> DialogResult:
        """Показати вікно / вивести звіт і повернути результат."""
        raise NotImplementedError
