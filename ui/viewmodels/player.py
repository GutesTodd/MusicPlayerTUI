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
        self.duration_ms: int = 225000  # Фиктивные 3:45 по умолчанию
        self.repeat_mode: str = "none"  # "none", "all", "one"

    async def toggle_repeat(self) -> None:
        modes_cycle = ["none", "all", "one"]
        next_mode = modes_cycle[
            (modes_cycle.index(self.repeat_mode) + 1) % len(modes_cycle)
        ]

        response = await self._client.send_command(
            "playback.set_play_mode", {"modes": next_mode}
        )
        if response is None:
            return

        if response.get("status") == "ok":
            self.repeat_mode = next_mode
            self.notify()

    async def play_media(self, media_id: str, media_type: str, title: str, artist: str):
        self.is_loading = True
        self.set_error(None)
        logger.info(f"ViewModel запрашивает воспроизведение: {media_type} {media_id}")
        response = await self._client.send_command(
            "playback.play_media", {"media_id": media_id, "media_type": media_type}
        )
        if response is None:
            return
        self.is_loading = False
        if response.get("status") == "ok":
            self.current_track = f"{artist} — {title}" if artist else title
            self.is_playing = True
            self.position_ms = 0  # Сброс времени при новом треке
            self.notify()
        else:
            self.set_error(response.get("error", "Неизвестная ошибка воспроизведения"))

    async def toggle_pause(self) -> None:
        logger.info("Запрос на паузу")
        if not self.current_track:
            return
        action = "playback.pause" if self.is_playing else "playback.resume"
        response = await self._client.send_command(action)
        logger.debug(f"Ответ от сервера: {response}")
        if response is None:
            return
        if response.get("status") == "ok":
            self.is_playing = not self.is_playing
            self.notify()
        else:
            self.set_error("Не удалось изменить статус воспроизведения")

    async def next_track(self) -> None:
        logger.info("Запрос на следующий трек")
        await self._client.send_command("playback.next")

    async def prev_track(self) -> None:
        logger.info("Запрос на предыдущий трек")
        await self._client.send_command("playback.prev")

    async def set_volume(self, new_volume: int) -> None:
        safe_volume = max(0, min(100, new_volume))
        self.volume = safe_volume
        self.notify()
        response = await self._client.send_command(
            "playback.set_volume", {"volume": safe_volume}
        )
        if response is None:
            return
        if response.get("status") != "ok":
            logger.error(f"Не удалось установить громкость: {response.get('error')}")

    async def seek(self, position_ms: int) -> None:
        logger.info(f"Запрос на перемотку: {position_ms}ms")
        response = await self._client.send_command(
            "playback.seek", {"position_ms": position_ms}
        )
        if response and response.get("status") == "ok":
            self.position_ms = position_ms
            self.notify()
