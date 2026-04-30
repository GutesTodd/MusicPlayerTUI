from ui.utils.socket_client import SocketClient
from ui.viewmodels.base import BaseViewModel


class QueueViewModel(BaseViewModel):
    def __init__(self, client: SocketClient):
        super().__init__()
        self._client = client
        self.tracks: list = []
        self.current_track_id: str | int | None = None

    async def load_queue(self):
        self.is_loading = True
        self.notify()

        response = await self._client.send_command("playback.get_queue")
        if response and response.get("status") == "ok":
            data = response.get("data", {})
            self.tracks = data.get("tracks", [])
            self.current_track_id = data.get("current_id")

        self.is_loading = False
        self.notify()

    async def next_track(self):
        await self._client.send_command("playback.next")
        await self.load_queue()

    async def prev_track(self):
        await self._client.send_command("playback.prev")
        await self.load_queue()
