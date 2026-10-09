"""Перевірка оновлень pip-залежностей через PyPI JSON API.

Публічне API:
  * UpdateInfo               — інформація про один пакет
  * UpdateResult             — підсумок оновлення
  * check_package(pip_name)  — перевірка одного пакета
  * check_updates(packages)  — перевірка списку
  * run_updates(items, env, progress_cb) — запуск pip install -U

Особливості:
  * Без sudo — оновлення йде у поточне venv/conda/pipx
  * Помилки одного пакета не зупиняють інші
  * Пропонує альтернативні варіанти при помилці
  * Усі повідомлення локалізовано через translator.trf
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Iterable

from common.i18n.translator import translator

from .env import EnvInfo


# ─────────────────────────────────────────────────────────────
# Модель
# ─────────────────────────────────────────────────────────────

@dataclass
class UpdateInfo:
    """Інформація про один пакет.

    current:  поточна версія або None, якщо пакет не встановлено
    latest:   остання версія з PyPI або None, якщо не вдалось дізнатись
    """

    pip_name: str
    import_name: str
    current: str | None = None
    latest: str | None = None

    # Стан
    installed: bool = False
    outdated: bool = False
    install_needed: bool = False
    check_failed: str | None = None   # причина, якщо PyPI не відповів

    # Керування у UI
    selected: bool = True

    @property
    def needs_action(self) -> bool:
        return self.install_needed or self.outdated


@dataclass
class UpdateResult:
    """Підсумок оновлення."""

    installed: list[str] = field(default_factory=list)   # успішно встановлено
    updated: list[str] = field(default_factory=list)     # успішно оновлено
    failed: dict[str, str] = field(default_factory=dict) # name -> причина
    skipped: list[str] = field(default_factory=list)     # користувач не вибрав

    @property
    def any_success(self) -> bool:
        return bool(self.installed or self.updated)

    @property
    def any_failed(self) -> bool:
        return bool(self.failed)


# ─────────────────────────────────────────────────────────────
# Перевірка PyPI
# ─────────────────────────────────────────────────────────────

PYPI_URL = "https://pypi.org/pypi/{name}/json"
PYPI_TIMEOUT = 6  # секунд


def _fetch_latest(pip_name: str) -> tuple[str | None, str | None]:
    """Повертає (latest_version, error_message).

    latest_version = None, якщо пакет не знайдено або мережа недоступна.
    Повідомлення про помилки локалізовані через translator.trf.
    """
    url = PYPI_URL.format(name=pip_name)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "PDFTool/1.1"}
        )
        with urllib.request.urlopen(req, timeout=PYPI_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        info = data.get("info") or {}
        version = info.get("version")
        if isinstance(version, str):
            return version, None
        return None, translator.tr("bad_format", "updater")

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, translator.trf(
                "not_found_on_pypi", "updater", name=pip_name,
            )
        return None, translator.trf("http_error", "updater", code=e.code)

    except urllib.error.URLError as e:
        return None, translator.trf(
            "network_error", "updater", reason=e.reason,
        )

    except TimeoutError:
        return None, translator.tr("timeout", "updater")

    except json.JSONDecodeError:
        return None, translator.tr("bad_json", "updater")

    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def _get_installed_version(pip_name: str) -> str | None:
    """Поточна версія встановленого пакета."""
    try:
        import importlib.metadata as md

        return md.version(pip_name)
    except Exception:
        return None


def _version_older(current: str, latest: str) -> bool:
    """True, якщо current < latest."""
    try:
        from packaging.version import Version

        return Version(current) < Version(latest)
    except Exception:
        return current != latest


def check_package(pip_name: str, import_name: str) -> UpdateInfo:
    """Перевіряє один пакет: встановлено? актуально?"""
    info = UpdateInfo(pip_name=pip_name, import_name=import_name)

    # 1. Встановлено?
    current = _get_installed_version(pip_name)
    if current:
        info.installed = True
        info.current = current
    else:
        info.install_needed = True

    # 2. Остання версія з PyPI
    latest, err = _fetch_latest(pip_name)
    if err:
        info.check_failed = err
        return info
    info.latest = latest

    # 3. Порівняння
    if info.installed and current and latest:
        if _version_older(current, latest):
            info.outdated = True

    return info


def check_updates(
    packages: Iterable[tuple[str, str]],
) -> list[UpdateInfo]:
    """Перевіряє список пакетів.

    packages: iterable of (pip_name, import_name)
    """
    result: list[UpdateInfo] = []
    for pip_name, import_name in packages:
        result.append(check_package(pip_name, import_name))
    return result


# ─────────────────────────────────────────────────────────────
# Запуск оновлень
# ─────────────────────────────────────────────────────────────

ProgressCb = Callable[[int, int, str], None]


def _pip_install(
    pip_cmd: tuple[str, ...],
    pip_name: str,
    upgrade: bool,
) -> tuple[bool, str]:
    """Запускає pip install. Повертає (success, output).

    НЕ використовує sudo. Працює у поточному інтерпретаторі.
    """
    args = list(pip_cmd) + ["install"]
    if upgrade:
        args.append("--upgrade")
    args.append(pip_name)

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=300,  # 5 хв на пакет
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, translator.tr("install_timeout", "updater")
    except FileNotFoundError:
        return False, translator.tr("pip_not_found", "updater")
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"

    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.strip()


def build_failure_hint(
    pip_name: str,
    env: EnvInfo,
    output: str,
) -> str:
    """Пропонує альтернативи при помилці pip install.

    Враховує середовище, PEP 668, чи є інші способи.
    Заголовки локалізовано; команди — як є.
    """
    lines: list[str] = []
    low = output.lower()

    if "no matching distribution" in low or "not find a version" in low:
        lines.append(translator.tr("hint_no_match_header", "updater"))
        lines.append(f"    {' '.join(env.pip_cmd)} install --upgrade pip")

    elif "permission denied" in low or "externally-managed" in low:
        lines.append(translator.tr("hint_permission_header", "updater"))
        lines.append(f"    {env.python} -m venv .venv")
        lines.append("    source .venv/bin/activate")
        lines.append(f"    python -m pip install --upgrade {pip_name}")

    elif "network" in low or "connection" in low or "timed out" in low:
        lines.append(translator.tr("hint_network_header", "updater"))
        lines.append(f"    pip install --no-cache-dir {pip_name}")
        lines.append(
            f"    pip install --index-url https://pypi.org/simple/ {pip_name}"
        )

    else:
        lines.append(translator.tr("hint_generic_header", "updater"))
        lines.append(
            f"    1. {' '.join(env.pip_cmd)} install -U pip"
        )
        lines.append("    2. " + translator.tr(
            "not_found_on_pypi", "updater", name=pip_name
        ).replace(pip_name, f"<{pip_name}>"))
        lines.append(
            f"       {env.python} -m pip install -U "
            f"--index-url https://pypi.org/simple/ {pip_name}"
        )
        lines.append("    3. " + translator.tr(
            "hint_generic_header", "updater"
        ))

    if env.pep668 and env.kind == "system":
        lines.append("")
        lines.append(translator.tr("hint_pep668_warning", "updater"))

    return "\n".join(lines)


def run_updates(
    items: list[UpdateInfo],
    env: EnvInfo,
    progress_cb: ProgressCb | None = None,
) -> UpdateResult:
    """Виконує pip install для обраних items.

    items: список UpdateInfo з selected=True.
    Усі помилки збираються у result.failed; інші пакети продовжують.
    """
    result = UpdateResult()
    selected = [it for it in items if it.selected and it.needs_action]
    total = len(selected)

    if total == 0:
        return result

    for i, info in enumerate(selected, start=1):
        if progress_cb:
            progress_cb(i, total, info.pip_name)

        upgrade = info.installed  # якщо вже стоїть — оновлюємо, інакше — ставимо
        ok, output = _pip_install(env.pip_cmd, info.pip_name, upgrade=upgrade)

        if ok:
            if info.install_needed:
                result.installed.append(info.pip_name)
            else:
                result.updated.append(info.pip_name)
        else:
            hint = build_failure_hint(info.pip_name, env, output)
            result.failed[info.pip_name] = (
                f"{output}\n\n--- {translator.tr('hint_generic_header', 'updater')} ---\n{hint}"
            )

    return result
