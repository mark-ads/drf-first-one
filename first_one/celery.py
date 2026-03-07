import os
from datetime import timedelta

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "first_one.settings")

app = Celery(main="tasks")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "weather_forecast": {
        "task": "first_one.first_app.tasks.update_weather_task",
        "schedule": timedelta(minutes=5),
    },
    "status_check": {
        "task": "first_one.first_app.tasks.check_event_status",
        "schedule": timedelta(minutes=1),
    },
}
