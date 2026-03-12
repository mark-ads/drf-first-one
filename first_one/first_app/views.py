import logging
from datetime import datetime

from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from first_one.first_app.filters import (
    EventFilter,
    EventNotificationFilter,
)
from first_one.first_app.models import Event, EventImage, EventNotification, EventPlace
from first_one.first_app.permissions import EventImagePermission, EventPermission
from first_one.first_app.serializers import (
    EventImageSerializer,
    EventImportSerializer,
    EventNotificationSerializer,
    EventPlaceSerializer,
    EventSerializer,
)
from first_one.first_app.services.event_export import EventExportService
from first_one.first_app.services.event_import import EventImportService

logger = logging.getLogger("first_app")


@extend_schema_view(
    list=extend_schema(
        summary="Список мест для мероприятий",
        description="Возвращает список всех мест для проведения мероприятий.",
    ),
    retrieve=extend_schema(
        summary="Получить место мероприятия",
        description="Возвращает данные конкретного места для мероприятия.",
    ),
    create=extend_schema(
        summary="Создать место мероприятия",
        description="Создает новое место для мероприятия.",
    ),
    update=extend_schema(
        summary="Обновить место мероприятия",
        description="Обновляет данные места для мероприятия.",
    ),
    partial_update=extend_schema(
        summary="Частично обновить место мероприятия",
        description="Обновляет только переданные поля места мероприятия",
    ),
    destroy=extend_schema(
        summary="Удалить место мероприятия",
        description="Удаляет место для мероприятия.",
    ),
)
class EventPlaceViewSet(ModelViewSet):
    """ViewSet для управления местами для мероприятий."""

    queryset = EventPlace.objects.all()
    serializer_class = EventPlaceSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            logger.info(f"Создано новое место: {response.data.get('name')}")  # type: ignore
        else:
            logger.warning(f"Не удалось создать место: {response.data}")
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Место обновлено: {response.data.get('name')}")
        else:
            logger.warning(f'Не удалось обновить место "{response.data}"')
        return response

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Частично обновлено место: {instance.name})")
        else:
            logger.warning(f"Не удалось частично обновить место {response.data}")
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Место удалено {instance.name}")
        else:
            logger.warning(f"Не удалось удалить место {response.data}")
        return response


