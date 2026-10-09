"""Перевірка операційної системи.

PDF Tool розроблено спеціально для Linux. На інших системах
застосунок може працювати нестабільно або взагалі не запуститись.
"""

from __future__ import annotations

import sys

from ..env import EnvInfo
from .base import Check, CheckResult


class PlatformCheck(Check):
    key = "platform.os"
    name = "Операційна система"
    critical = True
    description = "PDF Tool підтримує лише Linux."

    def run(self, env: EnvInfo) -> CheckResult:
        if sys.platform.startswith("linux"):
            return self.ok(
                f"Linux ({env.distro})",
                details=(
                    f"Платформа: {sys.platform}\n"
                    f"Дистрибутив: {env.distro}"
                ),
            )

        return self.fail(
            f"Підтримується лише Linux (знайдено {sys.platform})",
            fix_kind="manual",
            fix_hint=(
                "Запустіть PDF Tool під Linux або у WSL2 (Windows).\n"
                "На macOS та Windows нативний запуск не підтримується."
            ),
            details=(
                f"Поточна платформа: {sys.platform}\n"
                "PDF Tool використовує Linux-специфічні утиліти "
                "(Ghostscript, poppler-utils, shutil.which) та "
                "розрахований на XDG-конфігурацію."
            ),
        )
