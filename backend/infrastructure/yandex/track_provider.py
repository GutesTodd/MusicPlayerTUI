from yandex_music import ClientAsync, Playlist

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
        y_albums = await self._client.albums(album_ids=[album_id])
        if y_albums:
            return YandexMapper.map_album(y_album=y_albums[0])
        return None

    async def get_track(self, track_id: int) -> entities.Track | None:
        y_tracks = await self._client.tracks(track_ids=[track_id])
        if y_tracks:
            return YandexMapper.map_track(y_tracks[0])
        return None

    async def get_artist_details(self, artist_id: str) -> entities.Artist | None:
        brief_info = await self._client.artists_brief_info(artist_id=artist_id)
        if not brief_info or not brief_info.artist:
            return None

        y_artist = brief_info.artist
        pop_tracks = brief_info.popular_tracks or []

        # Собираем все альбомы и дедуплицируем по ID
        albums_dict = {a.id: a for a in (brief_info.albums or [])}
        for a in brief_info.also_albums or []:
            if a.id not in albums_dict:
                albums_dict[a.id] = a

        all_albums = list(albums_dict.values())

        return YandexMapper.map_artist(
            y_artist=y_artist, popular_tracks=pop_tracks, albums=all_albums
        )
