from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management import BaseCommand

from first_one.first_app.models import Event, EventImage, EventPlace


class Command(BaseCommand):
    help = "Наполнить БД тестовыми примерами."

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password="admin"
            )

        if not User.objects.filter(is_superuser=False).exists():
            User.objects.create_user(
                username="user", email="user@example.com", password="user"
            )

        admin = User.objects.get(username="admin")

        places_names = ["РАНЧО Шарье", "Кубеково", "Сибирский Сафари клуб"]

        places_coordinates = [
            (56.180829, 92.948928),
            (56.149666, 93.067114),
            (55.989475, 92.845228),
        ]

        for i in range(3):
            place, _ = EventPlace.objects.get_or_create(
                name=places_names[i],
                latitude=places_coordinates[i][0],
                longitude=places_coordinates[i][1],
            )

        event_names = [
            "Зимний корпоратив",
            "8 Марта",
            "Тимбилдинг",
            "Весенний корпоратив",
        ]

        event_dates = [
            datetime.fromisoformat("2026-01-27T18:00:00"),
            datetime.fromisoformat("2026-03-08T18:00:00"),
            datetime.now() + timedelta(days=7),
            datetime.now() + timedelta(days=30),
        ]

        now = datetime.now()

        for i in range(4):
            # Делаю проверку, а не get_or_create(), так как из-за datetime.now()
            # ивент Тимбилдинг будет дублироваться при повторном использовании populate
            if Event.objects.filter(name=event_names[i]).exists():
                for event in Event.objects.filter(name=event_names[i]):
                    # Вложенный цикл удаления изображений мероприятия
                    for image in event.images.all():  # type: ignore
                        image.delete()

                    event.delete()

            place_idx = i if i == 4 else 0  # чтобы 4 ивенту назначилось [0] место проведения
            place = EventPlace.objects.get(name=places_names[place_idx])

            if now < event_dates[i] - timedelta(days=10):
                status = Event.StatusChoices.DRAFT
            elif now < event_dates[i]:
                status = Event.StatusChoices.PUBLISHED
            elif now > event_dates[i] + timedelta(hours=3):
                status = Event.StatusChoices.ENDED
            else:
                status = Event.StatusChoices.STARTED

            event = Event.objects.create(
                name=event_names[i],
                description=f'Описание мероприятия "{event_names[i]}".',
                publish_date=event_dates[i] - timedelta(days=10),
                start_date=event_dates[i],
                end_date=event_dates[i] + timedelta(hours=3),
                author=admin,
                place=place,
                rating=20 + i,
                status=status,
            )

            for j in range(2):
                if i > 2:  # 4 ивент остаётся без картинок 
                    break

                file_name = f"{i}_{j}.jpg"
                img_path = Path(settings.BASE_DIR) / "sample_data" / file_name

                if not EventImage.objects.filter(
                    event=event,
                    image=f"media/event_pics/{file_name}",
                ).exists():
                    with open(img_path, "rb") as f:
                        EventImage.objects.create(
                            event=event, image=File(f, name=f"{i}_{j}.jpg")
                        )
