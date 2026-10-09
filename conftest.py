"""Глобальні налаштування pytest для PDF Tool.

Додає потрібні теки в sys.path, щоб pytest міг імпортувати як
`src.app...`, так і внутрішні модулі (`tabs`, `utils`, `common`),
які використовує сам код під час запуску з src/app/.

Також додає src/ у sys.path, щоб працювали імпорти типу
`from common.deps.env import ...` та `from common.version import ...`.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "src" / "app"
COMMON = ROOT / "src" / "common"
SRC = ROOT / "src"

# Порядок важливий: спочатку SRC (щоб працювало `import common`),
# потім APP і COMMON (для внутрішніх імпортів самих модулів).
for p in (str(SRC), str(APP), str(COMMON), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
