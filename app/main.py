from fastapi import FastAPI

from app.core.config import settings
from app.core.exception_handlers import ExceptionHandlers


app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)


ExceptionHandlers(app)


@app.get("/", status_code=200)
async def home():
    message: dict = {
        "status": "success",
        "message": "Welcome Clinsights",
    }
    return message
