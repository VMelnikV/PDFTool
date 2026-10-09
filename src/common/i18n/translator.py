# src/common/i18n/translator.py
import json
import os
import sys
import locale
import urllib.request
import urllib.error


class Translator:
    # URL до репозиторію з перекладами на GitHub
    TRANSLATIONS_URL = (
        "https://raw.githubusercontent.com/VMelnikV/"
        "PDFTool/main/src/common/i18n/translations"
    )

    # Людяні назви мов для UI
    LANGUAGE_NAMES = {
        "en": "English",
        "uk": "Українська",
        "de": "Deutsch",
        "pl": "Polski",
        "fr": "Français",
        "es": "Español",
        "it": "Italiano",
        "pt": "Português",
        "nl": "Nederlands",
        "cs": "Čeština",
        "sk": "Slovenčina",
        "tr": "Türkçe",
        "ja": "日本語",
        "zh": "中文",
        "ko": "한국어",
    }

    def __init__(self):
        self.current_lang = "en"
        self.translations = {}
        self._ensure_user_dir()
        self._load_translations()

    # ────────────────────────────────────────────────────────
    # Визначення мови системи
    # ────────────────────────────────────────────────────────

    def _get_system_language(self):
        """Визначає мову системи"""
        try:
            system_lang = locale.getlocale()[0]
            if system_lang:
                return system_lang.split('_')[0]
        except Exception:
            pass

        for var in ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']:
            value = os.environ.get(var, '')
            if value and value not in ('C', 'POSIX'):
                return value.split('_')[0].split('.')[0]

        return 'en'

    # ────────────────────────────────────────────────────────
    # Шляхи до тек перекладів
    # ────────────────────────────────────────────────────────

    def _get_user_translations_dir(self):
        """Повертає шлях до користувацької папки перекладів"""
        config_home = os.environ.get(
            'XDG_CONFIG_HOME', os.path.expanduser('~/.config')
        )
        return os.path.join(config_home, 'pdf_tool', 'translations')

    def _get_builtin_translations_dir(self):
        """Повертає шлях до вбудованих перекладів"""
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(
                    sys._MEIPASS, 'common', 'i18n', 'translations'
                )
            else:
                base_path = os.path.dirname(sys.executable)
                return os.path.join(
                    base_path, 'common', 'i18n', 'translations'
                )

        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'translations')

    def _ensure_user_dir(self):
        """Створює папку для користувацьких перекладів"""
        user_dir = self._get_user_translations_dir()
        try:
            os.makedirs(user_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create user translations dir: {e}")

    # ────────────────────────────────────────────────────────
    # Завантаження
    # ────────────────────────────────────────────────────────

    def _load_translations(self):
        """Завантажує переклади з усіх джерел"""
        # 1. Вбудовані переклади
        builtin_dir = self._get_builtin_translations_dir()
        if os.path.exists(builtin_dir):
            self._load_from_dir(builtin_dir)

        # 2. Користувацькі переклади
        user_dir = self._get_user_translations_dir()
        if os.path.exists(user_dir):
            self._load_from_dir(user_dir)

        # 3. Визначаємо мову системи
        system_lang = self._get_system_language()

        # 4. Якщо переклад для мови системи не знайдено — з GitHub
        if system_lang not in self.translations:
            if self._download_from_github(system_lang):
                self.current_lang = system_lang
            else:
                # 5. Fallback на англійську
                self.current_lang = (
                    'en' if 'en' in self.translations
                    else list(self.translations.keys())[0]
                    if self.translations else 'en'
                )
        else:
            self.current_lang = system_lang

    def _download_from_github(self, lang):
        """Завантажує переклад з GitHub"""
        url = f"{self.TRANSLATIONS_URL}/{lang}.json"

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))

            flat_dict = self._flatten(data)
            self.translations[lang] = flat_dict
            self._save_to_cache(lang, data)

            print(f"✅ Завантажено переклад для '{lang}' з GitHub")
            return True

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"ℹ️ Переклад для '{lang}' не знайдено на GitHub")
            else:
                print(f"⚠️ Помилка завантаження перекладу: {e}")
            return False
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            print(f"⚠️ Не вдалося завантажити переклад: {e}")
            return False

    def _save_to_cache(self, lang, data):
        """Зберігає завантажений переклад у кеш"""
        try:
            user_dir = self._get_user_translations_dir()
            filepath = os.path.join(user_dir, f"{lang}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not cache translation: {e}")

    def _load_from_dir(self, directory):
        """Завантажує всі JSON-файли з папки"""
        if not os.path.exists(directory):
            return

        for filename in os.listdir(directory):
            if not filename.endswith('.json'):
                continue
            if filename.startswith('.'):       # .gitkeep, .DS_Store тощо
                continue

            lang = filename[:-5]
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                flat_dict = self._flatten(data)

                if lang in self.translations:
                    self.translations[lang].update(flat_dict)
                else:
                    self.translations[lang] = flat_dict
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")

    @staticmethod
    def _flatten(data):
        """Розгортає вкладену структуру JSON у плоский словник.

        Для кожного ключа всередині категорії додає ДВА записи:
          - голий ключ:       'section_language'
          - з префіксом:      'settings.section_language'

        Це дозволяє викликати tr('section_language', 'settings')
        або tr('settings.section_language') — обидва спрацюють.
        """
        flat = {}
        for category, values in data.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    flat[key] = value
                    flat[f"{category}.{key}"] = value
            else:
                flat[category] = values
        return flat

    # ────────────────────────────────────────────────────────
    # Переклад
    # ────────────────────────────────────────────────────────

    def tr(self, key, domain="common"):
        """Повертає переклад для заданого ключа"""
        if self.current_lang in self.translations:
            translation = self.translations[self.current_lang].get(key)
            if translation is not None:
                return translation

        # Fallback на англійську
        if 'en' in self.translations:
            translation = self.translations['en'].get(key)
            if translation is not None:
                return translation

        return key

    def trf(self, key, domain="common", **kwargs):
        """Переклад із форматуванням плейсхолдерів.

        Приклад:
            translator.trf('status_error_check', 'deps_ui',
                           error='RuntimeError: ...')
            # -> 'Помилка перевірки: RuntimeError: ...'

        Якщо в шаблоні немає плейсхолдера, який передано — він
        ігнорується. Якщо в шаблоні є зайвий плейсхолдер, якого
        немає в kwargs — повертається шаблон як є (без .format).
        """
        template = self.tr(key, domain)
        if not kwargs:
            return template
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # Шаблон містить плейсхолдери, яких немає в kwargs,
            # або синтаксично некоректний — повертаємо як є.
            return template

    def set_language(self, lang):
        if lang in self.translations:
            self.current_lang = lang
            return True
        return False

    def get_language(self):
        return self.current_lang

    # ────────────────────────────────────────────────────────
    # Список доступних мов (для шестерінки)
    # ────────────────────────────────────────────────────────

    def get_available_languages(self):
        """Повертає відсортований список доступних мов.

        Включає вбудовані, користувацькі та (за потреби) завантажені
        з GitHub. Якщо список порожній — повертає ['en'].
        """
        langs = sorted(self.translations.keys())
        return langs if langs else ['en']

    def get_language_display_name(self, lang):
        """Повертає людяну назву мови для UI.

        Якщо назви немає в LANGUAGE_NAMES — повертає код мови
        у верхньому регістрі (наприклад, 'xx' -> 'XX').
        """
        return self.LANGUAGE_NAMES.get(lang, lang.upper())


# Глобальний екземпляр
translator = Translator()
