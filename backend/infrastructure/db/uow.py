from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.contexts.catalog.infrastructure.repository import CatalogRepository
from shared.domain.interfaces import TrackProvider


class SqlAlchemyUnitOfWork:
    def __init__(
        self, session_factory: async_sessionmaker, track_provider: TrackProvider
    ) -> None:
        self._session_factory = session_factory
        self._track_provider = track_provider

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":  # pyright: ignore
        logger.debug("Начало работал модуля UnitOfWork")
        self._session = self._session_factory()
        self.catalog_repository = CatalogRepository(
            session=self._session, provider=self._track_provider
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            logger.error(f"Ошибка в работе UnitOfWork: {exc_val}")
            await self._session.rollback()
        await self._session.close()
        logger.debug("Конец работы модуля UnitOfWork")

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
