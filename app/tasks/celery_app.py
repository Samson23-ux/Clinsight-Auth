from celery import Celery


from app.core.config import settings


celery_app = Celery(
    main="celery_app", broker=settings.API_BROKER, include=["app.tasks.celery_app"]
)


celery_app.config_from_object("app.tasks.celeryconfig")
