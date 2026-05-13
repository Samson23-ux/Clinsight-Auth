import json
from uuid import uuid4, UUID
from redis.asyncio import Redis
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import settings
from app.api.models.auth import AuthOtp
from app.tasks.celery_task import send_email
from app.api.repo.auth_repo import auth_repo_v1
from app.api.models.users import User, GoogleUser
from app.api.services.user_service import user_service_v1
from app.api.schemas.users import UserCreateV1, UserOutV1
from app.api.schemas.auth import EmailLoginV1, TokenDataV1, EmailVerifyV1, ResendOtpV1
from app.core.security import (
    decode_token,
    hash_password,
    prepare_tokens,
    verify_password,
)
from app.core.exceptions import (
    ServerError,
    UserExistsError,
    CredentialError,
    InvalidOtpError,
    UserNotFoundError,
    AuthenticationError,
)


class AuthServiceV1:
    async def _get_tokens(self, user_email: str, redis_db: Redis) -> tuple:
        exp_time: int = 24 * 60 * 60
        token_data: TokenDataV1 = TokenDataV1(email=user_email)

        data: dict = await prepare_tokens(token_data)

        access_token_data: dict = data["access_token_data"]
        refresh_token_data: dict = data["refresh_token_data"]

        refresh_token_data["email"] = user_email

        access_token: str = access_token_data["access_token"]
        refresh_token: str = refresh_token_data["refresh_token"]

        refresh_token_id: str = refresh_token_data["refresh_token_id"]

        await auth_repo_v1.store_token(
            refresh_token_id,
            json.dumps(refresh_token_data),
            exp_time,
            redis_db,
        )

        return access_token, refresh_token

    def _get_verification_code(self, email_id: str, redis_db: Redis) -> dict:
        code: str | None = auth_repo_v1.get_verification_code(email_id, redis_db)

        if code:
            return json.loads(code)
        return None

    def _create_email_code(
        self, email_id: str, payload: dict, exp: int, redis_db: Redis
    ):
        auth_repo_v1.store_email_code(email_id, json.dumps(payload), exp, redis_db)

    def _create_auth_otp(self, otp: AuthOtp, session: Session):
        try:
            auth_repo_v1.add_otp_to_db(otp, session)
            session.commit()
        except Exception as e:
            session.rollback()
            raise ServerError() from e

    async def sign_up_with_email(
        self, user_create: UserCreateV1, session: AsyncSession
    ) -> str:
        """
        Create a new user and send otp to email.
        If user exists and is not verified the password is re-assigned and a new otp sent.
        Else a user exists error is raise
        """
        user_email: str = user_create.email
        existing_user: User | None = await user_service_v1._get_user(
            user_email, session
        )
        if existing_user:
            if not existing_user.is_verified:
                existing_user.email = user_email
                existing_user.last_name = user_create.last_name
                existing_user.first_name = user_create.first_name
                existing_user.hashed_password = await hash_password(
                    existing_user.hashed_password
                )
                user_id: UUID = existing_user.id
            else:
                raise UserExistsError(user_email)
        else:
            user_db: User = User(
                **user_create.model_dump(exclude={"password"}),
                hashed_password=await hash_password(user_create.password),
            )

            try:
                await user_service_v1.create_user(user_db, session)
                user_id: UUID = user_db.id
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise ServerError() from e

        email_id: UUID = str(uuid4())
        send_email.delay(email_id, user_email, user_id)

        return user_email

    async def create_google_user(
        self, id_token: str, redis_db: Redis, session: AsyncSession
    ) -> tuple[str]:
        user_info: dict = id_token.get("userinfo")

        user_id: str = user_info["sub"]
        user_email: str = user_info["email"]
        first_name: str = user_info["given_name"]
        last_name: str = user_info["family_name"]

        google_user: GoogleUser = await user_service_v1.get_google_user(
            user_id, session
        )

        try:
            if not google_user:
                user_db: GoogleUser = GoogleUser(
                    user_id=user_id,
                    email=user_email,
                    first_name=first_name,
                    last_name=last_name,
                )

                await user_service_v1.create_user(user_db, session)
                await session.commit()

            access_token, refresh_token = await self._get_tokens(user_email, redis_db)

            return access_token, refresh_token
        except Exception as e:
            await session.rollback()
            raise ServerError() from e

    async def login(
        self, email_login: EmailLoginV1, redis_db: Redis, session: AsyncSession
    ) -> tuple:
        """
        Return tokens if the credentails submitted are valid
        Both access token and refresh token are stored in redis with a TTL
        equal to their expiration time.
        """
        user_email: str = email_login.email
        user_password: str = email_login.password

        user: User = await user_service_v1.get_curr_user(user_email, session)

        is_password: bool = await verify_password(user_password, user.hashed_password)

        if user_email != user.email or not is_password:
            raise CredentialError()

        try:
            user.is_active = True
            await user_service_v1.update_user(user, session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise ServerError() from e

        access_token, refresh_token = await self._get_tokens(user_email, redis_db)

        return access_token, refresh_token

    async def get_curr_user(self, user: User) -> UserOutV1:
        user: UserOutV1 = UserOutV1.model_validate(user)
        return user

    async def create_new_token(self, refresh_token: str, redis_db: Redis) -> tuple[str]:
        refresh_token: dict = await decode_token(
            refresh_token, settings.REFRESH_TOKEN_SECRET_KEY
        )

        if not refresh_token:
            raise AuthenticationError()

        refresh_token_id: str = refresh_token["jti"]

        refresh_token_db: str = await auth_repo_v1.get_auth_token(
            refresh_token_id, redis_db
        )

        if not refresh_token_db:
            raise AuthenticationError()

        user_email: str = json.loads(refresh_token_db)["email"]

        try:
            await auth_repo_v1.delete_token(refresh_token_id, redis_db)
            access_token, refresh_token = await self._get_tokens(user_email, redis_db)

            return access_token, refresh_token
        except Exception as e:
            raise ServerError() from e

    async def logout(
        self,
        curr_user: User,
        session: AsyncSession,
    ):
        try:
            curr_user.is_active = False
            await user_service_v1.update_user(curr_user, session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise ServerError() from e

    async def verify_email(self, email_verify: EmailVerifyV1, session: AsyncSession):
        user: User | None = await user_service_v1._get_user(email_verify.email, session)

        if not user:
            raise InvalidOtpError()

        otp_db: AuthOtp | None = await auth_repo_v1.get_email_otp(
            email_verify.otp_token, session
        )

        if not otp_db:
            raise InvalidOtpError()

        try:
            user.is_verified = True
            await user_service_v1.update_user(user, session)
            await auth_repo_v1.delete_otp_token(otp_db, session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise ServerError() from e

    async def resend_otp(self, otp_resend: ResendOtpV1, session: AsyncSession):
        user: User = await user_service_v1._get_user(otp_resend.email, session)

        if not user:
            raise UserNotFoundError(otp_resend.email)

        # check and delete for any existing otp for user
        otp_db: AuthOtp | None = await auth_repo_v1.get_existing_otp(user.id, session)

        try:
            if otp_db:
                await auth_repo_v1.delete_otp_token(otp_db, session)

            email_id: UUID = str(uuid4())
            send_email.delay(email_id, user.email, user.id)
        except Exception as e:
            await session.rollback()
            raise ServerError() from e


auth_service_v1 = AuthServiceV1()
