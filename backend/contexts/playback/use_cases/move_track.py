from loguru import logger

from shared.domain.interfaces import PlaybackController, QueueManager, TrackStreamer


class MoveTrackUseCase:
    def __init__(
        self,
        queue_manager: QueueManager,
        player: PlaybackController,
        streamer: TrackStreamer,
    ):
        self.queue_manager = queue_manager
        self.player = player
        self.streamer = streamer

    async def execute(self, direction: str) -> None:
        logger.info(f"Переключение трека: {direction}")

        if direction == "next":
            track = await self.queue_manager.next_track()
        else:
            track = await self.queue_manager.prev_track()

        if track:
            stream_url = await self.streamer.get_stream_url(track.id)
            await self.player.play(stream_url)
            logger.info(f"Начато воспроизведение следующего трека: {track.title}")
        else:
            logger.warning(f"Больше нет треков в направлении {direction}")
