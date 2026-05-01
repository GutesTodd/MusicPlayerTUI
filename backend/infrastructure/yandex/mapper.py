from yandex_music import (
    Album as YandexAlbum,
    Artist as YandexArtist,
    Playlist as YandexPlaylist,
    Track as YandexTrack,
)

from shared.domain import entities


class YandexMapper:
    @staticmethod
    def map_track(y_track: YandexTrack) -> entities.Track:
        return entities.Track(
            id=y_track.id,
            title=y_track.title if y_track.title else "Неизвестно",
            duration_ms=y_track.duration_ms if y_track.duration_ms else 0,
            artists=[
                entities.Artist(
                    id=y_artist.id,
                    name=y_artist.name if y_artist.name else "Неизвестный",
                    cover_uri=y_artist.cover.uri if y_artist.cover else None,
                )
                for y_artist in y_track.artists
            ],
        )

    @staticmethod
    def map_artist(
        y_artist: YandexArtist,
        popular_tracks: list[YandexTrack] | None = None,
        albums: list[YandexAlbum] | None = None,
    ) -> entities.Artist:
        artist = entities.Artist(
            id=y_artist.id,
            name=y_artist.name if y_artist.name else "Неизвестный",
            cover_uri=y_artist.cover.uri if y_artist.cover else None,
        )

        if popular_tracks is not None or albums is not None:
            details = entities.ArtistDetails(id=y_artist.id)
            if popular_tracks:
                details.popular_tracks = [
                    YandexMapper.map_track(t) for t in popular_tracks
                ]
            if albums:
                for a in albums:
                    mapped_album = YandexMapper.map_album(a)
                    if mapped_album.type == "single":
                        details.singles.append(mapped_album)
                    else:
                        details.albums.append(mapped_album)
            artist.details = details

        return artist

    @staticmethod
    def map_album(y_album: YandexAlbum) -> entities.Album:
        album = entities.Album(
            id=y_album.id,
            title=y_album.title if y_album.title else "Неизвестно",
            type=y_album.type if y_album.type else "Неизвестный",
            artists=[
                entities.Artist(
                    id=y_artist.id,
                    name=y_artist.name if y_artist.name else "Неизвестный",
                    cover_uri=y_artist.cover.uri if y_artist.cover else None,
                )
                for y_artist in y_album.artists
            ],
            year=y_album.year,
            cover_uri=y_album.cover_uri,
        )
        volumes = getattr(y_album, "volumes", None)
        if volumes:
            album.tracks = [
                YandexMapper.map_track(y_track)
                for volume in volumes
                for y_track in volume
            ]
        return album

    @staticmethod
    def map_playlist(y_playlist: YandexPlaylist) -> entities.Playlist:
        playlist = entities.Playlist(
            id=f"{y_playlist.uid}:{y_playlist.kind}",
            uid=y_playlist.uid if y_playlist.uid else 0,
            kind=y_playlist.kind if y_playlist.kind else 0,
            title=y_playlist.title if y_playlist.title else "Без имени",
            track_count=y_playlist.track_count if y_playlist.track_count else 0,
            cover_uri=y_playlist.cover.uri if y_playlist.cover else None,
        )
        y_tracks = getattr(y_playlist, "tracks", None)
        if y_tracks:
            playlist.tracks = [
                YandexMapper.map_track(item.track) for item in y_tracks if item.track
            ]
        return playlist
