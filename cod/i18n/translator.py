import json
import os
from PySide6.QtCore import QLocale

class Translator:
    """Клас для роботи з перекладами у застосунку"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._translations = {}
        self._current_locale = 'en'
        self._load_translations()
        
    def _load_translations(self):
        """Завантажує всі доступні переклади з JSON"""
        locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
        
        if not os.path.exists(locale_dir):
            print(f"Warning: Locale directory not found: {locale_dir}")
            return
            
        for file in os.listdir(locale_dir):
            if file.endswith('.json'):
                locale = file.split('.')[0]
                try:
                    with open(os.path.join(locale_dir, file), 'r', encoding='utf-8') as f:
                        self._translations[locale] = json.load(f)
                except Exception as e:
                    print(f"Error loading {file}: {e}")
        
        # Визначаємо системну мову
        system_locale = QLocale.system().name()[:2]
        if system_locale in self._translations:
            self._current_locale = system_locale
        elif 'en' in self._translations:
            self._current_locale = 'en'
    
    def tr(self, key, context='common'):
        """Отримує переклад за ключем"""
        translation = self._translations.get(self._current_locale, {})
        context_dict = translation.get(context, {})
        return context_dict.get(key, key)
    
    def set_locale(self, locale):
        """Змінює поточну мову"""
        if locale in self._translations:
            self._current_locale = locale
            return True
        return False
    
    def get_available_locales(self):
        """Повертає список доступних мов"""
        return list(self._translations.keys())

# Глобальний екземпляр
translator = Translator()
