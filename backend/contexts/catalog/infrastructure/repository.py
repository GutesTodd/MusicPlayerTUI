from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.domain import entities
from shared.domain.interfaces import TrackProvider


class CatalogRepository:
    def __init__(self, session: AsyncSession, provider: TrackProvider) -> None:
        self._session = session
        self._provider = provider

    async def get_playlists(self, use_cache: bool = True) -> list[entities.Playlist]:
        if use_cache:
            stmt = select(entities.Playlist)
            result = await self._session.execute(stmt)
            db_playlists = list(result.scalars().all())
            if db_playlists:
                return db_playlists
        playlists = await self._provider.get_user_playlists()
        if not playlists:
            return []
        for playlist in playlists:
            await self._session.merge(playlist)
        return playlists

    async def get_playlist_with_tracks(
        self, uid: int, kind: int, use_cache: bool = True
    ) -> entities.Playlist | None:
        if use_cache:
            stmt = (
                select(entities.Playlist)
                .where(entities.Playlist.uid == uid, entities.Playlist.kind == kind)  # pyright: ignore
                .options(
                    selectinload(entities.Playlist.tracks).selectinload(  # pyright: ignore
                        entities.Track.artists  # pyright: ignore
                    )
                )
            )
            result = await self._session.execute(stmt)
            db_playlist = result.scalar_one_or_none()
            if db_playlist and db_playlist.tracks:
                return db_playlist
        playlist = await self._provider.get_playlist_tracks(playlist_id=str(kind))
        if not playlist:
            return None
        await self._session.merge(playlist)
        return playlist

    async def get_artist(self, artist_id: str) -> entities.Artist | None:
        return await self._provider.get_artist_details(artist_id=artist_id)

    async def get_album(self, album_id: str) -> entities.Album | None:
        return await self._provider.get_album_tracks(album_id=album_id)

    async def get_user_albums(self, use_cache: bool = True) -> list[entities.Album]:
        if use_cache:
            stmt = select(entities.Album).options(selectinload(entities.Album.artists))  # pyright: ignore
            result = await self._session.execute(stmt)
            db_albums = list(result.scalars().all())
            if db_albums:
                return db_albums
        albums = await self._provider.get_user_albums()
        if not albums:
            return []
        for album in albums:
            await self._session.merge(album)
        await self._session.commit()
        return albums
