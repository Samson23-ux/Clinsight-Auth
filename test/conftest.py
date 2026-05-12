import pytest_asyncio
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport, Response
from unittest.mock import patch, AsyncMock
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
from app.api import models  # noqa: F401
from app.dependencies import get_session


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    async_db_engine: AsyncEngine = create_async_engine(
        url=settings.ASYNC_TEST_DB_URL, poolclass=NullPool
    )

    async with async_db_engine.begin() as conn:
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


@pytest_asyncio.fixture
async def create_user(async_client: AsyncClient):
    path: str = "app.api.services.auth_service.send_email.delay"

    sign_up_payload: dict = {
        "email": "user@example.com",
        "password": "test_user_password",
        "last_name": "test_user_last_name",
        "first_name": "test_user_first_name",
    }

    with patch(path, new_callable=AsyncMock) as email_patch:
        res: Response = await async_client.post(
            "/auth/signup",
            json=sign_up_payload,
            headers={"x-api-version": "1", "env": "test"},
        )

    email_patch.assert_called_once()

    return res


@pytest_asyncio.fixture
async def verify_user(async_client: AsyncClient, create_user: Response):
    otp_path: str = "app.api.services.auth_service.auth_repo_v1.get_email_otp"
    delete_path: str = "app.api.services.auth_service.auth_repo_v1.delete_otp_token"

    otp_payload: dict = {
        "email": "user@example.com",
        "otp_token": "test_otp_token",
    }

    otp_patch: AsyncMock = patch(otp_path, new_callable=AsyncMock).start()
    delete_patch: AsyncMock = patch(delete_path, new_callable=AsyncMock).start()

    otp_patch.return_value = "test_otp_token"

    res: Response = await async_client.post(
        "/auth/verify",
        json=otp_payload,
        headers={"x-api-version": "1", "env": "test"},
    )

    otp_patch.start()
    delete_patch.start()

    otp_patch.assert_awaited_once()
    delete_patch.assert_awaited_once()

    return res
