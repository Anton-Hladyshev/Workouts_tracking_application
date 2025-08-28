import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from db.database import ORMBase
from models.models import Base
import logging
from app.main import app
from schemas.schemas import UserAddDTO
# make a fixture to create the test database, insert some test data, and drop the database after tests are done

logging.basicConfig(level=logging.DEBUG)

@pytest_asyncio.fixture(scope="session")
async def engine():
    async_engine = create_async_engine(
        settings.get_db_url_with_asyncpg_test, 
        echo=True,
        pool_size=10
    )

    logging.debug("Creating test database...")

    try:
        async with async_engine.begin() as conn:
             # Завершаем текущую транзакцию
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

            logging.debug("Test tables created.")
            # Insert test data
        async with async_sessionmaker(bind=async_engine)() as session:
            test_user = UserAddDTO(
                name="Alice Johnson",
                email="alice.jhonson@example.com",
                password="SimplePass123",
                role="coach",
                age=30,
                gender="woman"
            )
            await ORMBase.register_new_user(user=test_user, session=session)
            logging.debug("Inserted test data into the database.")
        
    except Exception as e:
        logging.error(f"Error creating test tables: {e}")
        raise

    yield async_engine
    
    logging.debug("Disposing test database...")
    await async_engine.dispose()


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def db_session(engine):
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    logging.debug("Closing AsyncClient...")