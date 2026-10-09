"""Перевірка валідності конфігурації.

Читає ~/.config/pdf_tool/config.json (якщо існує).
Якщо файл пошкоджений — показує FAIL з інструкцією.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..env import EnvInfo
from .base import Check, CheckResult


class ConfigCheck(Check):
    key = "config.json"
    name = "Конфігурація"
    critical = False
    description = "Файл ~/.config/pdf_tool/config.json"

    def run(self, env: EnvInfo) -> CheckResult:
        config_home = os.environ.get(
            "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
        )
        config_file = Path(config_home) / "pdf_tool" / "config.json"

        if not config_file.exists():
            return self.ok(
                "файл ще не створено",
                details=(
                    f"Очікуваний шлях: {config_file}\n"
                    "Файл буде створено автоматично при першій зміні "
                    "налаштувань."
                ),
            )

        try:
            text = config_file.read_text(encoding="utf-8")
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return self.fail(
                f"пошкоджений JSON ({e.msg})",
                fix_kind="config",
                fix_hint=(
                    f"Файл {config_file} пошкоджено.\n"
                    f"Видаліть його або виправте JSON:\n"
                    f"    rm {config_file}"
                ),
                details=(
                    f"Шлях: {config_file}\n"
                    f"Помилка: {e}\n"
                    f"Рядок: {e.lineno}, колонка: {e.colno}"
                ),
            )
        except OSError as e:
            return self.fail(
                f"не вдалось прочитати: {e}",
                fix_kind="fs",
                fix_hint=f"Перевірте права: ls -la {config_file}",
                details=f"Шлях: {config_file}\n{e}",
            )

        if not isinstance(data, dict):
            return self.fail(
                "корінь не є об'єктом",
                fix_kind="config",
                fix_hint=f"Видаліть {config_file} і перезапустіть.",
                details=f"Очікується об'єкт {{}}, отримано {type(data).__name__}",
            )

        return self.ok(
            "валідний",
            details=(
                f"Шлях: {config_file}\n"
                f"Ключів верхнього рівня: {len(data)}"
            ),
        )
