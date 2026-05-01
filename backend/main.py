import asyncio
import contextlib
import sys
from pathlib import Path

from dishka import make_async_container
from loguru import logger

from backend.contexts.auth.router import router as auth_router
from backend.contexts.catalog.router import router as catalog_router
from backend.contexts.playback.router import router as playback_router
from backend.contexts.search.router import router as search_router
from backend.providers import (
    AuthProvider,
    PlayerProvider,
    UseCaseProvider,
    YandexConfigProvider,
    YandexProvider,
)
from shared.infrastructure.socket.app import SocketApp, setup_dishka


def setup_logger():
    """Настройка логгера для продакшен-демона."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",  # noqa: E501
        level="DEBUG",
    )
    logger.add(
        Path("log/yandex_music_backend/daemon.log").expanduser(),
        rotation="10 MB",
        level="INFO",
    )


def create_app() -> SocketApp:
    """Создает инстанс сервера и регистрирует все маршруты."""
    app = SocketApp(host="127.0.0.1", port=8888)

    app.include_router(search_router)
    app.include_router(playback_router)
    app.include_router(auth_router)
    app.include_router(catalog_router)

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
    for route in app.routes:
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
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
