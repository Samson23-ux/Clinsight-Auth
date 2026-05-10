from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ServerError,
    AppException,
    UserNotFoundError,
    AuthorizationError,
    AuthenticationError,
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
            exc_class_or_status_code=AuthorizationError,
            handler=create_exception_handler(
                status_code=403,
                initial_detail={
                    "status": "error",
                    "message": "User is not authorized to make the requested action",
                },
            ),
        )


        self.app.add_exception_handler(
            exc_class_or_status_code=UserNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "User with id not found with id {user_id}",
                },
            ),
        )
