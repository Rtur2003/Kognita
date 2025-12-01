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
                "language": "tr",
                "notification_settings": {
                    "enable_goal_notifications": True,
                    "enable_focus_notifications": True,
                    "focus_notification_frequency_seconds": 300,
                    "show_achievement_notifications": True
                },
                "run_on_startup": False,
                "enable_sentry_reporting": False,
                "data_retention_days": 365
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
                loaded_config = json.load(f)
            
            # Yüklenen konfigürasyonu varsayılan ile birleştir (yeni eklenen ayarlar için)
            default_config = self._get_default_config()
            for key, value in default_config.items():
                if key not in loaded_config:
                    loaded_config[key] = value
                elif isinstance(value, dict) and isinstance(loaded_config[key], dict):
                    # Nested dict'ler için de varsayılanları ekle
                    for sub_key, sub_value in value.items():
                        if sub_key not in loaded_config[key]:
                            loaded_config[key][sub_key] = sub_value
            
            return loaded_config

        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"'{CONFIG_FILE}' okunamadı veya bozuk ({e}). Varsayılan yapılandırma kullanılıyor.")
            config = self._get_default_config()
            self.save(config)
            return config

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
        # Dotted notation desteği için (örn: "settings.idle_threshold_seconds")
        keys = key.split('.')
        d = self._config
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
            else:
                return default # Yol bulunamadı
        return d if d is not None else default # None ise default dön

    def set(self, key, value):
        """Bir yapılandırma anahtarını ayarlar ve kaydeder."""
        keys = key.split('.')
        d = self._config
        for k_index, k in enumerate(keys):
            if k_index == len(keys) - 1: # Son anahtar
                d[k] = value
            else:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {} # Yoksa veya dict değilse oluştur
                d = d[k]
        self.save()
