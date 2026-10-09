"""CLI-вивід результатів перевірки залежностей.

Використовується, коли:
  * немає ні PySide6, ні tkinter
  * користувач явно вибрав --ui=cli
  * запуск з --check-only (для CI та розробки)

Особливості:
  * ANSI-кольори (якщо підтримує термінал)
  * Жирний шрифт для критичних перевірок
  * Під FAIL/WARN — інструкція + примітка про sudo
  * Підсумковий рядок
  * Exit codes: 0 — OK, 1 — некритичні, 2 — критичні
"""

from __future__ import annotations

import json
import sys
from typing import TextIO

from ..instructions import SUDO_NOTE_CLI, has_sudo, strip_sudo
from ..report import CheckReport
from ..style import (
    ANSI_BOLD,
    ANSI_RESET,
    Status,
    format_row_cli,
    supports_ansi,
    supports_unicode_icons,
)
from .base import DependencyWindowBase, DialogResult


# ─────────────────────────────────────────────────────────────
# Рендер одного результату
# ─────────────────────────────────────────────────────────────

def render_result(
    result,
    *,
    use_ansi: bool,
    show_instructions: bool = True,
    indent: str = "    ",
) -> str:
    """Рендерить один CheckResult у текстовий блок.

    Для FAIL/WARN додає install_instructions і (за потреби) примітку про sudo.
    """
    lines: list[str] = [format_row_cli(result, use_ansi=use_ansi)]

    if not show_instructions or not result.needs_attention:
        return "\n".join(lines)

    if result.install_instructions:
        instr = result.install_instructions
        for line in instr.splitlines():
            lines.append(f"{indent}{line}")

        if has_sudo(instr):
            lines.append("")
            lines.append(f"{indent}{SUDO_NOTE_CLI}")

    if result.docs_url:
        lines.append("")
        lines.append(f"{indent}Документація: {result.docs_url}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Рендер всього звіту
# ─────────────────────────────────────────────────────────────

def render_report(
    report: CheckReport,
    *,
    use_ansi: bool | None = None,
    show_instructions: bool = True,
    show_env: bool = False,
) -> str:
    """Рендерить повний звіт для терміналу."""
    if use_ansi is None:
        use_ansi = supports_ansi()

    lines: list[str] = []

    # Заголовок
    if use_ansi:
        lines.append(f"{ANSI_BOLD}PDF Tool — перевірка залежностей{ANSI_RESET}")
    else:
        lines.append("PDF Tool — перевірка залежностей")
    lines.append("─" * 60)

    # Опційно: середовище
    if show_env and report.env:
        env = report.env
        lines.append(f"Середовище: {env.display_name}")
        lines.append(f"Python:     {env.python}")
        lines.append(f"Дистрибутив: {env.distro}")
        lines.append("─" * 60)

    # Перевірки
    for result in report.results:
        lines.append(render_result(
            result,
            use_ansi=use_ansi,
            show_instructions=show_instructions,
        ))

    lines.append("─" * 60)

    # Підсумок
    c = report.counts()
    summary_parts = [f"OK: {c['ok']}"]
    if c["warn"]:
        summary_parts.append(f"попереджень: {c['warn']}")
    if c["fail"]:
        summary_parts.append(f"помилок: {c['fail']}")
    if c["critical_fail"]:
        summary_parts.append(f"критичних: {c['critical_fail']}")

    summary = "  |  ".join(summary_parts)

    if use_ansi:
        if c["critical_fail"]:
            summary = f"{ANSI_BOLD}{summary}{ANSI_RESET}"
        lines.append(summary)
    else:
        lines.append(summary)

    # Статус
    if report.all_critical_ok:
        lines.append("✅ Можна запускати застосунок.")
    else:
        lines.append("❌ Запуск заблоковано: є критичні помилки.")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Публічний запуск
# ─────────────────────────────────────────────────────────────

def run_cli_report(
    report: CheckReport,
    *,
    json_mode: bool = False,
    strict: bool = False,
    show_instructions: bool = True,
    show_env: bool = False,
    stream: TextIO | None = None,
) -> int:
    """Виводить звіт і повертає exit code.

    Exit codes:
        0 — усе OK (немає FAIL і WARN)
        1 — є некритичні FAIL або WARN
        2 — є критичні FAIL
        3 — є критичні FAIL і увімкнено strict (для CI)
    """
    stream = stream or sys.stdout

    if json_mode:
        json.dump(report.as_dict(), stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    else:
        text = render_report(
            report,
            show_instructions=show_instructions,
            show_env=show_env,
        )
        stream.write(text)
        stream.write("\n")

    c = report.counts()

    if c["critical_fail"]:
        return 3 if strict else 2
    if c["fail"] or c["warn"]:
        return 1
    return 0


# ─────────────────────────────────────────────────────────────
# Клас-обгортка (для уніфікованого вибору UI)
# ─────────────────────────────────────────────────────────────

class CliDependencyWindow(DependencyWindowBase):
    """CLI-реалізація вікна перевірки.

    Не показує графічного вікна — виводить звіт у stdout.
    Повертає DialogResult залежно від стану звіту.
    """

    def __init__(
        self,
        report: CheckReport,
        *,
        json_mode: bool = False,
        show_instructions: bool = True,
        show_env: bool = False,
    ) -> None:
        super().__init__(report)
        self.json_mode = json_mode
        self.show_instructions = show_instructions
        self.show_env = show_env

    def run(self) -> DialogResult:
        run_cli_report(
            self.report,
            json_mode=self.json_mode,
            show_instructions=self.show_instructions,
            show_env=self.show_env,
        )
        return (
            DialogResult.CONTINUE
            if self.report.all_critical_ok
            else DialogResult.EXIT
        )


# ─────────────────────────────────────────────────────────────
# Демо-запуск: python -m common.deps.ui.cli_report
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from ..env import detect_env
    from ..report import run_all_checks

    env = detect_env()
    report = run_all_checks(env)

    json_mode = "--json" in sys.argv
    show_env = "--env" in sys.argv
    no_instructions = "--no-instructions" in sys.argv

    code = run_cli_report(
        report,
        json_mode=json_mode,
        show_instructions=not no_instructions,
        show_env=show_env,
    )
    sys.exit(code)
