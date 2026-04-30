from loguru import logger
from yandex_music import ClientAsync
from yandex_music.exceptions import YandexMusicError

from backend.infrastructure.yandex.mapper import YandexMapper
from shared.domain import entities


class YandexSearcher:
    def __init__(self, client: ClientAsync) -> None:
        self._client = client

    async def search_tracks(
        self, query: str, limit: int = 10
    ) -> list[entities.Track] | None:
        try:
            logger.debug(f"Запрос: {query}")
            result = await self._client.search(text=query, type_="track")
            logger.debug(f"Сырые данные поиска: {result}")
            if not result or not result.tracks or not result.tracks.results:
                return None

            return [
                YandexMapper.map_track(track) for track in result.tracks.results[:limit]
            ]
        except YandexMusicError as e:
            logger.error(f"Ошибка поиска трека по Яндекс.Музыке: {e}")
            raise e

    async def search_albums(
        self, query: str, limit: int = 10
    ) -> list[entities.Album] | None:
        try:
            result = await self._client.search(text=query, limit=limit, type_="album")
            if not result or not result.albums or not result.albums.results:
                return None
            return [
                YandexMapper.map_album(album) for album in result.albums.results[:limit]
            ]
        except YandexMusicError as e:
            logger.error(f"Ошибка поиска альбома по Яндекс.Музыке: {e}")
            raise e

    async def search_artists(
        self, query: str, limit: int = 10
    ) -> list[entities.Artist] | None:
        try:
            result = await self._client.search(text=query, limit=limit, type_="artist")
            if not result or not result.artists or not result.artists.results:
                return None
            return [
                YandexMapper.map_artist(artist)
                for artist in result.artists.results[:limit]
            ]
        except YandexMusicError as e:
            logger.error(f"Ошибка поиска артиста по Яндекс.Музыке: {e}")
            raise e
