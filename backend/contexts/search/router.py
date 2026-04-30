from dishka import FromDishka
from loguru import logger

from shared.domain import entities
from shared.domain.commands import (
    SearchAlbumsCommand,
    SearchArtistsCommand,
    SearchCommand,
    SearchTracksCommand,
)
from shared.domain.interfaces import TrackSearcher
from shared.infrastructure.socket.app import SocketRouter

router = SocketRouter(SearchCommand)


@router.handler
async def search_tracks(
    cmd: SearchTracksCommand, searcher: FromDishka[TrackSearcher]
) -> list[entities.Track] | None:
    logger.debug(f"Команда: {cmd}")
    return await searcher.search_tracks(query=cmd.query, limit=cmd.limit)


@router.handler
async def search_albums(
    cmd: SearchAlbumsCommand, searcher: FromDishka[TrackSearcher]
) -> list[entities.Album] | None:
    return await searcher.search_albums(query=cmd.query, limit=cmd.limit)


@router.handler
async def search_artists(
    cmd: SearchArtistsCommand, searcher: FromDishka[TrackSearcher]
) -> list[entities.Artist] | None:
    return await searcher.search_artists(query=cmd.query, limit=cmd.limit)
