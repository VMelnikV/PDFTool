"""Перевірка версії Python.

Мінімальна підтримувана версія — 3.10 (через
platform.freedesktop_os_release() та сучасний синтаксис).
"""

from __future__ import annotations

from ..env import EnvInfo
from .base import Check, CheckResult

MIN_VERSION = (3, 10)


class PythonVersionCheck(Check):
    key = "python.version"
    name = "Версія Python"
    critical = True
    description = f"Потрібен Python ≥ {'.'.join(map(str, MIN_VERSION))}."

    def run(self, env: EnvInfo) -> CheckResult:
        current = env.python_version  # (major, minor, micro)
        current_str = env.python_version_str
        min_str = ".".join(map(str, MIN_VERSION))

        if current >= MIN_VERSION:
            return self.ok(
                f"Python {current_str}",
                details=(
                    f"Інтерпретатор: {env.python}\n"
                    f"Версія: {current_str}"
                ),
            )

        return self.fail(
            f"Python {current_str} (потрібен ≥ {min_str})",
            fix_kind="manual",
            fix_hint=(
                f"Встановіть або активуйте Python ≥ {min_str}.\n"
                f"Перевірити поточну версію:\n"
                f"    {env.python} --version"
            ),
            details=(
                f"Поточна версія: {current_str}\n"
                f"Мінімальна: {min_str}\n"
                f"Інтерпретатор: {env.python}"
            ),
        )
