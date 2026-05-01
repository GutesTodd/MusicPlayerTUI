from typing import Annotated, Literal

from pydantic import Field

from shared.domain.common import BaseCommand


class SearchCommand(BaseCommand):
    action: Literal["search"] = "search"
    query: str
    limit: int = Field(default=20, ge=1, le=100)


class SearchTracksCommand(SearchCommand):
    action: Literal["search.tracks"] = "search.tracks"


class SearchAlbumsCommand(SearchCommand):
    action: Literal["search.albums"] = "search.albums"


class SearchArtistsCommand(SearchCommand):
    action: Literal["search.artists"] = "search.artists"


class PlaybackCommand(BaseCommand):
    action: Literal["playback"] = "playback"


class PauseCommand(PlaybackCommand):
    action: Literal["playback.pause"] = "playback.pause"


class ResumeCommand(PlaybackCommand):
    action: Literal["playback.resume"] = "playback.resume"


class SetVolumeCommand(PlaybackCommand):
    action: Literal["playback.set_volume"] = "playback.set_volume"
    volume_level: int = Field(ge=0, le=100)


class NextTrackCommand(PlaybackCommand):
    action: Literal["playback.next"] = "playback.next"


class PrevTrackCommand(PlaybackCommand):
    action: Literal["playback.prev"] = "playback.prev"


class GetQueueCommand(PlaybackCommand):
    action: Literal["playback.get_queue"] = "playback.get_queue"


class ModePlayCommand(PlaybackCommand):
    action: Literal["playback.set_play_mode"] = "playback.set_play_mode"
    modes: Literal["none", "all", "one"]


class SeekCommand(PlaybackCommand):
    action: Literal["playback.seek"] = "playback.seek"
    position_ms: int


class PlayMyWaveCommand(BaseCommand):
    action: Literal["my_wave"] = "my_wave"
    mood: str | None = None


class AuthCommand(BaseCommand):
    action: Literal["auth"] = "auth"


class GetAuthCodeCommand(AuthCommand):
    action: Literal["auth.get_auth_code"] = "auth.get_auth_code"
    platform: str


class GetAuthStatusCommand(AuthCommand):
    action: Literal["auth.get_status_auth"] = "auth.get_status_auth"
    platform: str


class PlayMediaCommand(PlaybackCommand):
    action: Literal["playback.play_media"] = "playback.play_media"
    media_id: str | int
    media_type: Literal["track", "album", "playlist", "artist"]


AnyCommand = Annotated[
    SearchCommand
    | PlayMyWaveCommand
    | PlayMediaCommand
    | PauseCommand
    | ResumeCommand
    | SetVolumeCommand
    | NextTrackCommand
    | PrevTrackCommand
    | GetQueueCommand
    | GetAuthCodeCommand
    | GetAuthStatusCommand,
    Field(discriminator="action"),
]
