from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from first_one.first_app.utils import create_preview

User = get_user_model()


class EventPlace(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Место проведения мероприятия"
        verbose_name_plural = "Места проведения мероприятия"


class Event(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"
        STARTED = "started", "В процессе"
        ENDED = "ended", "Закончилось"
        CANCELLED = "cancelled", "Отменено"

    name = models.CharField(max_length=100)

    preview = models.ImageField(blank=True, null=True, upload_to="event_preview/")

    description = models.TextField()
    publish_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="events")

    place = models.ForeignKey(
        EventPlace, on_delete=models.CASCADE, related_name="events"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(25)]
    )

    status = models.CharField(
        max_length=15, choices=StatusChoices.choices, default=StatusChoices.DRAFT
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Мероприятия"
        verbose_name_plural = "Мероприятия"
        ordering = ["publish_date"]


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="event_pics/")

    def __str__(self):
        return f"{self.event.name} - {getattr(self, 'id', 'unsaved')}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.event.preview:
            new_image = create_preview(self.image.path)
            new_name = f"prev_{Path(self.image.name).name}"
            self.event.preview.save(new_name, new_image, save=True)

    def delete(self, *args, **kwargs):
        """Удалить изображение из БД и диска. Обновить превью, если нужно."""

        # Проверяем на наличие превью и сходятся ли окончания названия файлов
        if self.event.preview and self.event.preview.name.endswith(
            Path(self.image.name).name
        ):
            self.event.preview.delete(save=False)

            other_image = self.event.images.exclude(pk=self.pk).first()
            if other_image:
                new_image = create_preview(other_image.image.path)
                new_name = f"prev_{Path(other_image.image.name).name}"
                self.event.preview.save(new_name, new_image, save=False)
            self.event.save()

        if self.image:
            self.image.delete(save=False)

        return super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Изображение мероприятия"
        verbose_name_plural = "Изображения мероприятия"


class WeatherForecast(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="weather")
    created_at = models.DateTimeField(auto_now_add=True)
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
        blank=True,
        null=True,
    )
    humidity = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True,
        null=True,
    )
    pressure = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(500), MaxValueValidator(1200)],
        blank=True,
        null=True,
    )
    wind_direction = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(359)],
        blank=True,
        null=True,
    )
    wind_speed = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'Прогноз погоды для "{self.event.name}".'

    class Meta:
        verbose_name = "Прогноз погоды"
        verbose_name_plural = "Прогнозы погоды"
