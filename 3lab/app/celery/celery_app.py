from celery import Celery
from app.core.config import settings
import redislite
import os

rconn = None
if "redis://" in settings.CELERY_BROKER_URL:
    try:
        rdb_path = settings.REDISLITE_RDB_FILE
        rdb_dir = os.path.dirname(rdb_path)
        if rdb_dir and not os.path.exists(rdb_dir):
            os.makedirs(rdb_dir)
        
        parsed_port = 6379
        if ":" in settings.CELERY_BROKER_URL.split("//")[-1]:
            try:
                parsed_port = int(settings.CELERY_BROKER_URL.split(":")[-1].split("/")[0])
            except ValueError:
                pass

        rconn = redislite.Redis(dbfilename=rdb_path, serverconfig={'port': str(parsed_port)})
        print(f"Redislite server started/connected using {rdb_path} on port {parsed_port}")

    except Exception as e:
        print(f"Failed to start redislite server: {e}")
        print("Please ensure redislite is installed correctly (pip install redislite)")

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.celery.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Moscow',
    enable_utc=True,
)

if __name__ == '__main__':
    celery_app.start() 