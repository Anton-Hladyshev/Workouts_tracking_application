import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from models.models import Base
import logging
from app.main import app
# make a fixture to create the test database, insert some test data, and drop the database after tests are done

logging.basicConfig(level=logging.DEBUG)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_database():
    engine = create_async_engine(
        settings.get_db_url_with_asyncpg_test, echo=True
    )

    logging.debug("Creating test database...")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.drop_all
            )
            await conn.run_sync(
                Base.metadata.create_all
            )
        logging.debug("Test database created.")
    except Exception as e:
        logging.error(f"Error creating test database: {e}")
        raise

    yield
    
    logging.debug("Disposing test database...")
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        logging.debug("Yielding AsyncClient for tests...")
        yield ac
    logging.debug("Closing AsyncClient...")

