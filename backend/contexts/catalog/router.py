from dishka import FromDishka

from backend.infrastructure.db.uow import SqlAlchemyUnitOfWork
from shared.domain import entities
from shared.domain.commands import (
    CatalogCommand,
    GetAlbumCatalogCommand,
    GetArtistCatalogCommand,
    GetPlaylistTracksCommand,
    GetUserPlaylistsCommand,
)
from shared.infrastructure.socket.app import SocketRouter

router = SocketRouter(CatalogCommand)


@router.handler
async def get_album(
    cmd: GetAlbumCatalogCommand, uow: FromDishka[SqlAlchemyUnitOfWork]
) -> entities.Album | None:
    async with uow as uow_instance:
        return await uow_instance.catalog_repository.get_album(album_id=cmd.album_id)


@router.handler
async def get_artist(
    cmd: GetArtistCatalogCommand, uow: FromDishka[SqlAlchemyUnitOfWork]
) -> entities.Artist | None:
    async with uow as uow_instance:
        return await uow_instance.catalog_repository.get_artist(artist_id=cmd.artist_id)


@router.handler
async def get_user_playlists(
    cmd: GetUserPlaylistsCommand, uow: FromDishka[SqlAlchemyUnitOfWork]
) -> list[entities.Playlist]:
    async with uow as uow_instance:
        return await uow_instance.catalog_repository.get_playlists()


@router.handler
async def get_playlist(
    cmd: GetPlaylistTracksCommand, uow: FromDishka[SqlAlchemyUnitOfWork]
) -> entities.Playlist | None:
    async with uow as uow_instance:
        if ":" in cmd.playlist_id:
            uid_str, kind_str = cmd.playlist_id.split(":")
            return await uow_instance.catalog_repository.get_playlist_with_tracks(
                uid=int(uid_str), kind=int(kind_str)
            )
        return await uow_instance.catalog_repository.get_playlist_with_tracks(
            uid=0, kind=int(cmd.playlist_id)
        )
