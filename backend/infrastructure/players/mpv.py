import mpv


class MpvAudioPlayer:
    def __init__(self) -> None:
        self._player = mpv.MPV(ytdl=False, video=False)

    async def play(self, url: str) -> None:
        self._player.play(url)

    async def pause(self) -> None:
        self._player.pause = True

    async def resume(self) -> None:
        self._player.pause = False

    async def set_volume(self, volume_level: int) -> None:
        self._player.volume = volume_level

    def set_position_ms(self, time_pos: int) -> None:
        self._player.time_pos = time_pos / 1000

    def get_position_ms(self) -> int:
        pos = self._player.time_pos
        return int(pos * 1000) if pos else 0

    def is_playing(self) -> bool:
        return not self._player.pause and self._player.time_pos is not None
