import asyncio
import json
from typing import Any
from loguru import logger


class SocketClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888) -> None:
        self._host = host
        self._port = port

    async def _send(self, reader, writer, action: str, payload: dict | None) -> dict[str, Any] | None:
        if payload is None:
            payload = {}

        request = {"action": action, **payload}
        try:
            data = json.dumps(request) + "\n"
            writer.write(data.encode("utf-8"))
            await writer.drain()
            response_data = await reader.readline()
            writer.close()
            await writer.wait_closed()
            if not response_data:
                return {"status": "error", "payload": "Пустой ответ"}
            return json.loads(response_data.decode("utf-8"))
        except Exception:
            logger.exception("Ошибка при общении с сервером")
            return None

    async def send_command(
        self, action: str, payload: dict | None = None
    ) -> dict[str, Any] | None:
        try:
            reader, writer = await asyncio.open_connection(self._host, self._port)
            return await self._send(reader, writer, action, payload)
        except ConnectionRefusedError:
            logger.error(f"Сервер не запущен на {self._host}:{self._port}")
            return {"status": "error", "error": "Сервер недоступен"}
        except Exception:
            logger.exception("Ошибка при открытии соединения")
            return None


class UnixSocketClient(SocketClient):
    def __init__(self, path: str = "/tmp/yandex_music_backend.sock") -> None:
        self._path = path

    async def send_command(
        self, action: str, payload: dict | None = None
    ) -> dict[str, Any] | None:
        try:
            reader, writer = await asyncio.open_unix_connection(self._path)
            return await self._send(reader, writer, action, payload)
        except (FileNotFoundError, ConnectionRefusedError):
            logger.error(f"Сервер не запущен на unix socket: {self._path}")
            return {"status": "error", "error": "Сервер недоступен"}
        except Exception:
            logger.exception("Ошибка при открытии unix соединения")
            return None
