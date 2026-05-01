from dishka import FromDishka

from shared.domain import entities
from shared.domain.commands import (
    CatalogCommand,
    GetAlbumCatalogCommand,
    GetArtistCatalogCommand,
)
from shared.domain.interfaces import TrackProvider
from shared.infrastructure.socket.app import SocketRouter

router = SocketRouter(CatalogCommand)


@router.handler
async def get_album(
    cmd: GetAlbumCatalogCommand, provider: FromDishka[TrackProvider]
) -> entities.Album | None:
    return await provider.get_album_tracks(album_id=cmd.album_id)


@router.handler
async def get_artist(
    cmd: GetArtistCatalogCommand, provider: FromDishka[TrackProvider]
) -> entities.Artist | None:
    return await provider.get_artist_details(artist_id=cmd.artist_id)
