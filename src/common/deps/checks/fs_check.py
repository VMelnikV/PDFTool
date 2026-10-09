"""Перевірка файлової системи.

Перевіряє:
  * Права на запис у поточну теку
  * Доступність ~/.config/pdf_tool/
  * Вільне місце на диску
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..env import EnvInfo
from .base import Check, CheckResult


class WriteAccessCheck(Check):
    key = "fs.write"
    name = "Права на запис"
    critical = True
    description = "Чи можна писати в робочі теки."

    def run(self, env: EnvInfo) -> CheckResult:
        problems: list[str] = []

        # 1. Поточна робоча тека
        cwd = Path.cwd()
        if not os.access(cwd, os.W_OK):
            problems.append(f"немає прав на запис у {cwd}")

        # 2. Тека конфігурації
        config_home = os.environ.get(
            "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
        )
        config_dir = Path(config_home) / "pdf_tool"
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            test = config_dir / ".write_test"
            test.touch()
            test.unlink()
        except (OSError, PermissionError) as e:
            problems.append(f"немає прав на {config_dir}: {e}")

        if problems:
            return self.fail(
                "; ".join(problems),
                fix_kind="fs",
                fix_hint=(
                    "Перевірте права на теки:\n"
                    f"  ls -ld {cwd}\n"
                    f"  ls -ld {config_dir}"
                ),
                details="\n".join(problems),
            )

        return self.ok(
            f"CWD: {cwd.name}",
            details=(
                f"Робоча тека: {cwd}\n"
                f"Тека конфігурації: {config_dir}"
            ),
        )


class DiskSpaceCheck(Check):
    key = "fs.disk"
    name = "Вільне місце на диску"
    critical = False
    description = "Мінімум 100 МБ для тимчасових файлів."

    MIN_MB = 100

    def run(self, env: EnvInfo) -> CheckResult:
        try:
            usage = shutil.disk_usage(Path.cwd())
        except OSError as e:
            return self.warn(
                f"не вдалось перевірити: {e}",
                fix_kind="fs",
                fix_hint="Перевірте доступ до диска вручну: df -h",
            )

        free_mb = usage.free // (1024 * 1024)

        if free_mb < self.MIN_MB:
            return self.fail(
                f"{free_mb} МБ (потрібно ≥ {self.MIN_MB} МБ)",
                fix_kind="fs",
                fix_hint="Звільніть місце на диску: df -h",
                details=(
                    f"Вільно: {free_mb} МБ\n"
                    f"Потрібно: ≥ {self.MIN_MB} МБ\n"
                    "Місце потрібно для тимчасових PDF при обробці."
                ),
            )

        # < 500 МБ — попередження
        if free_mb < 500:
            return self.warn(
                f"{free_mb} МБ (мало, рекомендовано ≥ 500 МБ)",
                details=f"Вільно: {free_mb} МБ",
            )

        return self.ok(
            f"{free_mb} МБ вільно",
            details=f"Вільно: {free_mb} МБ",
        )
