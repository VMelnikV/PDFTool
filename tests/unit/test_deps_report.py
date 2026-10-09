"""Unit-тести для common.deps.report.

Перевіряємо:
  * run_all_checks повертає CheckReport
  * counts() узгоджується з results
  * all_critical_ok коректно визначає стан
  * винятки в перевірках не ламають ланцюг
  * install_instructions генеруються для FAIL/WARN
"""

from __future__ import annotations

from common.deps.checks.base import Check, CheckResult
from common.deps.env import EnvInfo
from common.deps.report import CheckReport, run_all_checks
from common.deps.style import Status


# ─────────────────────────────────────────────────────────────
# Допоміжне
# ─────────────────────────────────────────────────────────────

def _make_env() -> EnvInfo:
    return EnvInfo(
        kind="venv",
        python="/usr/bin/python3",
        pip_cmd=("/usr/bin/python3", "-m", "pip"),
        is_writable=True,
        distro="debian",
        is_wsl=False,
        wsl_version=None,
        pep668=False,
        platform="linux",
        python_version=(3, 12, 0),
    )


class _OkCheck(Check):
    key = "test.ok"
    name = "Тест OK"
    critical = True

    def run(self, env):
        return self.ok("все добре")


class _WarnCheck(Check):
    key = "test.warn"
    name = "Тест WARN"
    critical = False

    def run(self, env):
        return self.warn("попередження")


class _FailCriticalCheck(Check):
    key = "test.fail_critical"
    name = "Тест FAIL критичний"
    critical = True

    def run(self, env):
        return self.fail(
            "не встановлено",
            fix_kind="pip",
            fix_arg="nonexistent-package",
        )


class _FailNonCriticalCheck(Check):
    key = "test.fail_non_critical"
    name = "Тест FAIL некритичний"
    critical = False

    def run(self, env):
        return self.fail("не критично")


class _CrashCheck(Check):
    key = "test.crash"
    name = "Тест з винятком"
    critical = False

    def run(self, env):
        raise RuntimeError("навмисний виняток")


# ─────────────────────────────────────────────────────────────
# run_all_checks
# ─────────────────────────────────────────────────────────────

def test_run_all_checks_returns_report():
    env = _make_env()
    report = run_all_checks(env, checks=[_OkCheck()])
    assert isinstance(report, CheckReport)
    assert report.env is env
    assert len(report.results) == 1


def test_run_all_checks_multiple():
    env = _make_env()
    checks = [_OkCheck(), _WarnCheck(), _FailCriticalCheck()]
    report = run_all_checks(env, checks=checks)
    assert len(report.results) == 3


def test_exception_in_check_becomes_fail():
    """Виняток у Check.run() не ламає ланцюг."""
    env = _make_env()
    report = run_all_checks(env, checks=[_CrashCheck()])
    assert len(report.results) == 1
    assert report.results[0].status == Status.FAIL
    assert "внутрішня помилка" in report.results[0].message


# ─────────────────────────────────────────────────────────────
# counts / підсумки
# ─────────────────────────────────────────────────────────────

def test_counts_sum_matches_total():
    env = _make_env()
    checks = [_OkCheck(), _WarnCheck(), _FailCriticalCheck()]
    report = run_all_checks(env, checks=checks)

    c = report.counts()
    total = c["ok"] + c["warn"] + c["fail"]
    assert total == len(report.results)


def test_all_critical_ok_true():
    env = _make_env()
    report = run_all_checks(env, checks=[_OkCheck(), _WarnCheck()])
    assert report.all_critical_ok is True
    assert report.has_critical_fail is False


def test_all_critical_ok_false():
    env = _make_env()
    report = run_all_checks(env, checks=[_FailCriticalCheck()])
    assert report.all_critical_ok is False
    assert report.has_critical_fail is True


def test_non_critical_fail_does_not_block():
    env = _make_env()
    report = run_all_checks(env, checks=[_FailNonCriticalCheck()])
    assert report.has_any_fail is True
    assert report.all_critical_ok is True


# ─────────────────────────────────────────────────────────────
# install_instructions
# ─────────────────────────────────────────────────────────────

def test_install_instructions_generated_for_fail():
    """Для FAIL з fix_kind='pip' мають згенеруватись інструкції."""
    env = _make_env()
    report = run_all_checks(env, checks=[_FailCriticalCheck()])
    result = report.results[0]
    assert result.install_instructions is not None
    assert "pip install" in result.install_instructions


def test_install_instructions_not_generated_for_ok():
    env = _make_env()
    report = run_all_checks(env, checks=[_OkCheck()])
    result = report.results[0]
    assert result.install_instructions is None


# ─────────────────────────────────────────────────────────────
# as_dict
# ─────────────────────────────────────────────────────────────

def test_as_dict_serializable():
    import json

    env = _make_env()
    report = run_all_checks(env, checks=[_OkCheck(), _FailCriticalCheck()])
    d = report.as_dict()
    text = json.dumps(d, ensure_ascii=False)
    assert "results" in text
    assert "env" in text
    assert "counts" in text


# ─────────────────────────────────────────────────────────────
# progress_cb
# ─────────────────────────────────────────────────────────────

def test_progress_callback_called():
    env = _make_env()
    calls = []

    def cb(current, total, result):
        calls.append((current, total, result.key))

    run_all_checks(
        env,
        checks=[_OkCheck(), _WarnCheck()],
        progress_cb=cb,
    )
    assert len(calls) == 2
    assert calls[0][0] == 1
    assert calls[0][1] == 2
    assert calls[1][0] == 2
