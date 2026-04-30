from loguru import logger
from yandex_music import ClientAsync
from yandex_music.exceptions import YandexMusicError


class YandexStreamer:
    def __init__(self, client: ClientAsync):
        self._client = client

    async def get_stream_url(self, track_id: int) -> str:
        try:
            download_info_list = await self._client.tracks_download_info(
                track_id=track_id, get_direct_links=True
            )
            if not download_info_list:
                raise RuntimeError(f"Для трека {track_id} нет доступных ссылок.")
            download_info_list.sort(key=lambda info: info.bitrate_in_kbps, reverse=True)
            best_quality_info = download_info_list[0]
            direct_link = best_quality_info.direct_link
            if not direct_link:
                direct_link = await best_quality_info.get_direct_link_async()
            logger.info(
                f"Получена ссылка для трека {track_id} ({best_quality_info.bitrate_in_kbps} kbps)"  # noqa: E501
            )
            return direct_link

        except YandexMusicError as e:
            logger.error(f"Ошибка API Яндекса при получении стрима: {e}")
            raise RuntimeError(
                "Не удалось подключиться к серверам Яндекса для получения трека."
            ) from e
