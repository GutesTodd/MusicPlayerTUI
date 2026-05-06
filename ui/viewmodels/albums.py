from loguru import logger
from ui.utils.socket_client import SocketClient
from ui.viewmodels.base import BaseViewModel
from shared.domain.entities import Album

class AlbumListViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.albums: list[Album] = []
        
    async def load_user_albums(self):
        """Загрузка списка альбомов пользователя."""
        self.is_loading = True
        self.notify()
        
        response = await self._client.send_command("catalog.get_user_albums")
        
        if response and isinstance(response, list):
            self.albums = []
            for a_data in response:
                try:
                    album = Album.model_validate(a_data)
                    self.albums.append(album)
                except Exception as e:
                    logger.error(f"Ошибка валидации альбома: {e}")
            
        self.is_loading = False
        self.notify()
