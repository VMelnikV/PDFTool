"""Перевірка PEP 668 (externally-managed-environment).

Інформує користувача, чи активний маркер externally-managed
у системному Python. У venv/conda/pipx він не застосовується,
тому показуємо це як INFO, а не FAIL.
"""

from __future__ import annotations

from ..env import EnvInfo
from .base import Check, CheckResult


class PEP668Check(Check):
    key = "python.pep668"
    name = "PEP 668"
    critical = False
    description = "Обмеження глобального pip install у системному Python."

    def run(self, env: EnvInfo) -> CheckResult:
        # У venv/conda/pipx PEP 668 не застосовується
        if env.kind != "system":
            return self.ok(
                f"не застосовується ({env.kind})",
                details=(
                    f"Середовище: {env.kind}\n"
                    "У venv / conda / pipx pip install дозволено завжди."
                ),
            )

        if env.pep668:
            return self.warn(
                "активний у системному Python",
                fix_kind="manual",
                fix_hint=(
                    "Глобальний pip install у системний Python заблоковано.\n"
                    "Рекомендовані варіанти:\n"
                    "  1. Створити venv:  python3 -m venv .venv\n"
                    "  2. Використати pipx:  pipx install <пакет>\n"
                    "  3. На власний ризик:  pip install --break-system-packages"
                ),
                details=(
                    "У системному Python знайдено файл EXTERNALLY-MANAGED.\n"
                    "Це захист від випадкового пошкодження системних пакетів.\n"
                    "Для встановлення залежностей PDF Tool використовуйте venv."
                ),
            )

        return self.ok("не активний у системному Python")
