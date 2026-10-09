"""Детекція середовища виконання PDF Tool.

Модуль визначає:
  * Тип Python-середовища (venv / conda / pipx / system)
  * Шлях до інтерпретатора та правильну команду pip
  * Права на запис у поточне середовище
  * Дистрибутив Linux (debian / fedora / arch / suse / unknown)
  * Наявність WSL (і версію)
  * Активність PEP 668 (externally-managed-environment)

Важливо: PEP 668 застосовується ЛИШЕ до системного Python.
У venv / conda / pipx маркер ігнорується, бо ці середовища
створені саме для встановлення пакетів без обмежень.

Результат — єдиний імутабельний об'єкт EnvInfo, який передається
в усі перевірки та в генератор інструкцій.
"""

from __future__ import annotations

import os
import platform
import sys
import sysconfig
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

EnvKind = Literal["venv", "conda", "pipx", "system", "unknown"]
Distro = Literal["debian", "fedora", "arch", "suse", "unknown"]


# ─────────────────────────────────────────────────────────────
# Публічна модель
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EnvInfo:
    """Інформація про середовище виконання.

    Створюється один раз через detect_env() і передається як аргумент.
    Імутабельний (frozen=True) — щоб випадково не змінити в перевірках.
    """

    kind: EnvKind
    python: str                         # sys.executable
    pip_cmd: tuple[str, ...]            # напр. ("/path/python", "-m", "pip")
    is_writable: bool                   # чи можна ставити без sudo
    distro: Distro
    is_wsl: bool
    wsl_version: int | None             # 1 або 2
    pep668: bool                        # externally-managed marker (тільки system)
    platform: str                       # sys.platform ("linux")
    python_version: tuple[int, int, int]

    # Додаткові поля для відображення (не впливають на логіку)
    display_name: str = field(default="")

    def __post_init__(self) -> None:
        # Заповнюємо display_name, якщо порожній
        if not self.display_name:
            object.__setattr__(self, "display_name", self._make_display_name())

    def _make_display_name(self) -> str:
        """Людяна назва середовища для UI."""
        base = {
            "venv": "venv",
            "conda": "conda",
            "pipx": "pipx",
            "system": "system",
            "unknown": "unknown",
        }.get(self.kind, "unknown")

        extras: list[str] = []
        if self.is_wsl:
            extras.append(f"WSL{self.wsl_version or ''}")
        # PEP 668 показуємо ТІЛЬКИ для system (у venv він не застосовується)
        if self.pep668 and self.kind == "system":
            extras.append("PEP 668")

        if extras:
            return f"{base} ({', '.join(extras)})"
        return base

    @property
    def python_version_str(self) -> str:
        return ".".join(str(x) for x in self.python_version)

    @property
    def can_autofix_pip(self) -> bool:
        """Чи можна запускати pip install без sudo."""
        if self.kind == "system":
            return self.is_writable and not self.pep668
        return True  # venv / conda / pipx — завжди можна

    def as_dict(self) -> dict:
        """Для JSON-серіалізації в CLI --json."""
        return {
            "kind": self.kind,
            "python": self.python,
            "pip_cmd": list(self.pip_cmd),
            "is_writable": self.is_writable,
            "distro": self.distro,
            "is_wsl": self.is_wsl,
            "wsl_version": self.wsl_version,
            "pep668": self.pep668,
            "platform": self.platform,
            "python_version": self.python_version_str,
            "display_name": self.display_name,
        }


# ─────────────────────────────────────────────────────────────
# Детектори
# ─────────────────────────────────────────────────────────────

def detect_kind() -> EnvKind:
    """Визначає тип Python-середовища."""
    # pipx виставляє ці змінні
    if os.environ.get("PIPX_HOME") or os.environ.get("PIPX_BIN_DIR"):
        return "pipx"

    # conda
    if os.environ.get("CONDA_PREFIX") or os.environ.get("CONDA_DEFAULT_ENV"):
        return "conda"

    # venv / virtualenv
    if sys.prefix != sys.base_prefix:
        return "venv"

    # якщо VIRTUAL_ENV вказує на теку — це venv
    if os.environ.get("VIRTUAL_ENV"):
        return "venv"

    return "system"


