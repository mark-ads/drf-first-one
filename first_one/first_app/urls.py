
from rest_framework.routers import DefaultRouter

from first_one.first_app.views import EventImageViewSet, EventNotificationViewSet, EventPlaceViewSet, EventViewSet

router = DefaultRouter()
router.register('places', EventPlaceViewSet)
router.register('events', EventViewSet)
router.register('images', EventImageViewSet)
router.register('notifications', EventNotificationViewSet)

urlpatterns = router.urls
