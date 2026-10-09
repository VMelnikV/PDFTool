"""Універсальна перевірка Python-бібліотек.

Один клас LibCheck приймає параметри (ім'я, імпорт, мінімальна версія,
критичність) — і створює готову перевірку.

Використовується в registry.py так:
    LibCheck("pypdf", import_name="pypdf", critical=True)

Клас універсальний: key/name задаються в __init__, тому
_validate_key = False.
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
from typing import Any

from ..env import EnvInfo
from .base import Check, CheckResult


class LibCheck(Check):
    """Перевірка однієї Python-бібліотеки.

    Параметри:
        pip_name     — ім'я пакета для pip (наприклад, "Pillow")
        import_name  — ім'я модуля для import (за замовч. = pip_name)
        key          — унікальний id (за замовч. "lib.<pip_name>")
        display_name — людська назва (за замовч. = pip_name)
        min_version  — мінімальна версія (опційно)
        critical     — критичність
        docs_url     — посилання на документацію (опційно)
        description  — короткий опис (опційно)
    """

    # Універсальний клас — key/name задаються в __init__,
    # тому пропускаємо перевірку в __init_subclass__.
    _validate_key = False

    def __init__(
        self,
        pip_name: str,
        *,
        import_name: str | None = None,
        key: str | None = None,
        display_name: str | None = None,
        min_version: str | None = None,
        critical: bool = False,
        docs_url: str | None = None,
        description: str = "",
    ) -> None:
        self.key = key or f"lib.{pip_name.lower()}"
        self.name = display_name or pip_name
        self.critical = critical
        self.description = description

        self._pip_name = pip_name
        self._import_name = import_name or pip_name
        self._min_version = min_version
        self._docs_url = docs_url

    def run(self, env: EnvInfo) -> CheckResult:
        # 1. Перевірка імпорту
        try:
            module = importlib.import_module(self._import_name)
        except ImportError:
            return self.fail(
                "не встановлено",
                fix_kind="pip",
                fix_arg=self._pip_name,
                fix_min_version=self._min_version,
                can_autofix=env.can_autofix_pip,
                fix_hint=f"pip install {self._pip_name}",
                docs_url=self._docs_url,
                details=self.description or None,
            )

        # 2. Визначення версії
        version = self._get_version(module)

        if not version:
            return self.ok(
                f"{self.name} (версія невідома)",
                details="Модуль імпортується, але версію визначити не вдалося.",
            )

        # 3. Перевірка мінімальної версії
        if self._min_version and self._is_older(version, self._min_version):
            return self.warn(
                f"{version} (рекомендовано ≥ {self._min_version})",
                fix_kind="pip",
                fix_arg=self._pip_name,
                fix_min_version=self._min_version,
                can_autofix=env.can_autofix_pip,
                fix_hint=f"pip install -U {self._pip_name}>={self._min_version}",
                docs_url=self._docs_url,
                details=(
                    f"Встановлено: {version}\n"
                    f"Рекомендовано: ≥ {self._min_version}"
                ),
            )

        return self.ok(
            f"{self.name} {version}",
            details=f"Версія: {version}",
        )

    # ─── хелпери ────────────────────────────────────────────

    def _get_version(self, module: Any) -> str | None:
        """Пробує різні способи отримати версію."""
        # 1. importlib.metadata (найнадійніше для встановлених пакетів)
        try:
            return md.version(self._pip_name)
        except md.PackageNotFoundError:
            pass

        # 2. Атрибут __version__
        v = getattr(module, "__version__", None)
        if v:
            return str(v)

        # 3. Атрибут VERSION (для PIL)
        v = getattr(module, "VERSION", None)
        if v:
            return str(v)

        # 4. Pillow: PIL.__version__ (коли import_name == "PIL")
        try:
            import PIL  # type: ignore

            return getattr(PIL, "__version__", None)
        except ImportError:
            pass

        return None

    def _is_older(self, version: str, min_version: str) -> bool:
        """Порівняння версій через packaging, з fallback на рядки."""
        try:
            from packaging.version import Version

            return Version(version) < Version(min_version)
        except Exception:
            # Якщо packaging недоступний — просте порівняння рядків
            return version < min_version