@extend_schema_view(
    list=extend_schema(
        summary="Список мероприятий",
        description="Возвращает список всех мероприятий. Доступны фильтры и поиск..",
    ),
    retrieve=extend_schema(
        summary="Получить мероприятие",
        description="Возвращает данные конкретного мероприятия.",
    ),
    create=extend_schema(
        summary="Создать мероприятие",
        description="Создает новое мероприятие.",
    ),
    update=extend_schema(
        summary="Обновить мероприятие",
        description="Обновляет данные мероприятия.",
    ),
    partial_update=extend_schema(
        summary="Частично обновить мероприятие",
        description="Обновляет только переданные поля мероприятия.",
    ),
    destroy=extend_schema(
        summary="Удалить мероприятие",
        description="Удаляет мероприятие.",
    ),
)
class EventViewSet(ModelViewSet):
    """ViewSet для работы с мероприятиями."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [EventPermission]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ["name", "place__name"]
    ordering_fields = ["name", "start_date", "end_date"]

    def get_queryset(self):  # type: ignore
        qs = Event.objects.select_related("author", "place").prefetch_related("images")
        if not self.request.user.is_superuser:  # type: ignore
            qs = qs.filter(
                status__in=[
                    Event.StatusChoices.PUBLISHED,
                    Event.StatusChoices.STARTED,
                ]
            )
        return qs

    @extend_schema(
        summary="Экспорт мероприятий",
        description="""Скачать .xlsx файл с мероприятиями.
        Доступны фильтры из параметров запроса /events/?.""",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(
        detail=False,
        methods=["GET"],
        url_path="export",
        permission_classes=[IsAdminUser],
    )
    def export(self, _):
        queryset = self.filter_queryset(self.get_queryset())
        service = EventExportService(queryset)
        new_xlsx = service.run()

        current_time = datetime.now().strftime("%Y_%m_%dT%H_%M")
        file_name = f"events_export_{current_time}.xlsx"
        return FileResponse(new_xlsx, as_attachment=True, filename=file_name)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            logger.info(f"Создано новое мероприятие: {response.data.get('name')}")  # type: ignore
        else:
            logger.warning(f"Не удалось создать мероприятие: {response.data}")
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Мероприятие обновлено: {response.data.get('name')}")
        else:
            logger.warning(f'Не удалось обновить мероприятие "{response.data}"')
        return response

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Частично обновлено мероприятие: {instance.name})")
        else:
            logger.warning(f"Не удалось частично обновить мероприятие {response.data}")
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Мероприятие удалено {instance.name}")
        else:
            logger.warning(f"Не удалось удалить мероприятие {response.data}")
        return response


@extend_schema_view(
    list=extend_schema(
        summary="Список изображений для мероприятий",
        description="Возвращает список всех изображений.",
    ),
    retrieve=extend_schema(
        summary="Получить конкретное изображение для мероприятия",
        description="Возвращает данные конкретного уведомления для мероприятия.",
    ),
    create=extend_schema(
        summary="Загрузить изображение для мероприятия",
        description="Загружает новое изображение для мероприятия.",
    ),
    destroy=extend_schema(
        summary="Удалить изображение мероприятия",
        description="Удаляет изображение для мероприятия.",
    ),
)
class EventImageViewSet(ModelViewSet):
    """ViewSet для работы с изображениями для мероприятий."""

    queryset = EventImage.objects.all()
    serializer_class = EventImageSerializer
    permission_classes = [EventImagePermission]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):  # type: ignore
        qs = EventImage.objects.select_related("event")
        if not self.request.user.is_superuser:  # type: ignore
            qs = qs.filter(
                event__status__in=[
                    Event.StatusChoices.PUBLISHED,
                    Event.StatusChoices.STARTED,
                ]
            )
        return qs

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            logger.info(f"Добавлено новое изображение: {response.data.get('image')}")  # type: ignore
        else:
            logger.warning(f"Не удалось добавить изображение: {response.data}")
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Изображение удалено {instance}")
        else:
            logger.warning(f"Не удалось удалить изображение {response.data}")
        return response


@extend_schema_view(
    list=extend_schema(
        summary="Список настроек уведомлений для мероприятий",
        description="Возвращает список всех уведомлений.",
    ),
    retrieve=extend_schema(
        summary="Получить уведомление для мероприятия",
        description="Возвращает данные конкретного уведомления для мероприятия.",
    ),
    create=extend_schema(
        summary="Создать уведомление для мероприятия",
        description="Создает новое уведомление для мероприятия.",
    ),
    update=extend_schema(
        summary="Обновить уведомление для мероприятия",
        description="Обновляет данные уведомления для мероприятия.",
    ),
    partial_update=extend_schema(
        summary="Частично обновить уведомление для мероприятия",
        description="Обновляет только переданные поля уведомления для мероприятия",
    ),
    destroy=extend_schema(
        summary="Удалить уведомление мероприятия",
        description="Удаляет уведомление для мероприятия.",
    ),
)
class EventNotificationViewSet(ModelViewSet):
    """ViewSet для работы с уведомлениями о мероприятиях."""

    queryset = EventNotification.objects.all()
    serializer_class = EventNotificationSerializer
    permission_classes = [IsAdminUser]

    filterset_class = EventNotificationFilter

    def get_queryset(self):  # type: ignore
        qs = EventNotification.objects.select_related("event")
        qs = qs.filter(event__status=Event.StatusChoices.DRAFT)

        return qs

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            logger.info(f"Добавлено новое уведомление: {response.data.get('event')}")  # type: ignore
        else:
            logger.warning(f"Не удалось добавить уведомление: {response.data}")
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Уведомление обновлено: {response.data.get('event')}")
        else:
            logger.warning(f'Не удалось обновить уведомление "{response.data}"')
        return response

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Частично обновлено уведомление: {instance.event})")
        else:
            logger.warning(f"Не удалось частично обновить уведомление {response.data}")
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        if response.status_code in (200, 204):
            logger.info(f"Изображение удалено {instance.event}")
        else:
            logger.warning(f"Не удалось удалить изображение {response.data}")
        return response


@extend_schema(
    summary="Импортировать меропритятия",
    description="Принимает .xlsx файл с мероприятиями.",
)
class ImportEventAPIView(generics.CreateAPIView):
    """Эндпоинт для загрузки пользовательского .xlsx файла с мероприятиями."""

    # Делаю отдельную вьюшку, чтобы нормально отрендерилось поле с выбором файла
    serializer_class = EventImportSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        file = serializer.validated_data["file"]
        service = EventImportService(file, self.request)
        self.result = service.run()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # Ниже линтер ругается, что код недоступен, в случае исключения
        # Так и не смог победить линтер
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(getattr(self, "result", {}), status=status.HTTP_200_OK)
