"""Unit-тести для common.deps.env.

Перевіряємо:
  * detect_env() повертає EnvInfo
  * kind у відомих значеннях
  * pep668 == False для venv/conda/pipx
  * distro у відомих значеннях або "unknown"
  * as_dict() серіалізується
  * get_env() кешує результат
"""

from __future__ import annotations

import sys

import pytest

# conftest.py додає src у sys.path
from common.deps.env import (
    EnvInfo,
    detect_distro,
    detect_env,
    detect_kind,
    detect_wsl,
    get_env,
    pep668_active,
)


# ─────────────────────────────────────────────────────────────
# detect_env
# ─────────────────────────────────────────────────────────────

def test_detect_env_returns_envinfo():
    env = detect_env()
    assert isinstance(env, EnvInfo)


def test_detect_env_kind_known():
    env = detect_env()
    assert env.kind in ("venv", "conda", "pipx", "system", "unknown")


def test_detect_env_platform_is_linux():
    env = detect_env()
    assert env.platform.startswith("linux")


def test_detect_env_python_version_is_tuple():
    env = detect_env()
    assert isinstance(env.python_version, tuple)
    assert len(env.python_version) == 3
    assert all(isinstance(x, int) for x in env.python_version)


def test_detect_env_distro_known():
    env = detect_env()
    assert env.distro in ("debian", "fedora", "arch", "suse", "unknown")


# ─────────────────────────────────────────────────────────────
# PEP 668 — головне правило
# ─────────────────────────────────────────────────────────────

def test_pep668_false_for_venv(monkeypatch):
    """У venv PEP 668 не застосовується — навіть якщо файл є."""
    monkeypatch.setattr(
        "common.deps.env.detect_kind",
        lambda: "venv",
    )
    monkeypatch.setattr(
        "common.deps.env.pep668_active",
        lambda: True,  # навіть якщо файл існує
    )
    env = detect_env()
    assert env.pep668 is False, "У venv pep668 має бути False"


def test_pep668_true_for_system(monkeypatch):
    """Для system — використовується реальна перевірка."""
    monkeypatch.setattr(
        "common.deps.env.detect_kind",
        lambda: "system",
    )
    monkeypatch.setattr(
        "common.deps.env.pep668_active",
        lambda: True,
    )
    env = detect_env()
    assert env.pep668 is True


def test_pep668_false_for_system_without_marker(monkeypatch):
    """Для system без маркера — False."""
    monkeypatch.setattr(
        "common.deps.env.detect_kind",
        lambda: "system",
    )
    monkeypatch.setattr(
        "common.deps.env.pep668_active",
        lambda: False,
    )
    env = detect_env()
    assert env.pep668 is False


# ─────────────────────────────────────────────────────────────
# display_name
# ─────────────────────────────────────────────────────────────

def test_display_name_no_pep668_in_venv(monkeypatch):
    monkeypatch.setattr("common.deps.env.detect_kind", lambda: "venv")
    monkeypatch.setattr("common.deps.env.pep668_active", lambda: True)
    env = detect_env()
    assert "PEP 668" not in env.display_name


def test_display_name_includes_pep668_for_system(monkeypatch):
    monkeypatch.setattr("common.deps.env.detect_kind", lambda: "system")
    monkeypatch.setattr("common.deps.env.pep668_active", lambda: True)
    env = detect_env()
    assert "PEP 668" in env.display_name


# ─────────────────────────────────────────────────────────────
# as_dict / can_autofix_pip
# ─────────────────────────────────────────────────────────────

def test_as_dict_is_json_serializable():
    import json

    env = detect_env()
    d = env.as_dict()
    assert isinstance(d, dict)
    # Перевірка серіалізації
    text = json.dumps(d, ensure_ascii=False)
    assert "kind" in text


def test_can_autofix_pip_in_venv():
    env = detect_env()
    if env.kind == "venv":
        assert env.can_autofix_pip is True


def test_can_autofix_pip_for_system_pep668(monkeypatch):
    """System + PEP 668 → НЕ можна автовстановлювати."""
    monkeypatch.setattr("common.deps.env.detect_kind", lambda: "system")
    monkeypatch.setattr("common.deps.env.pep668_active", lambda: True)
    monkeypatch.setattr(
        "common.deps.env.detect_is_writable",
        lambda: True,
    )
    env = detect_env()
    assert env.can_autofix_pip is False


# ─────────────────────────────────────────────────────────────
# get_env — кеш
# ─────────────────────────────────────────────────────────────

def test_get_env_is_cached():
    import common.deps.env as env_module

    # Скидаємо кеш
    env_module._cached_env = None

    env1 = get_env()
    env2 = get_env()
    assert env1 is env2, "get_env() має повертати той самий об'єкт"
