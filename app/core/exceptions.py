from __future__ import annotations

from uuid import UUID
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    pass


class ServerError(AppException):
    """Internal server error"""

    pass


class AuthenticationError(AppException):
    """User not authenticated"""

    pass


class UserExistsError(AppException):
    """User already exists"""
    def __init__(self, user_email: UUID):
        self.user_email = user_email

    pass


class UserNotFoundError(AppException):
    """User not found"""
    def __init__(self, user_email: UUID):
        self.user_email = user_email

    pass


def create_exception_handler(
    initial_detail: dict, status_code: int
) -> callable[[Request, AppException], JSONResponse]:
    async def handler(request: Request, exc: AppException):
        message: str = initial_detail.get("message")
        initial_detail["message"] = message.format(**exc.__dict__)
        return JSONResponse(content=initial_detail, status_code=status_code)

    return handler
