import json
from pathlib import Path
from loguru import logger

CONFIG_DIR = Path.home() / ".config" / "ym-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigService:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.config_dir = config_path.parent

    def get_token(self) -> str | None:
        if not self.config_path.exists():
            return None

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return config_data.get("yandex", {}).get("token")
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Ошибка при чтении конфига {self.config_path}: {e}")
            return None

    def save_token(self, token: str) -> bool:
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config_data = {}
            if self.config_path.exists():
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                except Exception:
                    pass

            if "yandex" not in config_data:
                config_data["yandex"] = {}

            config_data["yandex"]["token"] = token

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            logger.success(f"Токен успешно сохранен в {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Не удалось сохранить токен: {e}")
            return False
