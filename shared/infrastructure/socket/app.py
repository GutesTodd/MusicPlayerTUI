import asyncio
import contextvars
import json
from collections.abc import Callable

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection
from loguru import logger
from pydantic import BaseModel, ValidationError

from shared.domain.common import BaseCommand

from .router import SocketRouter

request_container_var: contextvars.ContextVar[AsyncContainer] = contextvars.ContextVar(
    "dishka_request_container"
)


def _get_container(*args, **kwargs):
    return request_container_var.get()


def setup_dishka(container: AsyncContainer, app: "SocketApp"):
    app.container = container
    for route_path, (func, model_class) in app.routes.items():
        wrapped_func = wrap_injection(
            func=func,
            container_getter=_get_container,
            is_async=True,
            remove_depends=True,
        )
        app.routes[route_path] = (wrapped_func, model_class)


class SocketApp:
    container: AsyncContainer | None

    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.routes: dict[str, tuple[Callable, type[BaseCommand]]] = {}

    def include_router(self, router: SocketRouter):
        for route_path, handler_data in router.routes.items():
            if route_path in self.routes:
                logger.warning(f"Конфликт маршрутов! Перезапись {route_path}")
            self.routes[route_path] = handler_data

    async def serve(self):
        server = await asyncio.start_server(
            self._handle_client, host=self.host, port=self.port
        )

        logger.success(f"Сервер запущен на tcp://{self.host}:{self.port}")
        async with server:
            await server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        logger.info("TUI Клиент подключился")
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                try:
                    raw_payload = json.loads(data.decode("utf-8").strip())
                    action = raw_payload.get("action", "")

                    if action not in self.routes:
                        logger.error(f"Маршрут не найден: {action}")
                        await self._send_json(
                            writer,
                            {
                                "status": "error",
                                "error": "Route Not Found",
                                "route": action,
                            },
                        )
                        continue

                    func, model_class = self.routes[action]
                    command_obj = model_class.model_validate(raw_payload)

                    if hasattr(self, "container") and self.container:
                        async with self.container() as request_container:
                            token = request_container_var.set(request_container)
                            try:
                                response = await func(command_obj)
                            finally:
                                request_container_var.reset(token)
                    else:
                        response = await func(command_obj)

                    if isinstance(response, BaseModel):
                        await self._send_raw(writer, response.model_dump_json())
                    elif isinstance(response, list):
                        serialized_list = [
                            item.model_dump() if isinstance(item, BaseModel) else item
                            for item in response
                        ]
                        await self._send_json(
                            writer, {"status": "ok", "data": serialized_list}
                        )
                    else:
                        await self._send_json(
                            writer, {"status": "ok", "data": response}
                        )

                except ValidationError as e:
                    logger.error(f"Ошибка валидации Pydantic: {e.errors()}")
                    await self._send_json(
                        writer,
                        {
                            "status": "error",
                            "error": "Validation Failed",
                            "details": e.errors(),
                        },
                    )
                except json.JSONDecodeError:
                    logger.error("Получен невалидный байт-код JSON")
                    await self._send_json(
                        writer, {"status": "error", "error": "Invalid JSON bytes"}
                    )
                except Exception as e:
                    logger.exception("Внутренняя ошибка сервера")
                    await self._send_json(
                        writer,
                        {
                            "status": "error",
                            "error": "Internal Server Error",
                            "message": str(e),
                        },
                    )

        except asyncio.CancelledError:
            pass
        finally:
            logger.info("TUI Клиент отключился")
            writer.close()
            await writer.wait_closed()

    async def _send_json(self, writer: asyncio.StreamWriter, data: dict):
        await self._send_raw(writer, json.dumps(data))

    async def _send_raw(self, writer: asyncio.StreamWriter, json_str: str):
        writer.write((json_str + "\n").encode("utf-8"))
        await writer.drain()
