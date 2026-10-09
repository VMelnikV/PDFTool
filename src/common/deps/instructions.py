"""Генерація інструкцій для встановлення залежностей.

Особливості:
  * Враховує тип середовища (venv / conda / pipx / system)
  * Враховує дистрибутив Linux (debian / fedora / arch / suse)
  * Враховує PEP 668 (--break-system-packages)
  * strip_sudo() — копіювання завжди без sudo (безпечніше)
  * has_sudo() — чи є в тексті команди з sudo (для показу примітки)

Публічні функції:
  pip_install_instructions(pkg, env, min_version=None) -> str
  external_install_instructions(tool, env) -> str
  strip_sudo(text) -> str
  has_sudo(text) -> bool
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .env import EnvInfo


# ─────────────────────────────────────────────────────────────
# Метадані зовнішніх утиліт
# ─────────────────────────────────────────────────────────────

EXTERNAL_PACKAGES: dict[str, dict[str, str]] = {
    "gs": {
        "debian": "ghostscript",
        "fedora": "ghostscript",
        "arch": "ghostscript",
        "suse": "ghostscript",
    },
    "pdftoppm": {
        "debian": "poppler-utils",
        "fedora": "poppler-utils",
        "arch": "poppler",
        "suse": "poppler-tools",
    },
    "qpdf": {
        "debian": "qpdf",
        "fedora": "qpdf",
        "arch": "qpdf",
        "suse": "qpdf",
    },
    "tesseract": {
        "debian": "tesseract-ocr",
        "fedora": "tesseract",
        "arch": "tesseract",
        "suse": "tesseract-ocr",
    },
}

# Дружні назви для відображення
EXTERNAL_DISPLAY_NAMES: dict[str, str] = {
    "gs": "Ghostscript",
    "pdftoppm": "Poppler (pdftoppm)",
    "qpdf": "qpdf",
    "tesseract": "Tesseract OCR",
}


# ─────────────────────────────────────────────────────────────
# Хелпери для дистрибутивів
# ─────────────────────────────────────────────────────────────

def _pkg_install_cmd(distro: str, pkg: str) -> str:
    """Повертає команду встановлення пакета для дистрибутива."""
    return {
        "debian": f"sudo apt install {pkg}",
        "fedora": f"sudo dnf install {pkg}",
        "arch":   f"sudo pacman -S {pkg}",
        "suse":   f"sudo zypper install {pkg}",
    }.get(distro, f"<ваш пакетний менеджер> install {pkg}")


def _distro_pretty(distro: str) -> str:
    return {
        "debian": "Debian / Ubuntu / Linux Mint",
        "fedora": "Fedora / RHEL / CentOS",
        "arch":   "Arch / Manjaro",
        "suse":   "openSUSE / SUSE",
    }.get(distro, "невідомий дистрибутив")


# ─────────────────────────────────────────────────────────────
# pip-пакети
# ─────────────────────────────────────────────────────────────

def pip_install_instructions(
    pkg: str,
    env: "EnvInfo",
    min_version: str | None = None,
) -> str:
    """Генерує інструкцію для встановлення pip-пакета.

    Враховує тип середовища та PEP 668.
    """
    spec = f"{pkg}>={min_version}" if min_version else pkg
    lines: list[str] = [
        f"Середовище: {env.kind}",
        f"Python:     {env.python}",
    ]

    if env.pep668:
        lines.append("PEP 668:    активний (externally-managed-environment)")

    lines.append("")

    if env.kind == "venv":
        lines += [
            "Встановити у поточне venv:",
            f"    {env.python} -m pip install {spec}",
        ]

    elif env.kind == "conda":
        lines += [
            "Встановити через conda (рекомендовано):",
            f"    conda install -y {pkg}",
            "",
            "Або через pip у поточне conda-середовище:",
            f"    {env.python} -m pip install {spec}",
        ]

    elif env.kind == "pipx":
        lines += [
            "Встановити через pipx:",
            f"    pipx install {pkg}",
        ]

    else:  # system
        if env.pep668:
            lines += [
                "⚠️  PEP 668 блокує глобальний pip install, щоб не",
                "    зламати системні пакети. Варіант 3 вимагає",
                "    --break-system-packages і робить це на ваш ризик.",
                "",
            ]

        lines += [
            "Варіант 1 — створити venv (рекомендовано):",
            f"    {env.python} -m venv .venv",
            "    source .venv/bin/activate",
            f"    python -m pip install {spec}",
            "",
            "Варіант 2 — встановити через pipx:",
            "    sudo apt install pipx       # або відповідний менеджер",
            f"    pipx install {pkg}",
            "",
            "Варіант 3 — глобально через pip (на власний ризик):",
        ]

        if env.pep668:
            lines.append(
                f"    {env.python} -m pip install "
                f"--break-system-packages {spec}"
            )
        else:
            lines.append(f"    {env.python} -m pip install {spec}")

    if min_version:
        lines += [
            "",
            "Оновити, якщо вже встановлено старішу версію:",
            f'    {env.python} -m pip install -U "{spec}"',
        ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Зовнішні утиліти
# ─────────────────────────────────────────────────────────────

def external_install_instructions(tool: str, env: "EnvInfo") -> str:
    """Генерує інструкцію для системної утиліти."""
    display = EXTERNAL_DISPLAY_NAMES.get(tool, tool)
    pkgs = EXTERNAL_PACKAGES.get(tool)

    lines: list[str] = [
        f"Утиліта: {display}",
        f"Дистрибутив: {_distro_pretty(env.distro)}",
        "",
    ]

    if pkgs:
        pkg = pkgs.get(env.distro, tool)
        lines += [
            "Встановити через пакетний менеджер:",
            f"    {_pkg_install_cmd(env.distro, pkg)}",
        ]
    else:
        lines.append(
            "Встановіть відповідний пакет для вашої системи "
            "(назва може відрізнятись)."
        )

    lines += [
        "",
        "Перевірка після встановлення:",
        f"    {tool} --version",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# sudo-обробка (для безпечного копіювання)
# ─────────────────────────────────────────────────────────────

def has_sudo(text: str) -> bool:
    """Чи є в тексті команди з sudo (у рядках, що не є коментарями)."""
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith("sudo "):
            return True
    return False


def strip_sudo(text: str) -> str:
    """Прибирає 'sudo ' на початку кожного рядка (з урахуванням відступів).

    Коментарі (# ...) не чіпає.
    Приклади:
        'sudo apt install gs'       -> 'apt install gs'
        '    sudo apt install gs'   -> '    apt install gs'
        '# sudo apt install gs'     -> без змін
    """
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        if stripped.startswith("#"):
            out.append(line)
            continue

        if stripped.startswith("sudo "):
            line = indent + stripped[len("sudo "):]

        out.append(line)

    return "\n".join(out)


# ─────────────────────────────────────────────────────────────
# Примітка про sudo (для UI і CLI)
# ─────────────────────────────────────────────────────────────

SUDO_NOTE = (
    "ⓘ Копіюється без «sudo». Якщо потрібні root-права — "
    "додайте «sudo» вручну в терміналі."
)

SUDO_NOTE_CLI = (
    "ⓘ Якщо копіюєте команди — приберіть «sudo», "
    "якщо не маєте root-прав у поточному сеансі."
)


# ─────────────────────────────────────────────────────────────
# Демонстрація
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from .env import detect_env

    env = detect_env()
    print("=== Env ===")
    print(f"kind={env.kind}  distro={env.distro}  "
          f"pep668={env.pep668}  writable={env.is_writable}")
    print()

    print("=== pip: PyPDFForm (system, PEP 668) ===")
    print(pip_install_instructions("PyPDFForm", env))
    print()

    print("=== external: Ghostscript ===")
    print(external_install_instructions("gs", env))
    print()

    print("=== strip_sudo демо ===")
    sample = "sudo apt install ghostscript\n# sudo not touched\necho done"
    print("Було:")
    print(sample)
    print("Стало:")
    print(strip_sudo(sample))
