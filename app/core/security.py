from uuid import uuid4
from typing import Optional
from jose import jwt, JWTError
from pwdlib.hashers.argon2 import Argon2Hasher
from datetime import datetime, timezone, timedelta
from authlib.integrations.starlette_client import OAuth


from app.core.config import settings
from app.api.schemas.auth import TokenDataV1


arg2_hasher = Argon2Hasher()


# oauth2
oauth: OAuth = OAuth()

oauth.register(
    name="google",
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
)


async def hash_password(password: str) -> str:
    password: str = password + settings.ARGON2_PASSWORD_PEPPER
    return arg2_hasher.hash(password)


async def verify_password(password: str, hash_password: str) -> bool:
    password: str = password + settings.ARGON2_PASSWORD_PEPPER
    return arg2_hasher.verify(password, hash_password)


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
    token_data: TokenDataV1, expire_time: Optional[int] = None
) -> tuple:
    if not expire_time:
        expire_time: datetime = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_TIME
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


async def prepare_tokens(token_data: TokenDataV1) -> dict:
    access_token: str = await create_access_token(
        token_data
    )

    refresh_token, refresh_token_id, refresh_token_exp = await create_refresh_token(
        token_data
    )

    access_token_data: dict = {
        "access_token": access_token,
    }

    refresh_token_data: dict = {
        "refresh_token": refresh_token,
        "refresh_token_id": refresh_token_id,
        "refresh_token_exp": refresh_token_exp.isoformat(),
    }

    data: dict = {
        "access_token_data": access_token_data,
        "refresh_token_data": refresh_token_data,
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
