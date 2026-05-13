from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.sessions import SessionMiddleware


from app.limiter import limiter
from app.core.config import settings
from app.api.routers.auth import auth_router_v1
from app.core.exception_handlers import ExceptionHandlers


app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)


app.include_router(auth_router_v1, prefix=settings.API_PREFIX, tags=["Auth"])


app.add_middleware(
    SessionMiddleware,
    max_age=900,
    same_site="lax",
    secret_key=settings.SESSION_SECRET_KEY,
    https_only=settings.ENVIRONMENT == "production",
)


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


exception_handers = ExceptionHandlers(app)

exception_handers.register_exceptions()


@app.get("/", status_code=200)
async def home():
    message: dict = {
        "status": "success",
        "message": "Welcome Clinsights",
    }
    return message
