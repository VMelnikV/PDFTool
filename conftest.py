"""Глобальні налаштування pytest для PDF Tool.

Додає потрібні теки в sys.path, щоб pytest міг імпортувати як
`src.app...`, так і внутрішні модулі (`tabs`, `utils`, `common`),
які використовує сам код під час запуску з src/app/.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "src" / "app"
COMMON = ROOT / "src" / "common"

for p in (str(ROOT), str(APP), str(COMMON)):
    if p not in sys.path:
        sys.path.insert(0, p)
