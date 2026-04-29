import asyncio
import json
from pathlib import Path
from typing import Optional

from loguru import logger
from ui.viewmodels.base import BaseViewModel
from ui.utils.socket_client import SocketClient

CONFIG_FILE = Path.home() / ".config" / "ym-cli" / "config.json"


class AuthViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self.client = client
        self.platforms = [
            ("Яндекс.Музыка", "yandex"),
        ]
        self.auth_code: Optional[str] = None
        self.auth_url: Optional[str] = None
        self.is_polling: bool = False
        self.is_authenticated_successfully: bool = False

    def is_authenticated(self, platform: str = "yandex") -> bool:
        if not CONFIG_FILE.exists():
            return False
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return bool(data.get(platform, {}).get("token"))
        except Exception:
            return False

    async def request_device_code(self, platform: str) -> bool:
        """Запрашивает код для авторизации устройства."""
        self.is_loading = True
        self.set_error(None)
        self.notify()

        try:
            response = await self.client.send_command(
                "auth.get_auth_code", {"platform": platform}
            )
            response = response.get("data") if response else None
            if response and response.get("status") == "pending":
                self.auth_code = response.get("user_code")
                self.auth_url = response.get("verification_url")
                logger.info(response)
                self.is_polling = True
                self.is_loading = False
                self.notify()
                asyncio.create_task(self._poll_auth_status(platform))
                return True
            else:
                error = response.get("error") if response else "Нет ответа от сервера"
                self.set_error(f"Ошибка получения кода: {error}")
                return False
        except Exception as e:
            self.set_error(f"Ошибка сети: {e}")
            return False
        finally:
            self.is_loading = False
            self.notify()

    async def _poll_auth_status(self, platform: str):
        while self.is_polling:
            await asyncio.sleep(2)
            try:
                response = await self.client.send_command(
                    "auth.get_status_auth", {"platform": platform}
                )
                response = response.get("data") if response else None
                if not response:
                    continue
                status = response.get("status")
                if status == "success":
                    self.is_polling = False
                    self.is_authenticated_successfully = True
                    self.notify()
                    break
                elif status == "error":
                    self.is_polling = False
                    self.set_error(response.get("error") or "Ошибка авторизации")
                    break
                elif status == "idle":
                    self.is_polling = False
                    self.set_error("Сессия авторизации истекла")
                    break
            except Exception:
                pass

    def stop_polling(self):
        self.is_polling = False
