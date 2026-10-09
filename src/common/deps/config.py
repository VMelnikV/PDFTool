"""Робота з ~/.config/pdf_tool/config.json.

Клас Config:
  * при першому створенні записує дефолтні значення у файл
  * читає/пише JSON
  * підтримує точкові ключі: "dependency_check.run_on_startup"

Приклад:
    cfg = Config()
    cfg.get("dependency_check.run_on_startup", True)   # True
    cfg.set("dependency_check.run_on_startup", False)  # зберігає одразу
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "pdf_tool"


def _config_file() -> Path:
    return _config_dir() / "config.json"


class Config:
    """Читання/запис config.json з точковими ключами."""

    # Дефолтні значення — записуються при першому створенні
    DEFAULTS: dict[str, Any] = {
        "dependency_check": {
            "run_on_startup": True,
        },
        "ui": {
            "language": None,   # None = мова системи
        },
    }

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _config_file()
        file_existed = self.path.exists()
        self.data: dict[str, Any] = self._load()

        # Якщо файл створюється вперше — записуємо дефолти
        if not file_existed:
            self.data = copy.deepcopy(self.DEFAULTS)
            self.save()

    # ── читання/запис файлу ─────────────────────────────────

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            text = self.path.read_text(encoding="utf-8")
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self) -> None:
        """Записує JSON. Створює теку за потреби. Атомарно через tmp."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(self.data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self.path)
        except OSError as e:
            # Не валимо GUI через проблеми з диском, але логуємо в stderr
            print(f"Warning: could not save config: {e}")

    # ── точкові ключі ───────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Читає значення за точковим ключем."""
        node: Any = self.data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        """Записує значення за точковим ключем і зберігає файл."""
        parts = key.split(".")
        node = self.data
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        self.save()

    # ── зручні методи ───────────────────────────────────────

    def get_language(self) -> str | None:
        return self.get("ui.language")

    def set_language(self, lang: str) -> None:
        self.set("ui.language", lang)

    def get_check_on_startup(self) -> bool:
        return bool(self.get("dependency_check.run_on_startup", True))

    def set_check_on_startup(self, value: bool) -> None:
        self.set("dependency_check.run_on_startup", bool(value))
