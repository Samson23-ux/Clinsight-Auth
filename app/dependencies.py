import httpx
from uuid import UUID
from typing import Annotated
from redis.asyncio import Redis
from fastapi import Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


from app.core.config import settings
from app.api.models.users import User
from app.core.security import decode_token
from app.api.services import user_service_v1
from app.database.session import async_session
from app.core.exceptions import AuthenticationError, AuthorizationError

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session():
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


async def get_redis_db():
    try:
        redis_client: Redis = Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
        )
        yield redis_client
    finally:
        await redis_client.close()


async def get_current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: AsyncSession = Depends(get_session),
):
    token = None

    if creds:
        if creds.credentials:
            token: str = creds.credentials
    else:
        token: str = request.cookies.get("access_token")

    if not token:
        raise AuthenticationError()

    key: str = settings.ACCESS_TOKEN_SECRET_KEY
    payload: dict = await decode_token(token, key)

    if not payload:
        raise AuthenticationError()

    user_id: UUID = payload.get("sub")
    user: User = await user_service_v1.get_user(user_id, session)

    return user


async def get_current_active_user(curr_user: User = Depends(get_current_user)):
    if curr_user.is_active is False:
        raise AuthorizationError()
    return curr_user
