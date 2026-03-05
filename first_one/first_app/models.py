from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from PIL import Image

User = get_user_model()


class EventPlace(models.Model):
    name = models.CharField(max_length=100)
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
        DRAFT = "Черновик"
        PUBLISHED = "Опубликовано"
        STARTED = "В процессе"
        ENDED = "Закончилось"
        CANCELLED = "Отменено"

    name = models.CharField(max_length=100)
    preview = models.ImageField(
        blank=True, null=True, upload_to="first_one/first_app/images/event_preview/"
    )
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

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Дата завершения должна быть не раньше даты начала.")

    def save(self, *args, **kwargs):
        """Сохранить модель с автоматическим уменьшением превью до 200px."""
        self.full_clean()
        super().save(*args, **kwargs)

        if self.preview:
            image = Image.open(self.preview.path)
            sizes = image.size
            if min(sizes) > 200:
                if sizes[0] <= sizes[1]:
                    image.thumbnail((200, sizes[1]))
                else:
                    image.thumbnail((sizes[0], 200))
                image.save(self.preview.path)

    class Meta:
        verbose_name = "Мероприятия"
        verbose_name_plural = "Мероприятия"
        ordering = ["publish_date"]


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="first_one/first_app/images/event_pics/")

    def __str__(self):
        return f"{self.event.name} - {getattr(self, 'id', 'unsaved')}"

    class Meta:
        verbose_name = "Изображение мероприятия"
        verbose_name_plural = "Изображения мероприятия"
