from rest_framework.permissions import SAFE_METHODS, BasePermission

from first_one.first_app.models import Event


class EventPermission(BasePermission):
    def has_permission(self, request, view):  # type: ignore
        """
        Суперпользователь: польный доступ;
        Авторизованный пользователь: (GET).
        """
        if request.user.is_superuser:
            return True

        if request.user.is_authenticated:
            return request.method in SAFE_METHODS

        return False

    def has_object_permission(self, request, view, object):  # type: ignore
        """
        Суперпользователь: полный доступ к объектам;
        Авторизованный пользователь: доступ к иваентам с определенным статусом.
        """
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated and request.method in SAFE_METHODS:
            return object.status in (
                Event.StatusChoices.PUBLISHED,
                Event.StatusChoices.STARTED,
            )
        return False


class EventImagePermission(EventPermission):
    # Осталвяем все тоже самое,
    # только проверяем не Event.status, а EventImage.event.status
    def has_object_permission(self, request, view, object):
        return super().has_object_permission(request, view, object.event)

