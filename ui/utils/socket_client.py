import asyncio
import contextlib
import json
from typing import Any

from loguru import logger


class SocketClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888) -> None:
        self._host = host
        self._port = port
        self._timeout = 5.0  # Таймаут для всех операций

    async def _send(
        self, reader, writer, action: str, payload: dict | None
    ) -> dict[str, Any] | None:
        if payload is None:
            payload = {}

        request = {"action": action, **payload}
        try:
            data = json.dumps(request) + "\n"
            writer.write(data.encode("utf-8"))
            await asyncio.wait_for(writer.drain(), timeout=self._timeout)

            response_data = await asyncio.wait_for(
                reader.readline(), timeout=self._timeout
            )

            writer.close()

            with contextlib.suppress(Exception):
                await writer.wait_closed()

            if not response_data:
                return {"status": "error", "payload": "Пустой ответ"}
            return json.loads(response_data.decode("utf-8"))
        except TimeoutError:
            logger.error(f"Таймаут при выполнении команды {action}")
            return None
        except Exception:
            logger.exception("Ошибка при общении с сервером")
            return None

    async def send_command(
        self, action: str, payload: dict | None = None
    ) -> dict[str, Any] | None:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=self._timeout
            )
            return await self._send(reader, writer, action, payload)
        except TimeoutError:
            logger.error(f"Не удалось подключиться к серверу за {self._timeout}с")
            return {"status": "error", "error": "Таймаут подключения"}
        except ConnectionRefusedError:
            logger.error(f"Сервер не запущен на {self._host}:{self._port}")
            return {"status": "error", "error": "Сервер недоступен"}
        except Exception:
            logger.exception("Ошибка при открытии соединения")
            return None