def detect_is_writable() -> bool:
    """Чи можна писати в site-packages без sudo."""
    try:
        purelib = sysconfig.get_path("purelib")
        if not purelib:
            return False
        p = Path(purelib)
        if not p.exists():
            return False
        # Пробуємо створити тимчасовий файл
        test = p / ".pdf_tool_write_test"
        try:
            test.touch()
            test.unlink()
            return True
        except (OSError, PermissionError):
            return False
    except Exception:
        return False


def detect_distro() -> Distro:
    """Визначає дистрибутив Linux через platform.freedesktop_os_release().

    Потребує Python 3.10+. Якщо недоступно — повертає 'unknown'.
    Без ручного парсингу /etc/os-release.
    """
    try:
        rel = platform.freedesktop_os_release()
    except (OSError, AttributeError):
        return "unknown"

    ids: set[str] = set()
    if rel.get("ID"):
        ids.add(rel["ID"].lower())
    if rel.get("ID_LIKE"):
        ids.update(rel["ID_LIKE"].lower().split())

    if ids & {"debian", "ubuntu", "linuxmint", "pop", "elementary", "zorin"}:
        return "debian"
    if ids & {"fedora", "rhel", "centos", "rocky", "almalinux"}:
        return "fedora"
    if ids & {"arch", "manjaro", "endeavouros", "garuda"}:
        return "arch"
    if ids & {"opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed"}:
        return "suse"

    return "unknown"


def detect_wsl() -> tuple[bool, int | None]:
    """Визначає, чи це WSL, і якої версії.

    Повертає (is_wsl, version). version: 1, 2 або None.
    """
    try:
        with open("/proc/version", encoding="utf-8", errors="ignore") as f:
            v = f.read().lower()
    except OSError:
        return False, None

    if "microsoft" not in v and "wsl" not in v:
        return False, None

    if "wsl2" in v:
        return True, 2
    # У WSL1 зазвичай "microsoft" без "wsl2"
    return True, 1


def pep668_active() -> bool:
    """Чи активний маркер externally-managed (PEP 668).

    Перевіряє наявність файлу EXTERNALLY-MANAGED у stdlib.
    Увага: у venv sysconfig.get_path('stdlib') вказує на системну
    теку базового Python, тому перевірка має сенс ТІЛЬКИ для
    системного Python. Це враховується в detect_env().
    """
    try:
        stdlib = sysconfig.get_path("stdlib")
        if not stdlib:
            return False
        return (Path(stdlib) / "EXTERNALLY-MANAGED").exists()
    except Exception:
        return False


def detect_pip_cmd() -> tuple[str, ...]:
    """Повертає правильну команду pip для поточного інтерпретатора."""
    return (sys.executable, "-m", "pip")


def detect_python_version() -> tuple[int, int, int]:
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


# ─────────────────────────────────────────────────────────────
# Головна функція
# ─────────────────────────────────────────────────────────────

def detect_env() -> EnvInfo:
    """Створює EnvInfo для поточного процесу.

    Викликати один раз при старті, результат передавати далі.

    PEP 668 перевіряється лише для системного Python: у venv/conda/pipx
    цей маркер не застосовується, бо там pip install дозволено завжди.
    """
    kind = detect_kind()
    is_wsl, wsl_ver = detect_wsl()

    # PEP 668 — тільки для system
    pep668 = False
    if kind == "system":
        pep668 = pep668_active()

    return EnvInfo(
        kind=kind,
        python=sys.executable,
        pip_cmd=detect_pip_cmd(),
        is_writable=detect_is_writable(),
        distro=detect_distro(),
        is_wsl=is_wsl,
        wsl_version=wsl_ver,
        pep668=pep668,
        platform=sys.platform,
        python_version=detect_python_version(),
    )


# ─────────────────────────────────────────────────────────────
# Кешований доступ (для використання в різних місцях)
# ─────────────────────────────────────────────────────────────

_cached_env: EnvInfo | None = None


def get_env() -> EnvInfo:
    """Повертає кешований EnvInfo (створює при першому виклику)."""
    global _cached_env
    if _cached_env is None:
        _cached_env = detect_env()
    return _cached_env


# ─────────────────────────────────────────────────────────────
# CLI для швидкої перевірки
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    env = detect_env()
    print(json.dumps(env.as_dict(), indent=2, ensure_ascii=False))
