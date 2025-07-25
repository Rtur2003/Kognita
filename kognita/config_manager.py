# kognita/config_manager.py

import json
import os
import logging
from pathlib import Path

# Proje kök dizinini belirle
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"

class ConfigManager:
    """Uygulama yapılandırmasını yönetmek için merkezi bir sınıf."""

    def __init__(self):
        self._config = self._load()

    def _get_default_config(self):
        """Varsayılan yapılandırma sözlüğünü döndürür."""
        return {
            "settings": {
                "idle_threshold_seconds": 180,
                "language": "tr" 
            },
            "app_state": {
                "first_run": True
            }
        }

    def _load(self):
        """Yapılandırmayı dosyadan yükler, yoksa veya bozuksa varsayılanı oluşturur."""
        if not CONFIG_FILE.exists():
            logging.info(f"'{CONFIG_FILE}' bulunamadı, varsayılan yapılandırma oluşturuluyor.")
            config = self._get_default_config()
            self.save(config)
            return config
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logging.error(f"'{CONFIG_FILE}' okunamadı veya bozuk. Varsayılan yapılandırma kullanılıyor.")
            return self._get_default_config()

    def save(self, config_data=None):
        """Mevcut yapılandırmayı dosyaya kaydeder."""
        data_to_save = config_data if config_data is not None else self._config
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Yapılandırma dosyası kaydedilemedi: {e}")

    def get(self, key, default=None):
        """Anahtar-değer çiftiyle yapılandırma verisi alır."""
        return self._config.get(key, default)

    def set(self, key, value):
        """Bir yapılandırma anahtarını ayarlar ve kaydeder."""
        # Dotted notation desteği için (örn: "settings.idle_threshold_seconds")
        keys = key.split('.')
        d = self._config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save()