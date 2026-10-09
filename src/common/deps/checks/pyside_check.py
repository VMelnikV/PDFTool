"""Перевірка наявності PySide6.

PySide6 — основний GUI-фреймворк PDF Tool. Без нього головне
вікно застосунку не запуститься.
"""

from __future__ import annotations

import importlib.metadata as md

from ..env import EnvInfo
from .base import Check, CheckResult

MIN_VERSION = "6.5.0"


class PySideCheck(Check):
    key = "gui.pyside6"
    name = "PySide6"
    critical = True
    description = "GUI-фреймворк для головного вікна застосунку."

    def run(self, env: EnvInfo) -> CheckResult:
        # 1. Перевірка імпорту
        try:
            import PySide6  # noqa: F401
        except ImportError:
            return self.fail(
                "не встановлено",
                fix_kind="pip",
                fix_arg="PySide6",
                fix_min_version=MIN_VERSION,
                can_autofix=env.can_autofix_pip,
                fix_hint="pip install PySide6",
                docs_url="https://doc.qt.io/qtforpython-6/",
                details=(
                    "PySide6 — офіційні Qt-біндинги для Python (LGPL).\n"
                    "Використовується для всього GUI застосунку."
                ),
            )

        # 2. Визначення версії
        version: str | None = None
        try:
            version = md.version("PySide6")
        except md.PackageNotFoundError:
            version = getattr(PySide6, "__version__", None)

        if not version:
            return self.ok(
                "PySide6 (версія невідома)",
                details="Модуль імпортується, але версію визначити не вдалося.",
            )

        # 3. Перевірка мінімальної версії
        try:
            from packaging.version import Version

            if Version(version) < Version(MIN_VERSION):
                return self.warn(
                    f"{version} (рекомендовано ≥ {MIN_VERSION})",
                    fix_kind="pip",
                    fix_arg="PySide6",
                    fix_min_version=MIN_VERSION,
                    can_autofix=env.can_autofix_pip,
                    fix_hint=f"pip install -U PySide6>={MIN_VERSION}",
                    details=(
                        f"Встановлено: {version}\n"
                        f"Рекомендовано: ≥ {MIN_VERSION}"
                    ),
                )
        except Exception:
            # packaging недоступний — не блокуємо, просто показуємо версію
            pass

        return self.ok(
            f"PySide6 {version}",
            details=f"Версія: {version}",
        )
