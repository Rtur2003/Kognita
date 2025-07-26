import json
import os
import logging
from .config_manager import ConfigManager

class LocalizationManager:
    """Uygulama metinlerini seçilen dile göre yönetir."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LocalizationManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # __init__'in tekrar tekrar çalışmasını engelle
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.config_manager = ConfigManager()
        self.language_code = self.config_manager.get('settings.language', 'en')
        self.translations = self._load_translations()
        logging.info(f"LocalizationManager initialized with language: {self.language_code}")

    def _load_translations(self):
        """Dil dosyasını yükler."""
        locales_path = os.path.join(os.path.dirname(__file__), '..', 'locales')
        file_path = os.path.join(locales_path, f"{self.language_code}.json")
        
        # Seçilen dil dosyası yoksa İngilizce'ye dön
        if not os.path.exists(file_path):
            logging.warning(f"Language file '{file_path}' not found. Falling back to English.")
            self.language_code = 'en'
            file_path = os.path.join(locales_path, "en.json")
            if not os.path.exists(file_path):
                logging.error("Default language file 'en.json' not found! UI text will be missing.")
                return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load translation file {file_path}: {e}")
            return {}

    def get(self, key, **kwargs):
        """Verilen anahtar için çevrilmiş metni alır."""
        text = self.translations.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logging.warning(f"Missing format key {e} in translation for '{key}'")
        return text

# Global ve tekil bir nesne oluştur
loc = LocalizationManager()