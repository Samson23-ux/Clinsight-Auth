from uuid import UUID
from sqlalchemy import select
from redis.asyncio import Redis
from sqlalchemy.orm import Session
from redis import Redis as SyncRedis
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession


from app.api.models.auth import AuthOtp


class AuthRepoV1:
    async def get_auth_token(self, token_id: str, redis_db: Redis) -> str | None:
        token: str | None = await redis_db.get(token_id)
        return token

    async def get_email_otp(self, otp: str, session: AsyncSession) -> AuthOtp | None:
        today: datetime = datetime.now(timezone.utc)
        stmt = select(AuthOtp).where(AuthOtp.otp == otp, AuthOtp.expires_at >= today)

        res = await session.execute(stmt)

        otp_db: AuthOtp | None = res.scalar()
        return otp_db

    async def get_existing_otp(
        self, user_id: UUID, session: AsyncSession
    ) -> AuthOtp | None:
        today: datetime = datetime.now(timezone.utc)
        stmt = select(AuthOtp).where(
            AuthOtp.user_id == user_id, AuthOtp.expires_at >= today
        )

        res = await session.execute(stmt)

        otp_db: AuthOtp | None = res.scalar()
        return otp_db

    def get_verification_code(self, email_id: str, redis_db: SyncRedis) -> str:
        code: str | None = redis_db.get(email_id)
        return code

    def add_otp_to_db(self, otp: AuthOtp, session: Session):
        session.add(otp)
        session.flush()

    async def store_token(self, token_id: str, token: str, exp: int, redis_db: Redis):
        await redis_db.set(token_id, token, ex=exp)

    def store_email_code(self, email_id: str, code: str, exp: int, redis_db: SyncRedis):
        redis_db.set(email_id, code, ex=exp)

    async def delete_token(self, token_id: str, redis_db: Redis):
        await redis_db.delete(token_id)

    async def delete_otp_token(self, otp: AuthOtp, session: AsyncSession):
        await session.delete(otp)
        await session.flush()


auth_repo_v1 = AuthRepoV1()
