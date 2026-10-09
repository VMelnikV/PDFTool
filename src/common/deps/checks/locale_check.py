"""Перевірка наявності мовних файлів.

Перевіряє, що вбудовані переклади (uk, en) доступні.
Не критично, бо завжди є fallback на англійську.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..env import EnvInfo
from .base import Check, CheckResult

REQUIRED_LANGS = ("en", "uk")


class LocaleCheck(Check):
    key = "locale.translations"
    name = "Мовні файли"
    critical = False
    description = "Вбудовані переклади (uk, en)."

    def run(self, env: EnvInfo) -> CheckResult:
        builtin = self._find_builtin_dir()
        if not builtin:
            return self.warn(
                "не знайдено теку перекладів",
                fix_kind="manual",
                fix_hint=(
                    "Переклади мають бути в "
                    "src/common/i18n/translations/ (uk.json, en.json)."
                ),
                details="Не вдалось знайти каталог з вбудованими перекладами.",
            )

        found: list[str] = []
        missing: list[str] = []

        for lang in REQUIRED_LANGS:
            if (builtin / f"{lang}.json").exists():
                found.append(lang)
            else:
                missing.append(lang)

        # Користувацькі переклади (додаткові)
        user_langs = self._list_user_langs()

        details_lines = [
            f"Вбудовані: {', '.join(found) or '—'}",
            f"Відсутні: {', '.join(missing) or '—'}",
        ]
        if user_langs:
            details_lines.append(f"Користувацькі: {', '.join(user_langs)}")

        if missing:
            return self.warn(
                f"відсутні: {', '.join(missing)}",
                fix_kind="manual",
                fix_hint=(
                    f"Відсутні вбудовані переклади: {', '.join(missing)}.\n"
                    "Програма використає fallback на англійську."
                ),
                details="\n".join(details_lines),
            )

        return self.ok(
            f"{', '.join(found)}",
            details="\n".join(details_lines),
        )

    # ─── хелпери ────────────────────────────────────────────

    def _find_builtin_dir(self) -> Path | None:
        """Шукає теку з вбудованими перекладами."""
        import sys

        candidates = []

        # 1. У замороженому вигляді (AppImage)
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidates.append(
                Path(sys._MEIPASS) / "common" / "i18n" / "translations"
            )

        # 2. Звичайний запуск з коду
        here = Path(__file__).resolve()
        # src/common/deps/checks/locale_check.py → src/common/i18n/translations
        candidates.append(
            here.parent.parent.parent / "i18n" / "translations"
        )

        for c in candidates:
            if c.exists():
                return c
        return None

    def _list_user_langs(self) -> list[str]:
        """Список мов у користувацькій теці."""
        config_home = os.environ.get(
            "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
        )
        user_dir = Path(config_home) / "pdf_tool" / "translations"
        if not user_dir.exists():
            return []
        return sorted(
            p.stem for p in user_dir.glob("*.json")
        )
