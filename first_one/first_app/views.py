from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from first_one.first_app.filters import EventFilter
from first_one.first_app.models import Event, EventImage, EventPlace
from first_one.first_app.permissions import EventImagePermission, EventPermission
from first_one.first_app.serializers import (
    EventImageSerializer,
    EventPlaceSerializer,
    EventSerializer,
)


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
        qs = EventImage.objects.select_related('event')
        if not self.request.user.is_superuser:  # type: ignore
            qs = qs.filter(
                event__status__in=[
                    Event.StatusChoices.PUBLISHED,
                    Event.StatusChoices.STARTED,
                ]
            )
        return qs
