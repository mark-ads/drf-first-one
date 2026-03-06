from datetime import datetime

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from first_one.first_app.models import Event, EventImage, EventPlace


class EventPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPlace
        fields = ["id", "name", "latitude", "longitude"]


class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ["id", "event", "image"]

    def validate_image(self, image):
        max_size = 10 * 1024 * 1024

        if image.size > max_size:
            raise ValidationError("Размер изображения не должен превышать 10 мб.")

        if not image.name.endswith((".jpg", ".jpeg", ".png")):
            raise ValidationError("Изображение должно быть формата jpeg или png.")

        return image


class EventSerializer(serializers.ModelSerializer):
    # Превью создается автоматически в моделях
    preview = serializers.ImageField(read_only=True)

    images = EventImageSerializer(many=True, read_only=True)

    # Игнорируем поле author в АПИ, вместо этого отдаём author_info
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    author_info = serializers.SerializerMethodField()

    place = serializers.PrimaryKeyRelatedField(
        queryset=EventPlace.objects.all(), write_only=True
    )

    place_info = EventPlaceSerializer(source="place", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "preview",
            "images",
            "description",
            "publish_date",
            "start_date",
            "end_date",
            "author",
            "author_info",
            "place",
            "place_info",
            "rating",
            "status",
        ]

    def get_author_info(self, object):
        return {
            "id": object.author.id,
            "username": object.author.username,
        }

    def validate(self, attrs):
        publish_date = attrs.get("publish_date")
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if publish_date and start_date:
            if publish_date > start_date:
                raise ValidationError(
                    "Дата публикации не может быть позднее даты начала."
                )

            if start_date < datetime.now():
                raise ValidationError("Дата начала не может быть в прошлом.")

        if publish_date and end_date:
            if publish_date > end_date:
                raise ValidationError(
                    "Дата публикации не может быть позднее даты завершения."
                )

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(
                    "Дата начала не может быть позднее даты завершения."
                )

        return attrs
