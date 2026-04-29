from yandex_music import Album, ClientAsync, Playlist

from backend.infrastructure.yandex.mapper import YandexMapper
from shared.domain import entities


class YandexTrackProvider:
    def __init__(self, client: ClientAsync) -> None:
        self._client = client

    async def get_playlist_tracks(self, playlist_id: str) -> entities.Playlist | None:
        y_playlist = await self._client.users_playlists(kind=playlist_id)
        if y_playlist and isinstance(y_playlist, Playlist):
            return YandexMapper.map_playlist(y_playlist=y_playlist)
        return None

    async def get_album_tracks(self, album_id: str) -> entities.Album | None:
        y_album = await self._client.albums(album_ids=album_id)
        if y_album and isinstance(y_album, Album):
            return YandexMapper.map_album(y_album=y_album)
        return None

    async def get_track(self, track_id: int) -> entities.Track | None:
        y_tracks = await self._client.tracks(track_ids=[track_id])
        if y_tracks:
            return YandexMapper.map_track(y_tracks[0])
        return None

    async def get_artist_tracks(self, artist_id: str) -> list[entities.Track] | None:
        y_artist_tracks = await self._client.artists_tracks(artist_id=artist_id)
        if y_artist_tracks:
            return [YandexMapper.map_track(t) for t in y_artist_tracks.tracks]
        return None
