from datetime import datetime, timedelta
from pathlib import Path

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from first_one.first_app.models import Event, EventNotification, WeatherForecast
from first_one.first_app.utils import create_preview

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

    # Ограничение на прогноз погоды, нельзя запрашивать дальше чем на 10 дней
    current_time = datetime.now()
    max_date = current_time + timedelta(days=10)

    # Фильтруем так же в диапазоне максимальной даты для прогноза
    events = Event.objects.filter(
        status=Event.StatusChoices.PUBLISHED,
        start_date__gte=current_time,
        start_date__lte=max_date,
    ).select_related("place")

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


@shared_task
def send_email_notification(notification_id: int):
    """Отправить уведомления на имейл всем получателям."""

    notification = EventNotification.objects.get(id=notification_id)
    email_list = notification.recipients
    subject = notification.email_subject or "Нет темы"
    text = notification.email_text or ""

    send_mail(
        subject=subject,
        message=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=email_list,
        fail_silently=True,
    )
    print("Письма отправлены")


@shared_task
def check_event_status():
    events = Event.objects.filter(status=Event.StatusChoices.DRAFT)

    for event in events:
        if event.publish_date <= datetime.now():
            print(f"Поменялся статус ивента {event.name}")
            event.status = Event.StatusChoices.PUBLISHED
            event.save(update_fields=["status"])

            if EventNotification.objects.filter(event=event).exists():
                print("Отдаем задачу на отправку уведомления")
                notification = EventNotification.objects.get(event=event)
                send_email_notification.delay(notification.id)  # type: ignore


@shared_task
def check_preview_availability():
    """Проверить, наличие, необходимость обновить или удалить первью.

    При необходимости создаёт и сохраняет новое превью.

    1) Проверяет наличие изображений для мероприятия и наличие превью;
    2) Проверяет необходимость удаления превью, если изображения удалены;
    3) Проверяет совпадение имен первого изображения и превью;
    4) Создает новое превью.
    """
    events = Event.objects.filter(
        status__in=[Event.StatusChoices.DRAFT, Event.StatusChoices.PUBLISHED]
    ).prefetch_related("images")

    for event in events:
        image_list = list(event.images.all())  # type: ignore

        # Задаем первую картинку или None.
        first_image = image_list[0].image if image_list else None

        if not first_image and not event.preview:
            print(f"Отсутствует превью для {event.name}")
            continue

        if not first_image and event.preview:
            event.preview.delete()
            print(f"Удаляем превью для {event.name}")
            continue

        if first_image and event.preview:
            expected_name = f"prev_{Path(first_image.name).name}"

            if expected_name == Path(event.preview.name).name:
                # Название изображения соответствует названию превью.
                print(f"Превью соответствует для {event.name}")
                continue

            print(f"Удаление превью. Не соответствует для {event.name}")
            event.preview.delete()

        # Либо превью нет, либо оно не соовпадает по названию.
        if first_image:
            new_image = create_preview(first_image.path)
            new_name = f"prev_{Path(first_image.name).name}"
            event.preview.save(new_name, new_image, save=True)
            print(f"Создано превью {new_name}, для {event.name}")
