"""Реєстр усіх перевірок.

Порядок у списку визначає порядок виконання і порядок рядків у UI.
Перевірки з critical=True блокують запуск при FAIL.
"""

from __future__ import annotations

from .base import Check
from .config_check import ConfigCheck
from .external_check import ExternalCheck
from .fs_check import DiskSpaceCheck, WriteAccessCheck
from .lib_check import LibCheck
from .locale_check import LocaleCheck
from .pep668_check import PEP668Check
from .platform_check import PlatformCheck
from .pyside_check import PySideCheck
from .python_check import PythonVersionCheck
from .wsl_check import WSLCheck

CHECKS: list[Check] = [
    # ─── Система та інтерпретатор ───────────────────────────
    PlatformCheck(),
    PythonVersionCheck(),
    WSLCheck(),
    PEP668Check(),

    # ─── GUI ────────────────────────────────────────────────
    PySideCheck(),

    # ─── Python-бібліотеки ──────────────────────────────────
    LibCheck(
        "Pillow",
        import_name="PIL",
        display_name="Pillow (PIL)",
        min_version="10.0.0",
        critical=True,
        docs_url="https://pillow.readthedocs.io/",
        description="Робота із зображеннями (конвертація у PDF).",
    ),
    LibCheck(
        "pypdf",
        display_name="pypdf",
        min_version="3.0.0",
        critical=True,
        docs_url="https://pypdf.readthedocs.io/",
        description="Маніпуляції з PDF (об'єднання, розділення).",
    ),
    LibCheck(
        "PyPDFForm",
        display_name="PyPDFForm",
        min_version="1.0.0",
        critical=True,
        docs_url="https://github.com/chinapandaman/PyPDFForm",
        description="Заповнення PDF-форм.",
    ),
    LibCheck(
        "pdf2image",
        display_name="pdf2image",
        min_version="1.16.0",
        critical=True,
        docs_url="https://github.com/Belval/pdf2image",
        description="Конвертація PDF-сторінок у зображення (потребує poppler-utils).",
    ),

    # ─── Системні утиліти ───────────────────────────────────
    ExternalCheck(
        "gs",
        display_name="Ghostscript",
        critical=True,
        docs_url="https://www.ghostscript.com/",
        description="Стиснення PDF (профілі Екран / Електронна книга / Друк).",
    ),
    ExternalCheck(
        "pdftoppm",
        display_name="Poppler (pdftoppm)",
        critical=True,
        docs_url="https://poppler.freedesktop.org/",
        description="Рендер PDF-сторінок у зображення (використовується pdf2image).",
    ),

    # ─── Файлова система ────────────────────────────────────
    WriteAccessCheck(),
    DiskSpaceCheck(),

    # ─── Конфігурація та локалізація ────────────────────────
    ConfigCheck(),
    LocaleCheck(),
]


def register(check: Check) -> None:
    """Додає перевірку в реєстр (для ручного розширення)."""
    CHECKS.append(check)


def get_checks() -> list[Check]:
    """Повертає список усіх зареєстрованих перевірок."""
    return list(CHECKS)
