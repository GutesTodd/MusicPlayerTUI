from sqlalchemy.orm import relationship

from shared.domain.entities import Album, Artist, Playlist, Track
from .base import mapper_registry
from .schemas import (
    album_artists_table,
    albums_table,
    artists_table,
    playlist_tracks_table,
    playlists_table,
    track_albums_table,
    track_artists_table,
    tracks_table,
)


def start_mappers():
    mapper_registry.map_imperatively(
        Artist,
        artists_table,
        properties={
            "details": relationship(
                # We don't map ArtistDetails for now as it's complex,
                # but we can leave it as None or handle later.
                # For now, we only map basic Artist info.
                uselist=False,
                viewonly=True,
            )
        },
    )

    mapper_registry.map_imperatively(
        Album,
        albums_table,
        properties={
            "artists": relationship(
                Artist,
                secondary=album_artists_table,
                collection_class=list,
                lazy="selectin",
            ),
            "tracks": relationship(
                Track,
                secondary=track_albums_table,
                collection_class=list,
                lazy="selectin",
            ),
        },
    )

    mapper_registry.map_imperatively(
        Track,
        tracks_table,
        properties={
            "artists": relationship(
                Artist,
                secondary=track_artists_table,
                collection_class=list,
                lazy="selectin",
            ),
            "albums": relationship(
                Album,
                secondary=track_albums_table,
                collection_class=list,
                lazy="selectin",
                viewonly=True,
            ),
        },
    )

    mapper_registry.map_imperatively(
        Playlist,
        playlists_table,
        properties={
            "tracks": relationship(
                Track,
                secondary=playlist_tracks_table,
                order_by=playlist_tracks_table.c.position,
                collection_class=list,
                lazy="selectin",
            )
        },
    )
