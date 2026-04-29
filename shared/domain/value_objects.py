from shared.domain.common import BaseValueObject
from shared.domain.entities import Track


class PlayerState(BaseValueObject):
    current_track: Track | None = None
    is_playing: bool = False
    volume: int = 50
    position_ms: int = 0

    @property
    def progress_percent(self):
        if not self.current_track or self.current_track.duration_ms == 0:
            return 0
        return (self.position_ms / self.current_track.duration_ms) * 100
