"""Базові класи та модель даних для перевірок.

Тут визначено:
  * Status        — статус перевірки (PENDING / RUNNING / OK / WARN / FAIL)
  * FixKind       — тип виправлення (pip / external / config / fs / manual)
  * CheckResult   — результат однієї перевірки (імутабельний, з усіма полями)
  * Check         — абстрактний клас, який успадковують усі перевірки

Кожна конкретна перевірка:
  * має унікальний key (для програмної ідентифікації)
  * має людський name (для UI)
  * має критичність (critical: bool) — впливає на жирний шрифт і блокування
  * реалізує метод run(env) -> CheckResult

Універсальні класи (LibCheck, ExternalCheck) створюють багато
екземплярів з різними key/name. Вони встановлюють _validate_key = False,
щоб пропустити перевірку при створенні класу.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from ..style import Status

if TYPE_CHECKING:
    from ..env import EnvInfo


# ─────────────────────────────────────────────────────────────
# Типи виправлення
# ─────────────────────────────────────────────────────────────

FixKind = Literal["pip", "external", "config", "fs", "manual"]


# ─────────────────────────────────────────────────────────────
# Результат однієї перевірки
# ─────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Результат однієї перевірки.

    Поля:
        key       — унікальний id (наприклад, "lib.pypdf")
        name      — людська назва (наприклад, "Бібліотека: pypdf")
        status    — OK / WARN / FAIL / RUNNING / PENDING
        message   — короткий текст (наприклад, "не встановлено")
        critical  — критичність (впливає на жирний шрифт, блокування)

        fix_hint          — короткий натяк ("pip install pypdf")
        fix_kind          — як виправляти: pip / external / config / fs / manual
        fix_arg           — назва пакета/утиліти (для генерації інструкції)
        fix_min_version   — мінімальна версія (для pip)
        can_autofix       — чи можна виправити автоматично

        install_instructions — готовий текст інструкції (генерується пізніше)
        docs_url             — посилання на документацію
        details              — розширений текст (для кнопки «Деталі»)
    """

    key: str
    name: str
    status: Status
    message: str
    critical: bool

    # Натяки для виправлення
    fix_hint: str | None = None
    fix_kind: FixKind | None = None
    fix_arg: str | None = None
    fix_min_version: str | None = None
    can_autofix: bool = False

    # Заповнюється пізніше в report.py
    install_instructions: str | None = None

    # Додаткова інформація
    docs_url: str | None = None
    details: str | None = None

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("CheckResult.key не може бути порожнім")
        if not self.name:
            raise ValueError("CheckResult.name не може бути порожнім")

    @property
    def is_failed(self) -> bool:
        return self.status == Status.FAIL

    @property
    def is_warning(self) -> bool:
        return self.status == Status.WARN

    @property
    def is_ok(self) -> bool:
        return self.status == Status.OK

    @property
    def needs_attention(self) -> bool:
        """FAIL або WARN — те, що показуємо з інструкцією."""
        return self.status in (Status.FAIL, Status.WARN)

    def as_dict(self) -> dict:
        """Серіалізація для CLI --json."""
        return {
            "key": self.key,
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "critical": self.critical,
            "fix_hint": self.fix_hint,
            "fix_kind": self.fix_kind,
            "fix_arg": self.fix_arg,
            "fix_min_version": self.fix_min_version,
            "can_autofix": self.can_autofix,
            "install_instructions": self.install_instructions,
            "docs_url": self.docs_url,
            "details": self.details,
        }


# ─────────────────────────────────────────────────────────────
# Абстрактна перевірка
# ─────────────────────────────────────────────────────────────

class Check(ABC):
    """Базовий клас для всіх перевірок.

    Підкласи визначають:
        key      — унікальний id (наприклад, "lib.pypdf")
        name     — людська назва (наприклад, "Бібліотека: pypdf")
        critical — критичність
        run(env) — логіка перевірки

    Універсальні класи (LibCheck, ExternalCheck) створюють багато
    екземплярів з різними key/name. Вони мають встановити
    _validate_key = False, щоб пропустити перевірку при створенні класу.

    Для зручності є хелпери self.ok(), self.warn(), self.fail().
    """

    key: str = ""
    name: str = ""
    critical: bool = False
    description: str = ""

    # Якщо True — __init_subclass__ вимагатиме key/name.
    # Універсальні класи ставлять False.
    _validate_key: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        # Універсальні класи (LibCheck, ExternalCheck) пропускають перевірку.
        # Використовуємо cls.__dict__ напряму, щоб перевіряти саме цей клас,
        # а не успадковане значення.
        if not cls.__dict__.get("_validate_key", True):
            return

        if not getattr(cls, "key", ""):
            raise TypeError(f"{cls.__name__}: не вказано key")
        if not getattr(cls, "name", ""):
            raise TypeError(f"{cls.__name__}: не вказано name")

    @abstractmethod
    def run(self, env: "EnvInfo") -> CheckResult:
        """Виконує перевірку і повертає CheckResult.

        Може кидати виняток — report.py його перехопить і перетворить
        у CheckResult зі статусом FAIL.
        """
        raise NotImplementedError

    # ─── хелпери ─────────────────────────────────────────────

    def _base_kwargs(self) -> dict:
        return {"key": self.key, "name": self.name, "critical": self.critical}

    def ok(self, message: str = "OK", **kwargs) -> CheckResult:
        """Успішна перевірка."""
        return CheckResult(
            **self._base_kwargs(),
            status=Status.OK,
            message=message,
            **kwargs,
        )

    def warn(self, message: str, **kwargs) -> CheckResult:
        """Попередження (не блокує)."""
        return CheckResult(
            **self._base_kwargs(),
            status=Status.WARN,
            message=message,
            **kwargs,
        )

    def fail(self, message: str, **kwargs) -> CheckResult:
        """Помилка. Для critical=True блокує запуск."""
        return CheckResult(
            **self._base_kwargs(),
            status=Status.FAIL,
            message=message,
            **kwargs,
        )

    def running(self, message: str = "Перевірка…") -> CheckResult:
        """Проміжний стан (для UI з прогресом)."""
        return CheckResult(
            **self._base_kwargs(),
            status=Status.RUNNING,
            message=message,
        )
