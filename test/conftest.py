import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
# from unittest.mock import patch, AsyncMock, Mock
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncConnection,
    AsyncTransaction,
)


from app.main import app
from app.database.base import Base
from app.core.config import settings
from app.api.models.users import User  #noqa: F401
from app.dependencies import get_session

BASE_PATH: str = "app.api.services.auth_service"


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    sql_stmt: str = """
        CREATE OR REPLACE FUNCTION uuid_generate_v7()
               RETURNS UUID
               LANGUAGE SQL
               VOLATILE
               AS $$
                SELECT encode(
                    set_bit(
                        set_bit(
                            overlay(
                                uuid_send(gen_random_uuid())
                                placing substring(int8send(floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint) FROM 3)
                                FROM 1 FOR 6
                            ),
                            52, 1
                        ),
                        53, 1
                    ),
                    'hex'
                )::uuid
               $$;
    """
    async_db_engine: AsyncEngine = create_async_engine(
        url=settings.ASYNC_TEST_DB_URL, poolclass=NullPool
    )

    async with async_db_engine.begin() as conn:
        await conn.execute(text(sql_stmt))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)

    yield async_db_engine

    async with async_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_db_engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine: AsyncEngine):
    async_connection: AsyncConnection = await async_engine.connect()
    async_transaction: AsyncTransaction = await async_connection.begin()

    session = async_sessionmaker(
        bind=async_connection,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async_session: AsyncSession = session()
    yield async_session

    await async_session.close()
    await async_transaction.rollback()
    await async_connection.close()


@pytest_asyncio.fixture
async def async_client(async_session: AsyncSession):
    async def get_test_session():
        return async_session

    app.dependency_overrides[get_session] = get_test_session

    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://localhost/api"
    ) as client:
        yield client