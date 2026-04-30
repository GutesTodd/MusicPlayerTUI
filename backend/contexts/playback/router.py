from dishka import FromDishka

from shared.domain.commands import (
    GetQueueCommand,
    ModePlayCommand,
    NextTrackCommand,
    PauseCommand,
    PlaybackCommand,
    PlayMediaCommand,
    PrevTrackCommand,
    ResumeCommand,
    SetVolumeCommand,
)
from shared.domain.interfaces import PlaybackController, QueueManager, VolumeController
from shared.infrastructure.socket.app import SocketRouter

from .use_cases.get_queue import GetQueueUseCase
from .use_cases.move_track import MoveTrackUseCase
from .use_cases.play_media import PlayMediaUseCase

router = SocketRouter(PlaybackCommand)


@router.handler
async def get_queue(
    cmd: GetQueueCommand, use_case: FromDishka[GetQueueUseCase]
) -> dict:
    return await use_case.execute()


@router.handler
async def next_track(
    cmd: NextTrackCommand, use_case: FromDishka[MoveTrackUseCase]
) -> bool:
    await use_case.execute(direction="next")
    return True


@router.handler
async def prev_track(
    cmd: PrevTrackCommand, use_case: FromDishka[MoveTrackUseCase]
) -> bool:
    await use_case.execute(direction="prev")
    return True


@router.handler
async def play_media(
    cmd: PlayMediaCommand, use_case: FromDishka[PlayMediaUseCase]
) -> bool:
    await use_case.execute(cmd)
    return True


@router.handler
async def set_volume(
    cmd: SetVolumeCommand, controller: FromDishka[VolumeController]
) -> bool:
    await controller.set_volume(volume_level=cmd.volume_level)
    return True


@router.handler
async def pause(cmd: PauseCommand, controller: FromDishka[PlaybackController]) -> bool:
    await controller.pause()
    return True


@router.handler
async def resume(
    cmd: ResumeCommand, controller: FromDishka[PlaybackController]
) -> bool:
    await controller.resume()
    return True


@router.handler
async def set_play_mode(cmd: ModePlayCommand, queue_manager: QueueManager): ...
