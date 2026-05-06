from collections.abc import AsyncIterable
from pathlib import Path

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.infrastructure.db.base import metadata_obj
from backend.infrastructure.db.mapper import start_mappers
from backend.infrastructure.db.uow import SqlAlchemyUnitOfWork
from shared.domain.interfaces import TrackProvider


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_engine(self) -> AsyncIterable[AsyncEngine]:
        db_path = Path.home() / ".config" / "ym-cli" / "library.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        start_mappers()
        async with engine.begin() as conn:
            await conn.run_sync(metadata_obj.create_all)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def get_session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(bind=engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_uow(
        self, session_factory: async_sessionmaker[AsyncSession], provider: TrackProvider
    ) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(
            session_factory=session_factory, track_provider=provider
        )
