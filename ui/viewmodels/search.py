from __future__ import annotations

from loguru import logger

from shared.domain.entities import Album, Artist, Track
from ui.utils.socket_client import SocketClient

from .base import BaseViewModel


class BaseSearchViewModel(BaseViewModel):
    def __init__(self, client: SocketClient, search_type: str):
        super().__init__()
        self._client = client
        self.results: list[Track | Album | Artist] = []
        self.last_query: str = ""
        self.search_type = search_type

    async def search(self, query: str) -> None:
        if not query.strip():
            return

        self.last_query = query
        self.is_loading = True
        self.results = []
        self.set_error(None)

        action = f"search.{self.search_type}s"
        logger.info(f"Ищем {self.search_type} по запросу: {query} (action: {action})")

        response = await self._client.send_command(
            action, {"query": query, "limit": 20}
        )

        self.is_loading = False
        if response is None:
            self.set_error("Нет ответа от сервера")
            self.notify()
            return

        if response.get("status") == "ok":
            raw_data = response.get("data") or []
            self.results = []
            for item in raw_data:
                try:
                    self.results.append(self._validate_item(item))
                except Exception as e:
                    logger.error(f"Ошибка валидации {self.search_type}: {e}")
        else:
            self.set_error(response.get("error", "Ошибка поиска"))
        self.notify()

    def _validate_item(self, item: dict) -> Track | Album | Artist:
        raise NotImplementedError


class SearchTrackViewModel(BaseSearchViewModel):
    def __init__(self, client: SocketClient):
        super().__init__(client, "track")

    def _validate_item(self, item: dict) -> Track:
        return Track.model_validate(item)


class SearchAlbumViewModel(BaseSearchViewModel):
    def __init__(self, client: SocketClient):
        super().__init__(client, "album")

    def _validate_item(self, item: dict) -> Album:
        return Album.model_validate(item)


class SearchArtistViewModel(BaseSearchViewModel):
    def __init__(self, client: SocketClient):
        super().__init__(client, "artist")

    def _validate_item(self, item: dict) -> Artist:
        return Artist.model_validate(item)


class SearchViewModel(BaseViewModel):
    """Композитный ViewModel, управляющий тремя типами поиска."""

    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.tracks = SearchTrackViewModel(client)
        self.albums = SearchAlbumViewModel(client)
        self.artists = SearchArtistViewModel(client)
        self.current_type: str = "track"

        self.tracks.subscribe(self.notify)
        self.albums.subscribe(self.notify)
        self.artists.subscribe(self.notify)

    @property
    def current(self) -> BaseSearchViewModel:
        if self.current_type == "album":
            return self.albums
        if self.current_type == "artist":
            return self.artists
        return self.tracks

    async def search(self, query: str, search_type: str = "track") -> None:
        self.current_type = search_type
        await self.current.search(query)
        self.notify()

    @property
    def results(self):
        return self.current.results

    @property
    def is_loading(self):
        return self.current.is_loading

    @is_loading.setter
    def is_loading(self, value):
        # Игнорируем установку, так как состояние берется из вложенных ViewModel
        pass

    @property
    def error_message(self):
        return self.current.error_message

    @error_message.setter
    def error_message(self, value):
        # Игнорируем установку
        pass

    @property
    def last_query(self):
        return self.current.last_query
