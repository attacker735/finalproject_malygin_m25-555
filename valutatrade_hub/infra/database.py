import json
import os
from threading import Lock


class DatabaseManager:

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: str):
        """Загружает данные из json."""
        if not os.path.exists(path):
            self.save(path, [])
            raise FileNotFoundError
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, path: str, data):
        """Сохраняет данные в json."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
