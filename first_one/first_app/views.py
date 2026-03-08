from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from first_one.first_app.filters import EventFilter, EventNotificationFilter
from first_one.first_app.models import Event, EventImage, EventNotification, EventPlace
from first_one.first_app.permissions import EventImagePermission, EventPermission
from first_one.first_app.serializers import (
    EventImageSerializer,
    EventImportSerializer,
    EventNotificationSerializer,
    EventPlaceSerializer,
    EventSerializer,
)
from first_one.first_app.services.event_import import EventImportService


class EventPlaceViewSet(ModelViewSet):
    queryset = EventPlace.objects.all()
    serializer_class = EventPlaceSerializer
    permission_classes = [IsAdminUser]


class EventViewSet(ModelViewSet):
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


class EventImageViewSet(ModelViewSet):
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


class EventNotificationViewSet(ModelViewSet):
    queryset = EventNotification.objects.all()
    serializer_class = EventNotificationSerializer
    permission_classes = [IsAdminUser]

    filterset_class = EventNotificationFilter

    def get_queryset(self):  # type: ignore
        qs = EventNotification.objects.select_related("event")
        qs = qs.filter(event__status=Event.StatusChoices.DRAFT)

        return qs


class ImportEvent(generics.CreateAPIView):
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
