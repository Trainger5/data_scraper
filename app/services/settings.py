import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

class SettingsManager:
    _settings = None

    @classmethod
    def load_settings(cls):
        if not os.path.exists(SETTINGS_FILE):
            return {}
        try:
            with open(SETTINGS_FILE, 'r') as f:
                cls._settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            cls._settings = {}
        return cls._settings

    @classmethod
    def get_setting(cls, key, default=None):
        if cls._settings is None:
            cls.load_settings()
        return cls._settings.get(key, default)

    @classmethod
    def update_setting(cls, key, value):
        if cls._settings is None:
            cls.load_settings()
        cls._settings[key] = value
        cls.save_settings()

    @classmethod
    def save_settings(cls):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(cls._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @classmethod
    def get_all(cls):
        if cls._settings is None:
            cls.load_settings()
        return cls._settings


# yellow pages
# yelp
# tripadvisor     