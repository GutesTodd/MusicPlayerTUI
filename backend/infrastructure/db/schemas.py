from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)

from .base import metadata_obj

tracks_table = Table(
    "tracks",
    metadata_obj,
    Column("id", String, primary_key=True),
    Column("title", String),
    Column("duration_ms", BigInteger),
    Column("cover_uri", String, nullable=True),
    Column("is_explicit", Boolean, default=False),
)

artists_table = Table(
    "artists",
    metadata_obj,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("cover_uri", String, nullable=True),
)

albums_table = Table(
    "albums",
    metadata_obj,
    Column("id", String, primary_key=True),
    Column("title", String),
    Column("type", String),
    Column("year", Integer, nullable=True),
    Column("cover_uri", String, nullable=True),
)

track_artists_table = Table(
    "track_artists",
    metadata_obj,
    Column("track_id", String, ForeignKey("tracks.id"), primary_key=True),
    Column("artist_id", String, ForeignKey("artists.id"), primary_key=True),
)

track_albums_table = Table(
    "track_albums",
    metadata_obj,
    Column("track_id", String, ForeignKey("tracks.id"), primary_key=True),
    Column("album_id", String, ForeignKey("albums.id"), primary_key=True),
)

album_artists_table = Table(
    "album_artists",
    metadata_obj,
    Column("album_id", String, ForeignKey("albums.id"), primary_key=True),
    Column("artist_id", String, ForeignKey("artists.id"), primary_key=True),
)

playlists_table = Table(
    "playlists",
    metadata_obj,
    Column("uid", BigInteger),
    Column("kind", BigInteger),
    Column("title", String),
    Column("track_count", Integer),
    Column("description", String, nullable=True),
    Column("owner_id", String, nullable=True),
    Column("owner_name", String, nullable=True),
    Column("cover_uri", String, nullable=True),
    PrimaryKeyConstraint("uid", "kind"),
)

playlist_tracks_table = Table(
    "playlists_tracks",
    metadata_obj,
    Column("playlist_uid", BigInteger),
    Column("playlist_kind", BigInteger),
    Column("track_id", String, ForeignKey("tracks.id")),
    Column("position", Integer),
    PrimaryKeyConstraint("playlist_uid", "playlist_kind", "position"),
    ForeignKeyConstraint(
        ["playlist_uid", "playlist_kind"], ["playlists.uid", "playlists.kind"]
    ),
)
