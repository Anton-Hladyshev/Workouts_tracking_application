import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import settings
from repositories.training_repository import TrainingRepository

async_engine = create_async_engine(
    url=settings.get_db_url_with_asyncpg, 
    echo=True,
    pool_size=5,
    max_overflow=10
)

async_session_factory = async_sessionmaker(bind=async_engine)

class UnitOfWork:
    def __init__(self, session_factory: Callable[[], AsyncSession] = async_session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()
        self.training_repository = TrainingRepository(session=self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
