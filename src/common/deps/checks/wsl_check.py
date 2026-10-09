"""Перевірка середовища WSL.

WSL2 — це Linux-підсистема в Windows. Хоча sys.platform == "linux",
можливі проблеми з доступом до файлів на диску Windows, зовнішніми
утилітами та GUI. Тому показуємо окреме попередження.
"""

from __future__ import annotations

from ..env import EnvInfo
from .base import Check, CheckResult


class WSLCheck(Check):
    key = "platform.wsl"
    name = "Середовище WSL"
    critical = False
    description = "PDF Tool розроблено для нативного Linux."

    def run(self, env: EnvInfo) -> CheckResult:
        if not env.is_wsl:
            return self.ok("Не WSL (нативний Linux)")

        version = f"WSL{env.wsl_version}" if env.wsl_version else "WSL"

        return self.warn(
            f"{version} — можлива нестабільна робота",
            fix_kind="manual",
            fix_hint=(
                "Рекомендації для роботи у WSL:\n"
                "  • Зберігайте файли всередині ~/ (Linux FS), "
                "а не на /mnt/c/...\n"
                "  • Переконайтесь, що ghostscript, poppler-utils "
                "встановлені всередині WSL\n"
                "  • Для GUI потрібен WSLg (Windows 11) або X-сервер"
            ),
            details=(
                f"Виявлено: {version}\n"
                "PDF Tool розроблено спеціально для нативного Linux.\n"
                "У WSL можливі проблеми з:\n"
                "  • доступом до файлів на диску Windows (/mnt/c/...)\n"
                "  • зовнішніми утилітами (ghostscript, poppler-utils)\n"
                "  • графічним інтерфейсом (потрібен WSLg або X-сервер)\n"
                "Рекомендовано працювати з файлами всередині ~/."
            ),
        )
