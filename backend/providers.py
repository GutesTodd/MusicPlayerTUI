from typing import AsyncIterable
from dishka import Provider, Scope, provide
from loguru import logger
from yandex_music import ClientAsync

from backend.contexts.playback.domain.queue_manager import InMemoryQueueManager
from backend.infrastructure.players.mpv import MpvAudioPlayer
from backend.infrastructure.yandex.searcher import YandexSearcher
from backend.infrastructure.yandex.streamer import YandexStreamer
from backend.infrastructure.yandex.track_provider import YandexTrackProvider
from backend.infrastructure.config.service import ConfigService
from backend.contexts.playback.use_cases.play_media import PlayMediaUseCase
from backend.contexts.playback.use_cases.move_track import MoveTrackUseCase
from backend.contexts.playback.use_cases.get_queue import GetQueueUseCase
from backend.contexts.auth.domain import AuthSessionStore
from backend.contexts.auth.use_cases import YandexDeviceAuthFlow
from shared.domain.interfaces import (
    PlaybackController,
    PlaybackMonitor,
    QueueManager,
    TrackSearcher,
    TrackStreamer,
    TrackProvider,
    VolumeController,
)


class YandexConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_config_service(self) -> ConfigService:
        return ConfigService()


class AuthProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_auth_store(self) -> AuthSessionStore:
        return AuthSessionStore()

    @provide(scope=Scope.APP)
    def provide_auth_flow(
        self, store: AuthSessionStore, config: ConfigService
    ) -> YandexDeviceAuthFlow:
        return YandexDeviceAuthFlow(store, config)


class YandexProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_client(self, config: ConfigService) -> AsyncIterable[ClientAsync]:
        token = config.get_token()
        if not token:
            logger.warning(
                "Токен Яндекс.Музыки не найден. Клиент запущен в режиме авторизации."
            )
            client = ClientAsync()
        else:
            logger.info("Инициализация клиента Яндекс.Музыки с токеном из конфига")
            client = ClientAsync(token)
            try:
                await client.init()
            except Exception as e:
                logger.error(
                    f"Ошибка инициализации клиента: {e}. Возможно, токен протух."
                )
                client = ClientAsync()

        yield client

    @provide(scope=Scope.APP)
    def get_searcher(self, client: ClientAsync) -> TrackSearcher:
        return YandexSearcher(client)

    @provide(scope=Scope.APP)
    def get_streamer(self, client: ClientAsync) -> TrackStreamer:
        return YandexStreamer(client)

    @provide(scope=Scope.APP)
    def get_track_provider(self, client: ClientAsync) -> TrackProvider:
        return YandexTrackProvider(client)


class PlayerProvider(Provider):
    @provide(scope=Scope.APP)
    def get_player(self) -> MpvAudioPlayer:
        logger.info("Инициализация аудио-плеера MPV")
        return MpvAudioPlayer()

    @provide(scope=Scope.APP)
    def get_playback_controller(self, player: MpvAudioPlayer) -> PlaybackController:
        return player

    @provide(scope=Scope.APP)
    def get_volume_controller(self, player: MpvAudioPlayer) -> VolumeController:
        return player

    @provide(scope=Scope.APP)
    def get_playback_monitor(self, player: MpvAudioPlayer) -> PlaybackMonitor:
        return player

    @provide(scope=Scope.APP)
    def get_queue_manager(self) -> QueueManager:
        return InMemoryQueueManager()


class UseCaseProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_play_media_use_case(
        self,
        provider: TrackProvider,
        queue_manager: QueueManager,
        player: MpvAudioPlayer,
        streamer: TrackStreamer,
    ) -> PlayMediaUseCase:
        return PlayMediaUseCase(
            provider=provider,
            queue_manager=queue_manager,
            player=player,
            streamer=streamer,
        )

    @provide
    def get_move_track_use_case(
        self,
        queue_manager: QueueManager,
        player: MpvAudioPlayer,
        streamer: TrackStreamer,
    ) -> MoveTrackUseCase:
        return MoveTrackUseCase(
            queue_manager=queue_manager, player=player, streamer=streamer
        )

    @provide
    def get_get_queue_use_case(self, queue_manager: QueueManager) -> GetQueueUseCase:
        return GetQueueUseCase(queue_manager=queue_manager)
