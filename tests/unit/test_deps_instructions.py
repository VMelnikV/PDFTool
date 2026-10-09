"""Unit-тести для common.deps.instructions.

Перевіряємо:
  * strip_sudo — базові випадки, з відступами, з коментарями
  * has_sudo — детекція команд sudo
  * pip_install_instructions — для venv/system/conda/pipx
  * external_install_instructions — для gs на різних дистрибутивах
"""

from __future__ import annotations

import pytest

from common.deps.env import EnvInfo
from common.deps.instructions import (
    SUDO_NOTE,
    SUDO_NOTE_CLI,
    external_install_instructions,
    has_sudo,
    pip_install_instructions,
    strip_sudo,
)


# ─────────────────────────────────────────────────────────────
# Допоміжне
# ─────────────────────────────────────────────────────────────

def _make_env(
    kind: str = "venv",
    *,
    pep668: bool = False,
    distro: str = "debian",
    is_writable: bool = True,
) -> EnvInfo:
    return EnvInfo(
        kind=kind,
        python="/usr/bin/python3",
        pip_cmd=("/usr/bin/python3", "-m", "pip"),
        is_writable=is_writable,
        distro=distro,
        is_wsl=False,
        wsl_version=None,
        pep668=pep668,
        platform="linux",
        python_version=(3, 12, 0),
    )


# ─────────────────────────────────────────────────────────────
# strip_sudo
# ─────────────────────────────────────────────────────────────

def test_strip_sudo_simple():
    assert strip_sudo("sudo apt install gs") == "apt install gs"


def test_strip_sudo_with_indent():
    assert strip_sudo("    sudo apt install gs") == "    apt install gs"


def test_strip_sudo_multiline():
    text = "sudo apt install gs\nsudo apt install qpdf"
    assert strip_sudo(text) == "apt install gs\napt install qpdf"


def test_strip_sudo_keeps_comments():
    text = "# sudo not touched\nsudo apt install gs"
    result = strip_sudo(text)
    assert "# sudo not touched" in result
    assert "apt install gs" in result
    assert "sudo apt install gs" not in result


def test_strip_sudo_no_sudo():
    text = "apt install gs"
    assert strip_sudo(text) == text


def test_strip_sudo_empty():
    assert strip_sudo("") == ""


# ─────────────────────────────────────────────────────────────
# has_sudo
# ─────────────────────────────────────────────────────────────

def test_has_sudo_true():
    assert has_sudo("sudo apt install gs") is True


def test_has_sudo_true_with_indent():
    assert has_sudo("    sudo apt install gs") is True


def test_has_sudo_false():
    assert has_sudo("apt install gs") is False


def test_has_sudo_ignores_comments():
    assert has_sudo("# sudo apt install gs") is False


# ─────────────────────────────────────────────────────────────
# pip_install_instructions
# ─────────────────────────────────────────────────────────────

def test_pip_instructions_for_venv():
    env = _make_env("venv")
    text = pip_install_instructions("pypdf", env)
    assert "python3" in text
    assert "-m pip install pypdf" in text
    assert "venv" in text.lower()


def test_pip_instructions_for_venv_with_min_version():
    env = _make_env("venv")
    text = pip_install_instructions("pypdf", env, min_version="3.0.0")
    assert "pypdf>=3.0.0" in text


def test_pip_instructions_for_system_pep668_mentions_break_system():
    env = _make_env("system", pep668=True, is_writable=False)
    text = pip_install_instructions("pypdf", env)
    assert "--break-system-packages" in text
    assert "PEP 668" in text


def test_pip_instructions_for_system_no_pep668():
    env = _make_env("system", pep668=False, is_writable=True)
    text = pip_install_instructions("pypdf", env)
    assert "--break-system-packages" not in text


def test_pip_instructions_for_conda():
    env = _make_env("conda")
    text = pip_install_instructions("pypdf", env)
    assert "conda install" in text
    assert "pypdf" in text


def test_pip_instructions_for_pipx():
    env = _make_env("pipx")
    text = pip_install_instructions("pypdf", env)
    assert "pipx install pypdf" in text


# ─────────────────────────────────────────────────────────────
# external_install_instructions
# ─────────────────────────────────────────────────────────────

def test_external_gs_debian():
    env = _make_env(distro="debian")
    text = external_install_instructions("gs", env)
    assert "apt install ghostscript" in text
    assert "Debian" in text


def test_external_gs_fedora():
    env = _make_env(distro="fedora")
    text = external_install_instructions("gs", env)
    assert "dnf install ghostscript" in text


def test_external_gs_arch():
    env = _make_env(distro="arch")
    text = external_install_instructions("gs", env)
    assert "pacman -S ghostscript" in text


def test_external_pdftoppm_debian():
    env = _make_env(distro="debian")
    text = external_install_instructions("pdftoppm", env)
    assert "poppler-utils" in text


# ─────────────────────────────────────────────────────────────
# Константи
# ─────────────────────────────────────────────────────────────

def test_sudo_note_not_empty():
    assert SUDO_NOTE
    assert SUDO_NOTE_CLI
    assert "sudo" in SUDO_NOTE.lower()
