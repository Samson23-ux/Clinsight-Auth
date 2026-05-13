from celery import Celery


from app.core.config import settings


celery_app = Celery(
    main="celery_app", broker=settings.API_BROKER
)

celery_app.autodiscover_tasks(["app.tasks.celery_task"])

celery_app.config_from_object("app.tasks.celeryconfig")
