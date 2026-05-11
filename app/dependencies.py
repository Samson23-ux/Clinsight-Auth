import httpx
from uuid import UUID
from typing import Annotated
from redis.asyncio import Redis
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer


from app.core.config import settings
from app.api.models.users import User
from app.core.security import decode_token
from app.database.session import async_session
from app.core.exceptions import AuthenticationError
from app.api.services.user_service import user_service_v1


bearer_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_session():
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


async def get_redis_db():
    try:
        redis_client: Redis = Redis(settings.REDIS_URL)
        yield redis_client
    finally:
        await redis_client.close()


async def get_current_user(
    request: Request,
    token: Annotated[OAuth2PasswordBearer, Depends(bearer_scheme)],
    redis_db: Annotated[Redis, Depends(get_redis_db)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    key: str = settings.ACCESS_TOKEN_SECRET_KEY
    payload: dict = await decode_token(token, key)

    if not payload:
        raise AuthenticationError()

    user_email: UUID = payload.get("sub")
    user: User = await user_service_v1.get_curr_user(user_email, session)

    return user


async def get_current_active_user(curr_user: User = Depends(get_current_user)):
    if curr_user.is_active is False:
        raise AuthenticationError()
    return curr_user
