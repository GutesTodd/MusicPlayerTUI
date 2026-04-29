from pydantic import Field
from shared.domain.common import BaseEntity


class Artist(BaseEntity):
    name: str
    cover_uri: str | None = None


class Album(BaseEntity):
    title: str
    type: str
    artists: list[Artist] = Field(default_factory=list)
    year: int | None = None
    cover_uri: str | None = None
    tracks: list[Track] | None = None


class Track(BaseEntity):
    title: str
    duration_ms: int
    artists: list[Artist] = Field(default_factory=list)
    albums: list[Album] = Field(default_factory=list)
    is_explicit: bool = False
    cover_uri: str | None = None

    @property
    def duration_sec(self):
        return self.duration_ms // 1000

    @property
    def display_name(self):
        return ", ".join([artist.name for artist in self.artists])


class Playlist(BaseEntity):
    uid: int
    kind: int
    title: str
    track_count: int
    cover_uri: str | None = None
    tracks: list[Track] | None = None


class QueueNode(BaseEntity):
    track: Track
    next: QueueNode | None = None
    prev: QueueNode | None = None


class TrackQueue(BaseEntity):
    head: QueueNode | None = None
    tail: QueueNode | None = None
    current: QueueNode | None = None
    length: int = 0
