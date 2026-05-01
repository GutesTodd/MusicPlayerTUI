from __future__ import annotations

from loguru import logger

from shared.domain.entities import Album, Artist
from ui.utils.socket_client import SocketClient

from .base import BaseViewModel


class AlbumDetailViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.album: Album | None = None

    async def load_album(self, album_id: str) -> None:
        self.is_loading = True
        self.album = None
        self.set_error(None)
        self.notify()

        logger.info(f"Загрузка деталей альбома: {album_id}")
        response = await self._client.send_command(
            "catalog.get_album", {"album_id": album_id}
        )

        self.is_loading = False
        if response and response.get("status") == "ok":
            try:
                self.album = Album.model_validate(response.get("data"))
            except Exception as e:
                logger.error(f"Ошибка валидации альбома: {e}")
                self.set_error("Ошибка обработки данных альбома")
        else:
            self.set_error(
                response.get("error", "Не удалось загрузить данные альбома")
                if response
                else "Нет ответа от сервера"
            )
        self.notify()


class ArtistDetailViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.artist: Artist | None = None

    async def load_artist(self, artist_id: str) -> None:
        self.is_loading = True
        self.artist = None
        self.set_error(None)
        self.notify()

        logger.info(f"Загрузка деталей артиста: {artist_id}")
        response = await self._client.send_command(
            "catalog.get_artist", {"artist_id": artist_id}
        )

        self.is_loading = False
        if response and response.get("status") == "ok":
            try:
                self.artist = Artist.model_validate(response.get("data"))
            except Exception as e:
                logger.error(f"Ошибка валидации артиста: {e}")
                self.set_error("Ошибка обработки данных артиста")
        else:
            self.set_error(
                response.get("error", "Не удалось загрузить данные артиста")
                if response
                else "Нет ответа от сервера"
            )
        self.notify()
