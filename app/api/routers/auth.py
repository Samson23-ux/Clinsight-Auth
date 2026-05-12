from typing import Annotated
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, Header, Request, Response


from app.limiter import limiter
from app.core.security import oauth
from app.core.config import settings
from app.api.models.users import User
from app.core.exceptions import VersionError
from app.api.services.auth_service import auth_service_v1
from app.api.schemas.users import UserOutV1, UserCreateV1, UserResponseV1
from app.dependencies import get_session, get_redis_db, get_current_active_user
from app.api.schemas.auth import (
    TokenV1,
    ResendOtpV1,
    EmailLoginV1,
    EmailVerifyV1,
    VerifyResponseV1,
    SignUpResponseV1,
    LogoutResponseV1,
    OtpResendResponseV1,
)


auth_router_v1 = APIRouter()


@auth_router_v1.post(
    "/auth/signup",
    status_code=201,
    description="Sign up with email and password",
    response_model=SignUpResponseV1,
)
@limiter.limit("3/5minutes")
async def sign_up_with_email(
    request: Request,
    user_create: UserCreateV1,
    x_api_version: Annotated[str, Header()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not x_api_version:
        raise VersionError()

    user_email: str = await auth_service_v1.sign_up_with_email(user_create, session)
    return SignUpResponseV1(
        message="Sign up completed. Check email for verification code.",
        email=user_email,
    )


@auth_router_v1.get(
    "/auth/google",
    status_code=302,
    description="Sign up with google",
)
@limiter.limit("3/5minutes")
async def sign_up_with_google(
    request: Request,
    x_api_version: Annotated[str, Header()],
):
    if not x_api_version:
        raise VersionError()

    redirect_uri = request.url_for("/api/auth/google/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_router_v1.post(
    "/auth/google/callback",
    status_code=201,
    description="Google callback",
    response_model=TokenV1,
)
@limiter.limit("3/5minutes")
async def google_callback(
    request: Request,
    response: Response,
    x_api_version: Annotated[str, Header()],
    redis_db: Annotated[Redis, Depends(get_redis_db)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not x_api_version:
        raise VersionError()

    token = await oauth.google.authorize_access_token(request)

    access_token, refresh_token = await auth_service_v1.create_google_user(
        token, redis_db, session
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24,
    )

    return TokenV1(access_token=access_token)


@auth_router_v1.post(
    "/auth/verify",
    status_code=201,
    description="Verify email address",
    response_model=VerifyResponseV1,
)
@limiter.limit("3/5minutes")
async def verify_email(
    request: Request,
    email_verify: EmailVerifyV1,
    x_api_version: Annotated[str, Header()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not x_api_version:
        raise VersionError()

    await auth_service_v1.verify_email(email_verify, session)
    return VerifyResponseV1(
        message="Email verified successfully. Login to access account"
    )


@auth_router_v1.post(
    "/auth/login",
    status_code=201,
    description="Verify email address",
    response_model=TokenV1,
)
@limiter.limit("3/5minutes")
async def login(
    request: Request,
    response: Response,
    login_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    x_api_version: Annotated[str, Header()],
    redis_db: Annotated[Redis, Depends(get_redis_db)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not x_api_version:
        raise VersionError()

    email_login: EmailLoginV1 = EmailLoginV1(
        email=login_form.username, password=login_form.password
    )

    access_token, refresh_token = await auth_service_v1.login(
        email_login, redis_db, session
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24,
    )

    return TokenV1(access_token=access_token)


@auth_router_v1.post(
    "/auth/verify/resend",
    status_code=201,
    description="Resend verification code",
    response_model=OtpResendResponseV1,
)
@limiter.limit("3/5minutes")
async def resend_otp(
    request: Request,
    otp_resend: ResendOtpV1,
    x_api_version: Annotated[str, Header()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not x_api_version:
        raise VersionError()

    await auth_service_v1.resend_otp(otp_resend, session)
    return OtpResendResponseV1(
        message="Verification code sent to email successfully."
    )


@auth_router_v1.post(
    "/auth/refresh",
    status_code=201,
    response_model=TokenV1,
    description="Create new access token for user with a valid refresh token",
)
@limiter.limit("3/5minutes")
async def create_new_token(
    request: Request,
    response: Response,
    x_api_version: Annotated[str, Header()],
    redis_db: Annotated[Redis, Depends(get_redis_db)],
):
    if not x_api_version:
        raise VersionError()

    refresh_token: str = request.cookies.get("refresh_token")
    access_token, refresh_token = await auth_service_v1.create_new_token(
        refresh_token, redis_db
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24,
    )

    return TokenV1(access_token=access_token)


@auth_router_v1.get(
    "/auth/me",
    status_code=200,
    description="Get current active user",
    response_model=UserResponseV1,
)
@limiter.limit("3/5minutes")
async def get_current_user(
    request: Request,
    x_api_version: Annotated[str, Header()],
    curr_user: Annotated[User, Depends(get_current_active_user)],
):
    if not x_api_version:
        raise VersionError()

    user: UserOutV1 = await auth_service_v1.get_curr_user(curr_user)
    return UserResponseV1(data=user)


@auth_router_v1.post(
    "/auth/logout",
    status_code=201,
    description="Logout account",
    response_model=LogoutResponseV1,
)
@limiter.limit("3/5minutes")
async def logout(
    request: Request,
    x_api_version: Annotated[str, Header()],
    session: Annotated[AsyncSession, Depends(get_session)],
    curr_user: Annotated[User, Depends(get_current_active_user)],
):
    if not x_api_version:
        raise VersionError()

    await auth_service_v1.logout(curr_user, session)
    return LogoutResponseV1(message="Log out successful")
