import os
from datetime import timedelta

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "first_one.settings")
print(settings.TASKS_WEATHER_UPDATE_DELAY_MIN)
app = Celery(main="tasks")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "weather_forecast": {
        "task": "first_one.first_app.tasks.update_weather_task",
        "schedule": timedelta(minutes=settings.TASKS_WEATHER_UPDATE_DELAY_MIN),
    },
    "status_check": {
        "task": "first_one.first_app.tasks.check_event_status",
        "schedule": timedelta(minutes=1),
    },
}
