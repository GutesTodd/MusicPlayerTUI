import asyncio

from loguru import logger

from ui.utils.socket_client import SocketClient
from ui.viewmodels.base import BaseViewModel


class PlayerViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.current_track: str | None = None
        self.is_playing: bool = False
        self.volume: int = 100
        self.position_ms: int = 0
        self.duration_ms: int = 0
        self.repeat_mode: str = "none"
        self._lock = asyncio.Lock()  # Защита от одновременных команд

    def _update_track_state(self, response: dict) -> None:
        """Централизованное обновление стейта из любого ответа сервера."""
        if not response or not isinstance(response, dict):
            return

        # Обновляем инфо о треке
        if "title" in response:
            artists = ", ".join(a["name"] for a in response.get("artists", []))
            self.current_track = f"{artists} — {response['title']}"
            self.duration_ms = response.get("duration_ms", 0)
            self.position_ms = 0
            self.is_playing = True

        # Синхронизируем режим повтора
        if "repeat_mode" in response:
            raw_mode = str(response["repeat_mode"]).lower()
            if "none" in raw_mode:
                self.repeat_mode = "none"
            elif "one" in raw_mode:
                self.repeat_mode = "one"
            elif "all" in raw_mode:
                self.repeat_mode = "all"

        self.notify()

    async def toggle_repeat(self) -> None:
        """Цикличное переключение режима повтора с защитой от гонки."""
        async with self._lock:
            if self.repeat_mode == "none":
                next_mode = "all"
            elif self.repeat_mode == "all":
                next_mode = "one"
            else:
                next_mode = "none"

            logger.info(f"VM: Переход {self.repeat_mode} -> {next_mode}")
            response = await self._client.send_command(
                "playback.set_play_mode", {"modes": next_mode}
            )

            if response is not None:
                self.repeat_mode = next_mode
                logger.success(f"VM: Режим '{self.repeat_mode}' активен")
                self.notify()
            else:
                logger.error("VM: Сервер не ответил на смену режима")

    async def next_track(self, from_button: bool = False) -> None:
        async with self._lock:
            response = await self._client.send_command(
                "playback.next", {"response_from_button": from_button}
            )
            self._update_track_state(response)

    async def prev_track(self, from_button: bool = False) -> None:
        async with self._lock:
            response = await self._client.send_command(
                "playback.prev", {"response_from_button": from_button}
            )
            self._update_track_state(response)

    async def play_media(
        self,
        media_id: str,
        media_type: str,
        title: str,
        artist: str,
        duration_ms: int = 0,
        start_from_track_id: str | None = None,
    ):
        async with self._lock:
            payload = {"media_id": media_id, "media_type": media_type}
            if start_from_track_id:
                payload["start_from_track_id"] = start_from_track_id

            response = await self._client.send_command("playback.play_media", payload)

            if response:
                if isinstance(response, dict) and "title" in response:
                    self._update_track_state(response)
                else:
                    self.current_track = f"{artist} — {title}" if artist else title
                    self.duration_ms = duration_ms
                    self.position_ms = 0
                    self.is_playing = True
                    self.notify()

    async def toggle_pause(self) -> None:
        async with self._lock:
            if not self.current_track:
                return
            action = "playback.pause" if self.is_playing else "playback.resume"
            response = await self._client.send_command(action)
            if response:
                self.is_playing = not self.is_playing
                self.notify()

    async def set_volume(self, new_volume: int) -> None:
        # Для громкости лок не обязателен, чтобы не лагал ползунок
        self.volume = max(0, min(100, new_volume))
        await self._client.send_command("playback.set_volume", {"volume": self.volume})
        self.notify()

    async def seek(self, position_ms: int) -> None:
        # Для перемотки тоже можно без лока
        response = await self._client.send_command(
            "playback.seek", {"position_ms": position_ms}
        )
        if response:
            self.position_ms = position_ms
            self.notify()
