"""Універсальна перевірка системних утиліт.

Шукає бінарник у PATH через shutil.which() і намагається
отримати версію через `--version`.

Використовується в registry.py так:
    ExternalCheck("gs", display_name="Ghostscript", critical=True)

Клас універсальний: key/name задаються в __init__, тому
_validate_key = False.
"""

from __future__ import annotations

import re
import shutil
import subprocess

from ..env import EnvInfo
from .base import Check, CheckResult


class ExternalCheck(Check):
    """Перевірка однієї системної утиліти.

    Параметри:
        binary        — ім'я бінарника в PATH (наприклад, "gs")
        display_name  — людська назва (за замовч. = binary)
        critical      — критичність
        version_args  — аргументи для отримання версії (за замовч. ["--version"])
        version_regex — regex для витягування версії (опційно)
        docs_url      — посилання (опційно)
        description   — короткий опис (опційно)
    """

    # Універсальний клас — key/name задаються в __init__.
    _validate_key = False

    def __init__(
        self,
        binary: str,
        *,
        display_name: str | None = None,
        critical: bool = False,
        version_args: list[str] | None = None,
        version_regex: str | None = None,
        docs_url: str | None = None,
        description: str = "",
    ) -> None:
        self.key = f"external.{binary}"
        self.name = display_name or binary
        self.critical = critical
        self.description = description

        self._binary = binary
        self._version_args = version_args or ["--version"]
        self._version_regex = version_regex
        self._docs_url = docs_url

    def run(self, env: EnvInfo) -> CheckResult:
        # 1. Пошук у PATH
        path = shutil.which(self._binary)

        if not path:
            return self.fail(
                "не знайдено в PATH",
                fix_kind="external",
                fix_arg=self._binary,
                docs_url=self._docs_url,
                details=(
                    (self.description + "\n\n" if self.description else "")
                    + f"Бінарник '{self._binary}' не знайдено в PATH."
                ),
            )

        # 2. Спроба отримати версію
        version = self._get_version(path)

        if version:
            return self.ok(
                f"{self.name} {version}",
                details=(f"Шлях: {path}\n" f"Версія: {version}"),
            )

        return self.ok(
            f"{self.name} (знайдено)",
            details=f"Шлях: {path}\nВерсію визначити не вдалося.",
        )

    # ─── хелпери ────────────────────────────────────────────

    def _get_version(self, path: str) -> str | None:
        """Запускає бінарник з version_args і парсить вивід."""
        try:
            result = subprocess.run(
                [path] + self._version_args,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None

        output = (result.stdout or "") + "\n" + (result.stderr or "")

        if self._version_regex:
            m = re.search(self._version_regex, output)
            if m:
                return m.group(1) if m.groups() else m.group(0)

        # Загальний regex: перше число виду X.Y або X.Y.Z
        m = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
        if m:
            return m.group(1)

        return None
