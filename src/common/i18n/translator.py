# src/common/i18n/translator.py
import json
import os

class Translator:
    def __init__(self):
        self.current_lang = "uk"
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Завантажує переклади з JSON-файлів"""
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        
        if not os.path.exists(translations_dir):
            print(f"Warning: Translations directory not found: {translations_dir}")
            return
        
        for filename in os.listdir(translations_dir):
            if filename.endswith('.json') and filename != '.gitkeep':
                lang = filename[:-5]
                filepath = os.path.join(translations_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Розгортаємо вкладену структуру в плоский словник
                    flat_dict = {}
                    for category, values in data.items():
                        if isinstance(values, dict):
                            for key, value in values.items():
                                # Додаємо ключ як є (без категорії)
                                flat_dict[key] = value
                                # Додаємо з категорією для зворотної сумісності
                                flat_dict[f"{category}.{key}"] = value
                        else:
                            flat_dict[category] = values
                    
                    self.translations[lang] = flat_dict
                    #Закоментований вивід кількості ключів перекладу# print(f"Loaded {lang} translations: {len(flat_dict)} keys")
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")
    
    def tr(self, key, domain="common"):
        """Повертає переклад для заданого ключа"""
        # Спершу шукаємо ключ у поточній мові
        if self.current_lang in self.translations:
            translation = self.translations[self.current_lang].get(key)
            if translation is not None:
                return translation
        
        # Якщо не знайдено, повертаємо ключ
        print(f"Warning: No translation found for '{key}' in '{domain}'")
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
