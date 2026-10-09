"""Версія PDF Tool — єдине джерело правди.

Читають:
  * settings_tab.py — показ у шестерінці
  * launcher.py     — для --version
  * pdf_tool.py     — у діалозі About
  * packaging/*     — при збірці (руками, поки що)

Формат: MAJOR.MINOR.PATCH (SemVer).

Коли змінювати:
  * PATCH (1.1.x) — виправлення багів, без нового функціоналу
  * MINOR (1.x.0) — новий функціонал, сумісний
  * MAJOR (x.0.0) — зламування сумісності
"""

__version__ = "1.1.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))
__app_name__ = "PDF Tool"
