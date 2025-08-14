from kombu import Queue  # type: ignore[import-untyped]

from app.conf.environ import env
from app.conf.timezone import TIME_ZONE


CELERY_BROKER_URL = env("CELERY_BROKER_URL", cast=str, default="redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER", cast=bool, default=env("DEBUG"))
CELERY_TASK_DEFAULT_QUEUE = env("CELERY_TASK_DEFAULT_QUEUE", cast=str, default="celery")

CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

CELERY_TASK_DEFAULT_MAX_RETRIES = 5
CELERY_TASK_DEFAULT_RETRY_DELAY = 10

CELERY_TASK_QUEUES = (Queue(CELERY_TASK_DEFAULT_QUEUE, routing_key=CELERY_TASK_DEFAULT_QUEUE),)
