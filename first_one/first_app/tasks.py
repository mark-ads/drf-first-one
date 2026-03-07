from celery import shared_task
import requests

from first_one.first_app.models import Event, WeatherForecast

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

        print(f'Старт получения прогноза для {event.name}')
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
