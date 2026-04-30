from loguru import logger

from shared.domain.entities import Album, Artist, Track
from ui.utils.socket_client import SocketClient

from .base import BaseViewModel


class SearchViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.results: list[Track | Album | Artist] = []
        self.last_query: str = ""
        self.search_type: str = "track"

    async def search(self, query: str, search_type: str = "track") -> None:
        if not query.strip():
            return

        self.search_type = search_type
        # Разрешенные типы поиска согласно бэкенду
        # search.tracks, search.albums, search.artists
        if search_type == "track":
            action = "search.tracks"
        elif search_type == "album":
            action = "search.albums"
        elif search_type == "artist":
            action = "search.artists"
        else:
            action = "search.tracks"

        self.last_query = query
        self.is_loading = True
        self.results = []
        self.set_error(None)
        logger.info(f"Ищем {search_type} по запросу: {query} (action: {action})")
        response = await self._client.send_command(
            action, {"query": query, "limit": 20}
        )
        logger.debug(f"Ответ от сервера поиска: {response}")

        if response is None:
            self.is_loading = False
            self.set_error("Нет ответа от сервера")
            self.notify()
            return

        self.is_loading = False
        if response.get("status") == "ok":
            raw_data = response.get("data") or []
            self.results = []
            for item in raw_data:
                try:
                    if search_type == "track":
                        self.results.append(Track.model_validate(item))
                    elif search_type == "album":
                        self.results.append(Album.model_validate(item))
                    elif search_type == "artist":
                        self.results.append(Artist.model_validate(item))
                except Exception as e:
                    logger.error(f"Ошибка валидации {search_type}: {e}")
        else:
            self.set_error(response.get("error", "Ошибка поиска"))
        self.notify()
