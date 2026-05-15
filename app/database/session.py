from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


from app.core.config import settings

async_engine: AsyncEngine = create_async_engine(
    url=settings.ASYNC_DB_URL,
    connect_args={"server_settings": {"timezone": "utc"}},
    pool_size=15,
    max_overflow=5,
    pool_timeout=10.0,
    pool_pre_ping=True,
    prepared_statement_cache_size=0     # disable prepared statement
)

async_session = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
)
