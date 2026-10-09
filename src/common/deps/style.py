"""Спільні стилі для tkinter, PySide6 і CLI.

Визначає:
  * Іконки статусів (✅ ⚠️ ❌ ⏳ •)
  * Кольори статусів (однакові в усіх UI)
  * Правило «критичне — жирним»
  * Бейджі «критично» / «опційно»
  * Функції для форматування рядків

Усі UI імпортують цей модуль, щоб мати однакову візуальну мову.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .report import CheckResult


# ─────────────────────────────────────────────────────────────
# Статуси
# ─────────────────────────────────────────────────────────────

class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


# ─────────────────────────────────────────────────────────────
# Іконки (юнікод — працює у всіх трьох UI)
# ─────────────────────────────────────────────────────────────

STATUS_ICONS: dict[Status, str] = {
    Status.PENDING: "•",
    Status.RUNNING: "⏳",
    Status.OK: "✅",
    Status.WARN: "⚠️",
    Status.FAIL: "❌",
}


# ─────────────────────────────────────────────────────────────
# Кольори (hex — сумісні з tkinter, Qt, ANSI)
# ─────────────────────────────────────────────────────────────

COLOR_OK = "#2e7d32"       # зелений
COLOR_WARN = "#f9a825"     # жовтий
COLOR_FAIL = "#c62828"     # червоний
COLOR_PENDING = "#757575"  # сірий
COLOR_TEXT = "#212121"     # основний текст
COLOR_MUTED = "#757575"    # другорядний текст
COLOR_BADGE_CRITICAL = "#c62828"
COLOR_BADGE_OPTIONAL = "#757575"

STATUS_COLORS: dict[Status, str] = {
    Status.PENDING: COLOR_PENDING,
    Status.RUNNING: COLOR_PENDING,
    Status.OK: COLOR_OK,
    Status.WARN: COLOR_WARN,
    Status.FAIL: COLOR_FAIL,
}


# ─────────────────────────────────────────────────────────────
# ANSI-коди для CLI (коли термінал підтримує колір)
# ─────────────────────────────────────────────────────────────

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_GRAY = "\033[90m"

ANSI_STATUS_COLORS: dict[Status, str] = {
    Status.PENDING: ANSI_GRAY,
    Status.RUNNING: ANSI_GRAY,
    Status.OK: ANSI_GREEN,
    Status.WARN: ANSI_YELLOW,
    Status.FAIL: ANSI_RED,
}


# ─────────────────────────────────────────────────────────────
# Бейджі
# ─────────────────────────────────────────────────────────────

BADGE_CRITICAL = "критично"
BADGE_OPTIONAL = "опційно"


class FontWeight(str, Enum):
    NORMAL = "normal"
    BOLD = "bold"


def row_weight(result: "CheckResult") -> FontWeight:
    """Критичні перевірки — жирним, решта — звичайним."""
    return FontWeight.BOLD if result.critical else FontWeight.NORMAL


def is_bold(result: "CheckResult") -> bool:
    """Зручний булевий варіант для UI."""
    return result.critical


def row_badge(result: "CheckResult") -> str:
    """Текст бейджа: 'критично' або 'опційно'."""
    return BADGE_CRITICAL if result.critical else BADGE_OPTIONAL


def row_badge_color(result: "CheckResult") -> str:
    """Колір бейджа (hex)."""
    return COLOR_BADGE_CRITICAL if result.critical else COLOR_BADGE_OPTIONAL


# ─────────────────────────────────────────────────────────────
# Форматування рядка
# ─────────────────────────────────────────────────────────────

def format_message(result: "CheckResult") -> str:
    """Повертає 'name: message' для відображення в UI."""
    if result.message:
        return f"{result.name}: {result.message}"
    return result.name


def format_row_plain(result: "CheckResult") -> str:
    """Простий текстовий рядок без ANSI (для логів і файлів)."""
    icon = STATUS_ICONS.get(result.status, "?")
    badge = row_badge(result)
    return f"{icon}  {format_message(result)}  [{badge}]"


def format_row_cli(
    result: "CheckResult",
    use_ansi: bool = True,
    name_width: int = 40,
) -> str:
    """Рядок для CLI з ANSI-кольорами та жирним для критичних.

    use_ansi: False — коли NO_COLOR=1 або вивід не в TTY.
    """
    icon = STATUS_ICONS.get(result.status, "?")
    badge = row_badge(result)
    msg = format_message(result)

    if not use_ansi:
        return f"{icon}  {msg:<{name_width}}  [{badge}]"

    color = ANSI_STATUS_COLORS.get(result.status, "")
    badge_color = ANSI_RED if result.critical else ANSI_GRAY

    icon_s = f"{color}{icon}{ANSI_RESET}"

    if result.critical:
        msg_s = f"{ANSI_BOLD}{msg:<{name_width}}{ANSI_RESET}"
        badge_s = f"{ANSI_BOLD}{badge_color}[{badge}]{ANSI_RESET}"
    else:
        msg_s = f"{msg:<{name_width}}"
        badge_s = f"{badge_color}[{badge}]{ANSI_RESET}"

    return f"{icon_s}  {msg_s}  {badge_s}"


# ─────────────────────────────────────────────────────────────
# Утиліти
# ─────────────────────────────────────────────────────────────

def supports_ansi() -> bool:
    """Чи підтримує поточний термінал ANSI-кольори."""
    import os
    import sys

    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM", "").lower() in ("dumb", ""):
        return False
    return True


def supports_unicode_icons() -> bool:
    """Чи можна показувати емодзі (✅ ⚠️ ❌)."""
    import os
    import sys

    # Windows cmd.exe — краще не показувати
    if sys.platform == "win32":
        return False

    # Відсутність UTF-8 у локалі — ризик
    enc = (sys.stdout.encoding or "").lower()
    if "utf" not in enc:
        return False

    # У деяких мінімальних Linux-консолях емодзі не рендеряться
    if os.environ.get("TERM", "") == "linux":
        return False

    return True


# ─────────────────────────────────────────────────────────────
# Приклад використання
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Демонстрація (без реального CheckResult)
    print("Іконки:", {s.name: STATUS_ICONS[s] for s in Status})
    print("Кольори:", {s.name: STATUS_COLORS[s] for s in Status})
    print("ANSI:", supports_ansi())
    print("Unicode:", supports_unicode_icons())
