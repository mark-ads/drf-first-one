from datetime import datetime

import requests
from celery import shared_task

from first_one.first_app.models import Event, EventNotification, WeatherForecast

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_MAPPINGS = {
    "temperature": "temperature_2m",
    "humidity": "relativehumidity_2m",
    "pressure": "pressure_msl",
    "wind_direction": "winddirection_10m",
    "wind_speed": "windspeed_10m",
}


@shared_task
def update_weather_task():
    """Получить прогнозы погоды для каждого опубликованного мероприятия.

    Данные о погоде сохраняются в модель WeatherForecast.
    """

    events = Event.objects.filter(status=Event.StatusChoices.PUBLISHED).select_related(
        "place"
    )

    for event in events:
        params = {
            "latitude": event.place.latitude,
            "longitude": event.place.longitude,
            "hourly": "temperature_2m,relativehumidity_2m,pressure_msl,windspeed_10m,winddirection_10m,precipitation",
            "start_date": event.start_date.strftime("%Y-%m-%d"),
            "end_date": event.start_date.strftime("%Y-%m-%d"),
            "timezone": "Asia/Bangkok",
        }

        print(f"Старт получения прогноза для {event.name}")
        response = requests.get(WEATHER_URL, params=params, timeout=10)

        response.raise_for_status()

        event.weather.all().delete()  # type: ignore

        forecasts = response.json().get("hourly", {})

        hour = event.start_date.hour  # час начала мероприятия

        result = {}

        # Результат возвращается в виде словаря со списками: dict[str, list]

        # Безопасное присвоение значений, если АПИ вернет пустые или неполные списки
        for result_field, original_field in WEATHER_MAPPINGS.items():
            temp = forecasts.get(original_field, [])

            # Используем час как индекс в списке, чтобы получить нужный показатель
            try:
                result[result_field] = temp[hour]
            except IndexError:
                result[result_field] = None

        if result["pressure"] is not None:
            pressure = result["pressure"] * 0.75006  # конвертация hPa в мм.рт.ст
            result["pressure"] = round(pressure, 2)

        WeatherForecast.objects.create(
            event=event,
            temperature=result["temperature"],
            humidity=result["humidity"],
            pressure=result["pressure"],
            wind_direction=result["wind_direction"],
            wind_speed=result["wind_speed"],
        )


update_weather_task.delay()  # type: ignore


@shared_task
def send_email_notification(notification_id: int):
    """Отправить уведомления на имейл всем получателям."""

    notification = EventNotification.objects.get(id=notification_id)
    email_list = notification.recipients
    subject = notification.email_subject
    text = notification.email_text

    for email in email_list:
        print(f"Отправлен email по адресу {email}, тема {subject}, текст {text}")


@shared_task
def check_event_status():
    events = Event.objects.filter(status=Event.StatusChoices.DRAFT)

    for event in events:
        if event.publish_date <= datetime.now():
            print(f'Поменялся статус ивента {event.name}')
            event.status = Event.StatusChoices.PUBLISHED
            event.save(update_fields=["status"])

            if EventNotification.objects.filter(event=event).exists():
                print('Отдаем задачу на отправку уведомления')
                notification = EventNotification.objects.get(event=event)
                send_email_notification.delay(notification.id)  # type: ignore
