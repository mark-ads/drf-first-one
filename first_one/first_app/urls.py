
from rest_framework.routers import DefaultRouter

from first_one.first_app.views import EventImageViewSet, EventPlaceViewSet, EventViewSet

router = DefaultRouter()
router.register('places', EventPlaceViewSet)
router.register('events', EventViewSet)
router.register('images', EventImageViewSet)

urlpatterns = router.urls
