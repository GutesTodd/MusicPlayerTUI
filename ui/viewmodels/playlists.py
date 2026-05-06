from loguru import logger
from ui.utils.socket_client import SocketClient
from ui.viewmodels.base import BaseViewModel
from shared.domain.entities import Playlist

class PlaylistViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.playlists: list[Playlist] = []
        self.current_playlist: Playlist | None = None
        
    async def load_user_playlists(self):
        """Загрузка списка плейлистов пользователя."""
        self.is_loading = True
        self.notify()
        
        response = await self._client.send_command("catalog.get_user_playlists")
        
        if response and isinstance(response, list):
            self.playlists = []
            for p_data in response:
                try:
                    playlist = Playlist.model_validate(p_data)
                    self.playlists.append(playlist)
                except Exception as e:
                    logger.error(f"Ошибка валидации плейлиста: {e}")
            
            # Сортировка: "Мне нравится" (или Любимое) всегда первый
            # В будущем лучше проверять по флагу от бэкенда
            self.playlists.sort(key=lambda x: x.title.lower() not in ["мне нравится", "favorites", "любимое"])
            
        self.is_loading = False
        self.notify()

    async def load_playlist_details(self, playlist_id: str):
        """Загрузка содержимого плейлиста."""
        self.is_loading = True
        self.current_playlist = None
        self.notify()
        
        response = await self._client.send_command("catalog.get_playlist", {"playlist_id": playlist_id})
        
        if response:
            try:
                self.current_playlist = Playlist.model_validate(response)
            except Exception as e:
                logger.error(f"Ошибка загрузки деталей плейлиста: {e}")
                self.set_error("Ошибка загрузки треков")
                
        self.is_loading = False
        self.notify()
