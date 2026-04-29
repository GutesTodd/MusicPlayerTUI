import asyncio
import sys
import os
from loguru import logger
from dishka import make_async_container

from shared.infrastructure.socket.app import SocketApp, setup_dishka

from backend.providers import (
    YandexConfigProvider,
    YandexProvider,
    PlayerProvider,
    UseCaseProvider,
    AuthProvider,
)

from backend.contexts.search.router import router as search_router
from backend.contexts.playback.router import router as playback_router
from backend.contexts.auth.router import router as auth_router


def setup_logger():
    """Настройка логгера для продакшен-демона."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )
    logger.add(
        os.path.expanduser("log/yandex_music_backend/daemon.log"),
        rotation="10 MB",
        level="INFO",
    )


def create_app() -> SocketApp:
    """Создает инстанс сервера и регистрирует все маршруты."""
    app = SocketApp(host="127.0.0.1", port=8888)

    app.include_router(search_router)
    app.include_router(playback_router)
    app.include_router(auth_router)

    return app


async def main():
    setup_logger()
    logger.info("Инициализация Yandex Music Backend...")
    app = create_app()
    logger.info("Сборка графа зависимостей (Dishka)...")
    container = make_async_container(
        YandexConfigProvider(),
        YandexProvider(),
        PlayerProvider(),
        UseCaseProvider(),
        AuthProvider(),
    )
    setup_dishka(container, app)
    logger.info("Зарегистрированные маршруты:")
    for route in app.routes.keys():
        logger.info(f"  -> {route}")
    try:
        await app.serve()
    except asyncio.CancelledError:
        logger.warning("Получен сигнал SIGINT. Остановка демона...")
    except Exception:
        logger.exception("Критическая ошибка сервера")
    finally:
        logger.info("Закрытие DI-контейнера и освобождение ресурсов...")
        await container.close()
        logger.info("Демон успешно остановлен.")


if __name__ == "__main__":
    try:
        import uvloop

        uvloop.install()
        logger.info("uvloop активирован")
    except ImportError:
        pass
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
