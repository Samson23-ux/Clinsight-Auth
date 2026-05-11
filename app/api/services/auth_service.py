import json
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import settings
from app.api.models.auth import AuthOtp
from app.api.repo.auth_repo import auth_repo_v1
from app.api.models.users import User, GoogleUser
from app.api.services.user_service import user_service_v1
from app.api.schemas.users import UserCreateV1, UserOutV1
from app.api.schemas.auth import EmailLoginV1, TokenDataV1, EmailVerifyV1, ResendOtpV1
from app.core.security import (
    decode_token,
    hash_password,
    prepare_tokens,
    decode_id_token,
    verify_password,
)
from app.core.exceptions import (
    ServerError,
    UserExistsError,
    CredentialError,
    InvalidOtpError,
    AuthenticationError,
)


class AuthServiceV1:
    async def _get_tokens(self, user_email: str, redis_db: Redis) -> tuple:
        token_data: TokenDataV1 = TokenDataV1(email=user_email)

        data: dict = await prepare_tokens(user_email, token_data)

        access_token_data: dict = data["access_token_data"]
        refresh_token_data: dict = data["refresh_token_data"]

        refresh_token_data["email"] = user_email

        access_token: str = access_token_data["access_token"]
        refresh_token: str = refresh_token_data["refresh_token"]

        refresh_token_id: str = refresh_token_data["refresh_token_id"]
        refresh_token_exp: str = refresh_token_data["refresh_token_exp"]

        await auth_repo_v1.store_token(
            refresh_token_id,
            json.dumps(refresh_token_data),
            refresh_token_exp,
            redis_db,
        )

        return access_token, refresh_token

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
                existing_user.hashed_password = hash_password(existing_user.password)
            else:
                raise UserExistsError(user_email)
        else:
            user_db: User = User(
                **user_create.model_dump(exclude={"password"}),
                hashed_password=hash_password(existing_user.password),
            )

            try:
                await user_service_v1.create_user(user_db, session)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise ServerError() from e

            #### send email ###

        return user_email

    async def create_google_user(
        self, id_token: str, redis_db: Redis, session: AsyncSession
    ) -> tuple[str]:
        payload: dict | None = await decode_id_token(id_token)

        user_id: str = payload.get("sub")
        user_email: str = payload.get("email")
        first_name: str = payload.get("given_name")
        last_name: str = payload.get("family_name")

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

        access_token, refresh_token = await self._get_tokens(user_email, redis_db)

        return access_token, refresh_token

    async def get_curr_user(self, user: User) -> UserOutV1:
        user: UserOutV1 = UserOutV1.model_validate(user)
        return user

    async def create_new_token(
        self, refresh_token: str, redis_db: Redis
    ) -> tuple[str]:
        refresh_token: dict = await decode_token(refresh_token, settings.REFRESH_TOKEN_SECRET_KEY)

        if not refresh_token:
            raise AuthenticationError()

        refresh_token_id: str = refresh_token["jti"]

        refresh_token_db: str = await auth_repo_v1.get_auth_token(refresh_token_id, redis_db)

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
        user: User = await user_service_v1.get_curr_user(otp_resend.email, session)

        # check and delete for any existing otp for user
        otp_db: AuthOtp | None = await auth_repo_v1.get_existing_otp(user.id, session)

        try:
            if otp_db:
                await auth_repo_v1.delete_otp_token(otp_db, session)

            #### send email ####
        except Exception as e:
            await session.rollback()
            raise ServerError() from e


auth_service_v1 = AuthServiceV1()
