from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ServerError,
    AppException,
    VersionError,
    InvalidOtpError,
    CredentialError,
    UserExistsError,
    UserNotFoundError,
    AuthenticationError,
    GoogleUserNotFoundError,
    create_exception_handler
)


class ExceptionHandlers:
    def __init__(self, app: FastAPI):
        self.app = app

    def register_exceptions(self):
        @self.app.exception_handler(ServerError)
        async def server_error(request: Request, exc: AppException):
            return JSONResponse(
                content={
                    "status": "error", "message": "Oops! Something went wrong!"
                },
                status_code=500,
            )



        self.app.add_exception_handler(
            exc_class_or_status_code=AuthenticationError,
            handler=create_exception_handler(
                status_code=401,
                initial_detail={
                    "status": "error",
                    "message": "User is not authenticated",
                },
            ),
        )

        self.app.add_exception_handler(
            exc_class_or_status_code=UserNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "User not found with email {user_email}",
                },
            ),
        )

        self.app.add_exception_handler(
            exc_class_or_status_code=GoogleUserNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "User not found with id {user_id}",
                },
            ),
        )

        self.app.add_exception_handler(
            exc_class_or_status_code=UserExistsError,
            handler=create_exception_handler(
                status_code=409,
                initial_detail={
                    "status": "error",
                    "message": "User already exists with the provided email {user_email}",
                },
            ),
        )

        self.app.add_exception_handler(
            VersionError,
            create_exception_handler(
                initial_detail={
                    "status": "error",
                    "message": "API version header required",
                },
                status_code=400,
            ),
        )

        self.app.add_exception_handler(
            CredentialError,
            create_exception_handler(
                initial_detail={
                    "status": "error",
                    "message": "Invalid credentials!",
                },
                status_code=400,
            ),
        )

        self.app.add_exception_handler(
            InvalidOtpError,
            create_exception_handler(
                initial_detail={
                    "status": "error",
                    "message": "Invalid otp!",
                },
                status_code=400,
            ),
        )
