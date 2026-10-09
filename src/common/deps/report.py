"""Агрегація результатів перевірок і запуск усього ланцюжка.

Основні публічні елементи:
  * CheckReport     — колекція CheckResult + підсумки
  * run_all_checks  — виконує всі перевірки з registry.CHECKS

Особливості:
  * Винятки в Check.run() перетворюються в FAIL, не ламають ланцюг
  * Після кожної перевірки автоматично генеруються install_instructions,
    якщо їх ще немає (для FAIL/WARN з fix_kind)
  * Прогрес-колбек викликається після кожної перевірки
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .checks.base import Check, CheckResult
from .checks.registry import get_checks
from .env import EnvInfo
from .instructions import (
    external_install_instructions,
    pip_install_instructions,
)
from .style import Status

ProgressCallback = Callable[[int, int, CheckResult], None]


# ─────────────────────────────────────────────────────────────
# Звіт
# ─────────────────────────────────────────────────────────────

@dataclass
class CheckReport:
    """Колекція результатів + підсумки.

    Призначений для передачі в UI та CLI.
    """

    results: list[CheckResult] = field(default_factory=list)
    env: EnvInfo | None = None
    cancelled: bool = False

    # ─── додавання ───────────────────────────────────────────

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    def replace(self, key: str, result: CheckResult) -> bool:
        """Замінює результат за ключем (для повторної перевірки)."""
        for i, r in enumerate(self.results):
            if r.key == key:
                self.results[i] = result
                return True
        return False

    # ─── підсумки ────────────────────────────────────────────

    @property
    def all_critical_ok(self) -> bool:
        """True, якщо немає жодного FAIL серед критичних."""
        for r in self.results:
            if r.critical and r.status == Status.FAIL:
                return False
        return True

    @property
    def has_critical_fail(self) -> bool:
        return not self.all_critical_ok

    @property
    def has_any_fail(self) -> bool:
        return any(r.status == Status.FAIL for r in self.results)

    @property
    def has_warnings(self) -> bool:
        return any(r.status == Status.WARN for r in self.results)

    @property
    def critical_fails(self) -> list[CheckResult]:
        return [r for r in self.results
                if r.critical and r.status == Status.FAIL]

    @property
    def non_critical_fails(self) -> list[CheckResult]:
        return [r for r in self.results
                if not r.critical and r.status == Status.FAIL]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == Status.WARN]

    @property
    def needs_attention(self) -> list[CheckResult]:
        """Усі FAIL і WARN (для показу інструкцій)."""
        return [r for r in self.results if r.needs_attention]

    def counts(self) -> dict[str, int]:
        """Підрахунок статусів для підсумкового рядка."""
        result = {"ok": 0, "warn": 0, "fail": 0, "critical_fail": 0}
        for r in self.results:
            if r.status == Status.OK:
                result["ok"] += 1
            elif r.status == Status.WARN:
                result["warn"] += 1
            elif r.status == Status.FAIL:
                result["fail"] += 1
                if r.critical:
                    result["critical_fail"] += 1
        return result

    def summary_line(self) -> str:
        """Короткий рядок для CLI та статусбара."""
        c = self.counts()
        parts = [f"OK: {c['ok']}"]
        if c["warn"]:
            parts.append(f"попереджень: {c['warn']}")
        if c["fail"]:
            parts.append(f"помилок: {c['fail']}")
        if c["critical_fail"]:
            parts.append(f"критичних: {c['critical_fail']}")
        return " | ".join(parts)

    def as_dict(self) -> dict:
        """Серіалізація всього звіту для CLI --json."""
        return {
            "env": self.env.as_dict() if self.env else None,
            "counts": self.counts(),
            "all_critical_ok": self.all_critical_ok,
            "has_any_fail": self.has_any_fail,
            "has_warnings": self.has_warnings,
            "results": [r.as_dict() for r in self.results],
        }


# ─────────────────────────────────────────────────────────────
# Генерація інструкцій
# ─────────────────────────────────────────────────────────────

def _build_instructions(result: CheckResult, env: EnvInfo) -> str | None:
    """Генерує текст інструкції для FAIL/WARN на основі fix_kind."""
    if not result.needs_attention:
        return None

    kind = result.fix_kind
    arg = result.fix_arg

    if kind == "pip" and arg:
        return pip_install_instructions(arg, env, result.fix_min_version)

    if kind == "external" and arg:
        return external_install_instructions(arg, env)

    if kind == "config":
        return (
            "Спробуйте:\n"
            "  1. Видалити конфіг і перезапустити:\n"
            "       rm ~/.config/pdf_tool/config.json\n"
            "  2. Або перевірити права на файл:\n"
            "       ls -la ~/.config/pdf_tool/"
        )

    if kind == "fs":
        return (
            "Перевірте права на теку та вільне місце:\n"
            "  df -h\n"
            "  ls -ld <проблемна-тека>"
        )

    if kind == "manual" and result.fix_hint:
        return result.fix_hint

    return None


# ─────────────────────────────────────────────────────────────
# Запуск усіх перевірок
# ─────────────────────────────────────────────────────────────

def run_all_checks(
    env: EnvInfo,
    checks: list[Check] | None = None,
    progress_cb: ProgressCallback | None = None,
    stop_flag: Callable[[], bool] | None = None,
) -> CheckReport:
    """Запускає всі перевірки і повертає CheckReport.

    Параметри:
        env         — EnvInfo (обов'язково)
        checks      — список перевірок (за замовчуванням registry.CHECKS)
        progress_cb — колбек(current, total, result) після кожної перевірки
        stop_flag   — колбек, який повертає True для скасування

    Винятки в окремих перевірках не ламають ланцюг: вони
    перетворюються в CheckResult зі статусом FAIL і повідомленням.
    """
    if checks is None:
        checks = get_checks()

    report = CheckReport(env=env)
    total = len(checks)

    for i, check in enumerate(checks, start=1):
        if stop_flag and stop_flag():
            report.cancelled = True
            break

        try:
            result = check.run(env)
        except Exception as exc:  # noqa: BLE001
            result = CheckResult(
                key=check.key,
                name=check.name,
                status=Status.FAIL,
                message=f"внутрішня помилка перевірки: {exc}",
                critical=check.critical,
                details=f"{type(exc).__name__}: {exc}",
            )

        # Автогенерація інструкції, якщо ще немає
        if result.needs_attention and not result.install_instructions:
            result.install_instructions = _build_instructions(result, env)

        report.add(result)

        if progress_cb:
            try:
                progress_cb(i, total, result)
            except Exception:
                # Колбек не має ламати ланцюг
                pass

    return report


# ─────────────────────────────────────────────────────────────
# CLI для швидкої перевірки
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    env = detect_env = None  # placeholder для лінтера
    from .env import detect_env

    env = detect_env()
    report = run_all_checks(env)

    print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
