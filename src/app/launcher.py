#!/usr/bin/env python3
"""PDF Tool Launcher.

Точка входу для AppImage і .deb:
  1. Перевіряє залежності (config.get_check_on_startup()).
  2. Якщо потрібно — показує QtDependencyWindow (або CLI).
  3. Якщо все OK — запускає main.py.

CLI-прапорці:
    --check-only         тільки перевірка, без запуску GUI
    --json               вивід звіту у JSON (для скриптів)
    --strict             exit code != 0 при критичних (для CI)
    --ui=qt|cli          примусовий вибір інтерфейсу
    --force              запустити, навіть якщо є критичні помилки
    --no-startup-check   пропустити перевірку при старті (разово)
    --help, -h           довідка
"""

from __future__ import annotations

import argparse
import os
import sys

# ── Шляхи ───────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ── Argument parsing ────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf-tool",
        description="PDF Tool — універсальний редактор PDF.",
        add_help=False,  # власна обробка --help
    )
    parser.add_argument("--check-only", action="store_true",
                        help="Тільки перевірити залежності")
    parser.add_argument("--json", action="store_true",
                        help="Вивести звіт у JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Exit code 3 при критичних помилках (для CI)")
    parser.add_argument("--ui", choices=["qt", "cli"], default=None,
                        help="Примусовий вибір інтерфейсу")
    parser.add_argument("--force", action="store_true",
                        help="Запустити навіть з критичними помилками")
    parser.add_argument("--no-startup-check", action="store_true",
                        help="Пропустити перевірку при старті (разово)")
    parser.add_argument("--version", action="store_true",
                        help="Показати версію і вийти")
    parser.add_argument("-h", "--help", action="store_true",
                        help="Довідка")
    return parser.parse_args(argv)


def _print_help() -> None:
    print("""PDF Tool — універсальний редактор PDF

Використання:
    python launcher.py [ОПЦІЇ]

Опції:
    --check-only         Тільки перевірити залежності, не запускати GUI
    --json               Вивести звіт у форматі JSON (для скриптів)
    --strict             Exit code 3 при критичних помилках (для CI)
    --ui=qt|cli          Примусовий вибір інтерфейсу
    --force              Запустити, навіть якщо є критичні помилки
    --no-startup-check   Пропустити перевірку при старті (разово)
    --version            Показати версію і вийти
    -h, --help           Показати цю довідку

Приклади:
    python launcher.py                    # перевірити (за потреби) і запустити
    python launcher.py --check-only       # тільки перевірити
    python launcher.py --check-only --json
    python launcher.py --force            # запустити, ігноруючи критичні
""")


# ── Головна функція ─────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.help:
        _print_help()
        return 0

    if args.version:
        from common.version import __version__
        print(f"PDF Tool {__version__}")
        return 0

    # 1. EnvInfo + перевірки
    from common.deps.env import detect_env
    from common.deps.report import run_all_checks

    env = detect_env()
    report = run_all_checks(env)

    # 2. Режим --check-only: тільки CLI-звіт
    if args.check_only:
        from common.deps.ui.cli_report import run_cli_report

        return run_cli_report(
            report,
            json_mode=args.json,
            strict=args.strict,
        )

    # 3. Визначаємо, чи треба перевіряти при старті
    try:
        from common.deps.config import Config
        cfg = Config()
        check_on_startup = cfg.get_check_on_startup()
    except Exception:
        check_on_startup = True

    if args.no_startup_check:
        check_on_startup = False

    # 4. Показуємо вікно (або CLI), якщо потрібно
    if check_on_startup:
        from common.deps.ui.launcher import run_window
        from common.deps.ui.base import DialogResult

        result = run_window(
            report,
            force=args.ui,
            json_mode=args.json,  # для CLI-режиму
        )

        if result != DialogResult.CONTINUE and not args.force:
            return 1

    # 5. Все OK (або --force) — запускаємо головний застосунок
    try:
        import main
        main.main()
        return 0
    except ImportError as e:
        print(f"❌ Не вдалось імпортувати main.py: {e}", file=sys.stderr)
        print("Переконайтеся, що main.py знаходиться поряд з launcher.py.",
              file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"❌ Помилка запуску: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
