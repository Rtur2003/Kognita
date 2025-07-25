# kognita/utils.py

import os
import sys

def resource_path(relative_path):
    """ PyInstaller ile paketlendiğinde varlık dosyalarına doğru yolu bulur. """
    try:
        # PyInstaller geçici bir klasör oluşturur ve yolu _MEIPASS içine saklar.
        base_path = sys._MEIPASS
    except Exception:
        # Kod normal bir Python betiği olarak çalışırken
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    return os.path.join(base_path, 'assets', relative_path)