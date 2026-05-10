from uuid import uuid4
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta


from app.core.config import settings
from app.api.schemas.auth import TokenDataV1, RefreshToken


async def create_access_token(
    token_data: TokenDataV1, expire_time: Optional[int] = None
) -> str:
    if not expire_time:
        expire_time: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_TIME
        )
    else:
        expire_time: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=expire_time
        )

    payload: dict = {
        "sub": token_data.email,
        "exp": expire_time,
        "iat": datetime.now(timezone.utc),
    }

    token: str = jwt.encode(
        claims=payload,
        key=settings.ACCESS_TOKEN_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


async def create_refresh_token(
    token_data: TokenDataV1, expire_time: Optional[datetime] = None
) -> tuple:
    if not expire_time:
        expire_time: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_TIME
        )
    else:
        expire_time: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=expire_time
        )

    payload: dict = {
        "sub": token_data.email,
        "exp": expire_time,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),
    }

    token: str = jwt.encode(
        claims=payload,
        key=settings.REFRESH_TOKEN_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, payload["jti"], expire_time


async def prepare_tokens(user_email: str, token_data: TokenDataV1) -> dict:
    access_token: str = await create_access_token(token_data)

    refresh_token, token_id, token_exp = await create_refresh_token(token_data)

    refresh_token_db: RefreshToken = RefreshToken(
        id=token_id,
        token=await refresh_token,
        user_email=user_email,
        expires_at=token_exp,
    )

    data: dict = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_token_db": refresh_token_db,
    }

    return data


async def decode_token(token: str, key: str):
    try:
        payload: dict = jwt.decode(
            token=token, key=key, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
