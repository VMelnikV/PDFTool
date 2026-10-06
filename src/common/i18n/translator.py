# src/common/i18n/translator.py
import json
import os
import sys
import locale
import urllib.request
import urllib.error

class Translator:
    # URL до репозиторію з перекладами на GitLab
    TRANSLATIONS_URL = "https://gitlab.com/MelnikV/pdf_tool/-/raw/main/src/common/i18n/translations"
    
    def __init__(self):
        self.current_lang = "en"
        self.translations = {}
        self._ensure_user_dir()
        self._load_translations()
    
    def _get_system_language(self):
        """Визначає мову системи"""
        try:
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                return system_lang.split('_')[0]
        except:
            pass
        
        for var in ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']:
            value = os.environ.get(var, '')
            if value and value not in ('C', 'POSIX'):
                return value.split('_')[0].split('.')[0]
        
        return 'en'
    
    def _get_user_translations_dir(self):
        """Повертає шлях до користувацької папки перекладів"""
        config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        return os.path.join(config_home, 'pdf_tool', 'translations')
    
    def _get_builtin_translations_dir(self):
        """Повертає шлях до вбудованих перекладів"""
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, 'common', 'i18n', 'translations')
            else:
                base_path = os.path.dirname(sys.executable)
                return os.path.join(base_path, 'common', 'i18n', 'translations')
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'translations')
    
    def _ensure_user_dir(self):
        """Створює папку для користувацьких перекладів"""
        user_dir = self._get_user_translations_dir()
        try:
            os.makedirs(user_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create user translations dir: {e}")
    
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
        
        # 4. Якщо переклад для мови системи не знайдено — пробуємо завантажити з GitLab
        if system_lang not in self.translations:
            if self._download_from_gitlab(system_lang):
                self.current_lang = system_lang
            else:
                # 5. Fallback на англійську
                self.current_lang = 'en' if 'en' in self.translations else list(self.translations.keys())[0]
        else:
            self.current_lang = system_lang
    
    def _download_from_gitlab(self, lang):
        """Завантажує переклад з GitLab"""
        url = f"{self.TRANSLATIONS_URL}/{lang}.json"
        
        try:
            # Таймаут 5 секунд, щоб не блокувати запуск
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Розгортаємо вкладеною структуру
            flat_dict = {}
            for category, values in data.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        flat_dict[key] = value
                        flat_dict[f"{category}.{key}"] = value
                else:
                    flat_dict[category] = values
            
            self.translations[lang] = flat_dict
            
            # Кешуємо локально
            self._save_to_cache(lang, data)
            
            print(f"✅ Завантажено переклад для '{lang}' з GitLab")
            return True
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"ℹ️ Переклад для '{lang}' не знайдено на GitLab")
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
            if filename.endswith('.json') and filename != '.gitkeep':
                lang = filename[:-5]
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    flat_dict = {}
                    for category, values in data.items():
                        if isinstance(values, dict):
                            for key, value in values.items():
                                flat_dict[key] = value
                                flat_dict[f"{category}.{key}"] = value
                        else:
                            flat_dict[category] = values
                    
                    if lang in self.translations:
                        self.translations[lang].update(flat_dict)
                    else:
                        self.translations[lang] = flat_dict
                except Exception as e:
                    print(f"Warning: Could not load {filepath}: {e}")
    
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
    
    def set_language(self, lang):
        if lang in self.translations:
            self.current_lang = lang
            return True
        return False
    
    def get_language(self):
        return self.current_lang

# Глобальний екземпляр
translator = Translator()
