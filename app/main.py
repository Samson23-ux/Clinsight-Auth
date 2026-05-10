from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)


@app.get("/", status_code=200)
async def home():
    message: dict = {
        "status": "success",
        "message": "Welcome Clinsights",
    }
    return message
