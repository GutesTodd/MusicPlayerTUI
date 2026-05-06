from loguru import logger

from shared.domain.commands import PlayMediaCommand
from shared.domain.factories import QueueFactory
from shared.domain.interfaces import (
    PlaybackController,
    QueueManager,
    TrackProvider,
    TrackStreamer,
)


class PlayMediaUseCase:
    def __init__(
        self,
        provider: TrackProvider,
        queue_manager: QueueManager,
        player: PlaybackController,
        streamer: TrackStreamer,
    ):
        self.provider = provider
        self.queue_manager = queue_manager
        self.player = player
        self.streamer = streamer

    async def execute(self, cmd: PlayMediaCommand) -> None:
        logger.info(
            f"Запуск сценария воспроизведения медиа: {cmd.media_type} (id={cmd.media_id})"  # noqa: E501
        )

        source = None
        if cmd.media_type == "track":
            source = await self.provider.get_track(int(cmd.media_id))
        elif cmd.media_type == "album":
            source = await self.provider.get_album_tracks(str(cmd.media_id))
        elif cmd.media_type == "playlist":
            source = await self.provider.get_playlist_tracks(str(cmd.media_id))
        elif cmd.media_type == "artist":
            source = await self.provider.get_artist_details(str(cmd.media_id))

        if not source:
            logger.error(
                f"Не удалось получить данные для {cmd.media_type} {cmd.media_id}"
            )
            return

        queue = await QueueFactory.create_queue(source)
        if cmd.start_from_track_id:
            current_node = queue.head
            while current_node:
                if str(current_node.track.id) == str(cmd.start_from_track_id):
                    queue.current = current_node
                    break
                current_node = current_node.next
        await self.queue_manager.set_queue(queue)
        current_track = await self.queue_manager.get_current()
        if current_track:
            stream_url = await self.streamer.get_stream_url(current_track.id)
            await self.player.play(stream_url)
            logger.info(f"Начато воспроизведение трека: {current_track.title}")
