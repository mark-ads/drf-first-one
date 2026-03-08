from django.urls import include, path
from rest_framework.routers import DefaultRouter

from first_one.first_app.views import (
    EventImageViewSet,
    EventNotificationViewSet,
    EventPlaceViewSet,
    EventViewSet,
    ImportEvent,
)

router = DefaultRouter()
router.register("places", EventPlaceViewSet)
router.register("events", EventViewSet)
router.register("images", EventImageViewSet)
router.register("notifications", EventNotificationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("events-import/", ImportEvent.as_view(), name="import_events"),
]
